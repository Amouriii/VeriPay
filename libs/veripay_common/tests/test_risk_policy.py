"""Tests for veripay_common.risk_policy — tier boundaries and mappings."""

import pytest
from veripay_common.enums import DecisionAction, PaymentRail, ProcessingPath, RiskBand, RiskTier
from veripay_common.risk_policy import (
    TIER_POLICIES,
    TierPolicy,
    allowed_actions_for_tier,
    band_for_tier,
    policy_for_tier,
    processing_path_for_rail,
    tier_for_score,
    tier_from_band,
)

# --- tier_for_score: exact blueprint boundaries ----------------------------


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, RiskTier.NO_RISK),
        (5, RiskTier.NO_RISK),  # inclusive upper bound
        (5.01, RiskTier.LOW),
        (6, RiskTier.LOW),
        (25, RiskTier.LOW),
        (25.5, RiskTier.MODERATE),
        (26, RiskTier.MODERATE),
        (50, RiskTier.MODERATE),
        (50.5, RiskTier.HIGH),
        (51, RiskTier.HIGH),
        (100, RiskTier.HIGH),
    ],
)
def test_tier_for_score_boundaries(score, expected):
    assert tier_for_score(score) == expected


@pytest.mark.parametrize("score", [-1, -0.5, 101, 1000])
def test_tier_for_score_rejects_out_of_range(score):
    with pytest.raises(ValueError, match="0 and 100"):
        tier_for_score(score)


# --- policy_for_tier --------------------------------------------------------


def test_policy_for_tier_returns_matching_policy():
    for tier in RiskTier:
        policy = policy_for_tier(tier)
        assert isinstance(policy, TierPolicy)
        assert policy.tier == tier


def test_policies_cover_contiguous_score_ranges():
    """Tiers must tile 0-100 with no gaps or overlaps."""
    ordered = sorted(TIER_POLICIES, key=lambda p: p.minimum_score)
    assert ordered[0].minimum_score == 0
    assert ordered[-1].maximum_score == 100
    for prev, nxt in zip(ordered, ordered[1:], strict=False):
        assert nxt.minimum_score == prev.maximum_score + 1


def test_higher_tiers_mean_more_friction():
    """Friction ranks: NONE(0) < PUSH(1) < BIOMETRIC(2) < MULTI_FACTOR(3)."""
    rank = {"NONE": 0, "PUSH": 1, "BIOMETRIC": 2, "MULTI_FACTOR": 3}
    no_risk = policy_for_tier(RiskTier.NO_RISK)
    high = policy_for_tier(RiskTier.HIGH)
    assert rank[no_risk.friction.value] < rank[high.friction.value]


# --- band <-> tier projections ----------------------------------------------


@pytest.mark.parametrize(
    ("band", "tier"),
    [
        (RiskBand.APPROVE, RiskTier.LOW),
        (RiskBand.VERIFY, RiskTier.MODERATE),
        (RiskBand.BLOCK, RiskTier.HIGH),
    ],
)
def test_tier_from_band(band, tier):
    assert tier_from_band(band) == tier


@pytest.mark.parametrize(
    ("tier", "band"),
    [
        (RiskTier.NO_RISK, RiskBand.APPROVE),
        (RiskTier.LOW, RiskBand.APPROVE),
        (RiskTier.MODERATE, RiskBand.VERIFY),
        (RiskTier.HIGH, RiskBand.BLOCK),
    ],
)
def test_band_for_tier(tier, band):
    assert band_for_tier(tier) == band


def test_band_tier_roundtrip_is_stable():
    for band in RiskBand:
        assert band_for_tier(tier_from_band(band)) == band


# --- processing paths --------------------------------------------------------


@pytest.mark.parametrize(
    ("rail", "path"),
    [
        (PaymentRail.CARD, ProcessingPath.FAST),
        (PaymentRail.ISO_8583, ProcessingPath.FAST),
        (PaymentRail.FEDNOW, ProcessingPath.SECONDARY),
        (PaymentRail.RTP, ProcessingPath.SECONDARY),
        (PaymentRail.ACH, ProcessingPath.SECONDARY),
        (PaymentRail.SWIFT, ProcessingPath.SECONDARY),
        (PaymentRail.ISO_20022, ProcessingPath.SECONDARY),
        (PaymentRail.DOMESTIC_INSTANT, ProcessingPath.SECONDARY),
    ],
)
def test_processing_path_for_rail(rail, path):
    assert processing_path_for_rail(rail) == path


# --- allowed actions per tier ------------------------------------------------


def test_allowed_actions_are_never_empty():
    for tier in RiskTier:
        actions = allowed_actions_for_tier(tier)
        assert len(actions) > 0


def test_higher_tiers_allow_stricter_controls():
    low = set(allowed_actions_for_tier(RiskTier.LOW))
    high = set(allowed_actions_for_tier(RiskTier.HIGH))
    assert DecisionAction.REVERSE in high
    assert DecisionAction.REVERSE not in low


def test_no_risk_tier_cannot_decline():
    actions = allowed_actions_for_tier(RiskTier.NO_RISK)
    assert DecisionAction.DECLINE not in actions
