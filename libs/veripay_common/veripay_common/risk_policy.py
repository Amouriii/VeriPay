"""Deterministic operational policy for blueprint risk gating.

The fused model remains a 0-100 percentage score. This module converts that
continuous score into the customer-facing tier and the verification policy
that must be applied by downstream services.
"""

from __future__ import annotations

from dataclasses import dataclass

from veripay_common.enums import (
    DecisionAction,
    FrictionType,
    PaymentRail,
    ProcessingPath,
    RiskBand,
    RiskTier,
    TimeoutFallback,
    VerificationWorkflow,
)


@dataclass(frozen=True)
class TierPolicy:
    """Immutable customer-friction and fallback policy for one risk tier."""

    tier: RiskTier
    minimum_score: int
    maximum_score: int
    friction: FrictionType
    workflow: VerificationWorkflow
    timeout_seconds: int
    timeout_fallback: TimeoutFallback
    fallback_action: DecisionAction
    temporary_lock: bool = False
    analyst_escalation: bool = False


TIER_POLICIES: tuple[TierPolicy, ...] = (
    TierPolicy(
        tier=RiskTier.NO_RISK,
        minimum_score=0,
        maximum_score=5,
        friction=FrictionType.NONE,
        workflow=VerificationWorkflow.SILENT_PASS,
        timeout_seconds=0,
        timeout_fallback=TimeoutFallback.STANDARD_AUDIT,
        fallback_action=DecisionAction.ALLOW,
    ),
    TierPolicy(
        tier=RiskTier.LOW,
        minimum_score=6,
        maximum_score=25,
        friction=FrictionType.PUSH,
        workflow=VerificationWorkflow.PUSH_APPROVE_DENY,
        timeout_seconds=30,
        timeout_fallback=TimeoutFallback.AUTO_DECLINE,
        fallback_action=DecisionAction.DECLINE,
    ),
    TierPolicy(
        tier=RiskTier.MODERATE,
        minimum_score=26,
        maximum_score=50,
        friction=FrictionType.BIOMETRIC,
        workflow=VerificationWorkflow.PUSH_BIOMETRIC,
        timeout_seconds=30,
        timeout_fallback=TimeoutFallback.AUTO_DECLINE_AND_LOCK,
        fallback_action=DecisionAction.DECLINE,
        temporary_lock=True,
    ),
    TierPolicy(
        tier=RiskTier.HIGH,
        minimum_score=51,
        maximum_score=100,
        friction=FrictionType.MULTI_FACTOR,
        workflow=VerificationWorkflow.EXACT_AMOUNT_BIOMETRIC_SWIPE,
        timeout_seconds=30,
        timeout_fallback=TimeoutFallback.LIVE_ANALYST_ESCALATION,
        fallback_action=DecisionAction.REVIEW,
        analyst_escalation=True,
    ),
)


def tier_for_score(score: int | float) -> RiskTier:
    """Classify a bounded percentage score using exact blueprint boundaries."""
    if not 0 <= score <= 100:
        raise ValueError("Risk score must be between 0 and 100")
    if score <= 5:
        return RiskTier.NO_RISK
    if score <= 25:
        return RiskTier.LOW
    if score <= 50:
        return RiskTier.MODERATE
    return RiskTier.HIGH


def policy_for_tier(tier: RiskTier) -> TierPolicy:
    """Return the immutable policy for ``tier``."""
    return next(policy for policy in TIER_POLICIES if policy.tier == tier)


def tier_from_band(band: RiskBand) -> RiskTier:
    """Project the legacy three-band contract onto the four-tier model."""
    if band == RiskBand.APPROVE:
        return RiskTier.LOW
    if band == RiskBand.VERIFY:
        return RiskTier.MODERATE
    return RiskTier.HIGH


def band_for_tier(tier: RiskTier) -> RiskBand:
    """Project a blueprint tier to the legacy three-band contract."""
    if tier in (RiskTier.NO_RISK, RiskTier.LOW):
        return RiskBand.APPROVE
    if tier == RiskTier.MODERATE:
        return RiskBand.VERIFY
    return RiskBand.BLOCK


def processing_path_for_rail(rail: PaymentRail) -> ProcessingPath:
    """Map supported payment rails to the blueprint latency path."""
    if rail in (PaymentRail.CARD, PaymentRail.ISO_8583):
        return ProcessingPath.FAST
    return ProcessingPath.SECONDARY


def allowed_actions_for_tier(tier: RiskTier) -> tuple[DecisionAction, ...]:
    """Return actions permitted after applying the tier's friction policy."""
    if tier == RiskTier.NO_RISK:
        return (DecisionAction.ALLOW, DecisionAction.MONITOR)
    if tier == RiskTier.LOW:
        return (DecisionAction.ALLOW, DecisionAction.CHALLENGE, DecisionAction.DECLINE)
    if tier == RiskTier.MODERATE:
        return (DecisionAction.CHALLENGE, DecisionAction.REVIEW, DecisionAction.DECLINE)
    return (DecisionAction.REVIEW, DecisionAction.DECLINE, DecisionAction.REVERSE)


__all__ = [
    "TIER_POLICIES",
    "TierPolicy",
    "allowed_actions_for_tier",
    "band_for_tier",
    "policy_for_tier",
    "processing_path_for_rail",
    "tier_for_score",
    "tier_from_band",
]
