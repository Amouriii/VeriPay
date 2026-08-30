"""Tests for veripay_common.constants — canonical thresholds invariants."""

from veripay_common import constants as c


def test_tier_boundaries_are_ordered_and_contiguous():
    assert 0 <= c.RISK_TIER_NO_RISK_MAX < c.RISK_TIER_LOW_MAX
    assert c.RISK_TIER_LOW_MAX < c.RISK_TIER_MODERATE_MAX < c.RISK_TIER_HIGH_MAX
    assert c.RISK_TIER_HIGH_MAX == 100


def test_legacy_band_projection_matches_tiers():
    assert c.RISK_SCORE_APPROVE_MAX == c.RISK_TIER_LOW_MAX
    assert c.RISK_SCORE_VERIFY_MAX == c.RISK_TIER_MODERATE_MAX
    assert c.RISK_SCORE_BLOCK_MAX == c.RISK_TIER_HIGH_MAX


def test_latency_budgets():
    # Fast path must be far tighter than secondary path
    assert c.FAST_PATH_DEADLINE_MS < c.SECONDARY_PATH_DEADLINE_MS
    # ML budget is a slice of the fast path
    assert 0 < c.FAST_PATH_ML_BUDGET_MS < c.FAST_PATH_DEADLINE_MS


def test_verification_token_ttl_window():
    assert 0 < c.VERIFICATION_TOKEN_MIN_TTL_SEC < c.VERIFICATION_TOKEN_MAX_TTL_SEC
    assert c.VERIFICATION_TOKEN_MIN_TTL_SEC == 10
    assert c.VERIFICATION_TOKEN_MAX_TTL_SEC == 30
    # Default must lie inside the window
    assert (
        c.VERIFICATION_TOKEN_MIN_TTL_SEC
        <= c.DEFAULT_VERIFICATION_TOKEN_TTL_SEC
        <= c.VERIFICATION_TOKEN_MAX_TTL_SEC
    )


def test_gpv_thresholds_ordered():
    assert 0 < c.GPV_MATCH_MAX_M < c.GPV_LIKELY_MATCH_MAX_M


def test_h3_resolutions_ordered():
    # Higher resolution = finer grid; store level finer than shopping area
    assert c.H3_RES_SHOPPING_AREA < c.H3_RES_STORE_LEVEL


def test_challenge_nonce_strength():
    assert c.CHALLENGE_NONCE_BITS >= 128
    assert c.CHALLENGE_NONCE_TTL_SEC > 0


def test_fusion_weights_sum_to_one():
    total = sum(c.DEFAULT_FUSION_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9
    assert all(w > 0 for w in c.DEFAULT_FUSION_WEIGHTS.values())


def test_streaming_windows_well_formed():
    assert c.WINDOWS, "window set must not be empty"
    for name, window in c.WINDOWS.items():
        assert window["type"] == "tumbling", name
        assert window["size"].endswith(("min", "h")), name


def test_reason_codes_are_unique_strings():
    codes = [
        c.REASON_DCVV_MISMATCH,
        c.REASON_MERCHANT_LOCK_VIOLATION,
        c.REASON_BURNER_VELOCITY,
        c.REASON_IMPOSSIBLE_TRAVEL,
        c.REASON_SIGNAL_CONTRADICTION,
        c.REASON_NEW_DEVICE,
    ]
    assert len(codes) == len(set(codes))
    assert all(isinstance(code, str) and code for code in codes)
