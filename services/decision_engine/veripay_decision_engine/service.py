"""Cost-aware authorization routing constrained by the blueprint tier matrix."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from veripay_common.enums import (
    DecisionAction,
    ExplanationMode,
    PaymentRail,
    ProcessingPath,
    RiskBand,
    RiskTier,
    VerificationOutcome,
)
from veripay_common.risk_policy import (
    allowed_actions_for_tier,
    band_for_tier,
    policy_for_tier,
    processing_path_for_rail,
    tier_for_score,
    tier_from_band,
)


class DecisionReason(StrEnum):
    REVERSAL_REQUEST = "REVERSAL_REQUEST"
    COMPLIANCE_BLOCK = "COMPLIANCE_BLOCK"
    MANDATORY_CHALLENGE = "MANDATORY_CHALLENGE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    VERIFICATION_APPROVED = "VERIFICATION_APPROVED"
    VERIFICATION_DENIED = "VERIFICATION_DENIED"
    VERIFICATION_TIMEOUT = "VERIFICATION_TIMEOUT"
    VERIFICATION_ESCALATED = "VERIFICATION_ESCALATED"
    FAST_PATH_ASYNC_EXPLANATION = "FAST_PATH_ASYNC_EXPLANATION"
    SECONDARY_PATH_IN_BAND_EXPLANATION = "SECONDARY_PATH_IN_BAND_EXPLANATION"
    COST_MINIMIZED = "COST_MINIMIZED"


class CostModel(BaseModel):
    """Expected-loss inputs; values are minor currency units."""

    fraud_loss_minor: float = Field(default=10_000, ge=0)
    false_decline_loss_minor: float = Field(default=2_500, ge=0)
    monitor_cost_minor: float = Field(default=400, ge=0)
    challenge_cost_minor: float = Field(default=60, ge=0)
    review_cost_minor: float = Field(default=150, ge=0)
    reversal_cost_minor: float = Field(default=100, ge=0)
    monitor_residual_fraud_rate: float = Field(default=0.85, ge=0, le=1)
    challenge_residual_fraud_rate: float = Field(default=0.20, ge=0, le=1)
    review_residual_fraud_rate: float = Field(default=0.35, ge=0, le=1)
    reversal_residual_fraud_rate: float = Field(default=0.05, ge=0, le=1)


class DecisionRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    risk_score: int = Field(ge=0, le=100)
    risk_band: RiskBand | None = None
    risk_tier: RiskTier | None = None
    payment_rail: PaymentRail | None = None
    processing_path: ProcessingPath | None = None
    verification_outcome: VerificationOutcome = VerificationOutcome.PENDING
    is_reversal: bool = False
    compliance_blocked: bool = False
    mandatory_challenge: bool = False
    evidence_available: bool = True
    explanation_available: bool = True
    cost_model: CostModel = Field(default_factory=CostModel)

    @model_validator(mode="after")
    def derive_operational_fields(self) -> DecisionRequest:
        if self.risk_tier is None and self.risk_band is not None:
            self.risk_tier = tier_from_band(self.risk_band)
        elif self.risk_tier is None:
            self.risk_tier = tier_for_score(self.risk_score)
        if self.processing_path is None and self.payment_rail is not None:
            self.processing_path = processing_path_for_rail(self.payment_rail)
        return self


class DecisionCandidate(BaseModel):
    action: DecisionAction
    expected_cost_minor: float = Field(ge=0)


class DecisionResponse(BaseModel):
    transaction_id: str
    action: DecisionAction
    risk_score: int = Field(ge=0, le=100)
    risk_band: RiskBand
    risk_tier: RiskTier
    reason_code: DecisionReason
    expected_cost_minor: float = Field(ge=0)
    candidates: list[DecisionCandidate] = Field(default_factory=list)
    friction: str
    workflow: str
    timeout_seconds: int = Field(ge=0)
    timeout_fallback: str
    processing_path: ProcessingPath
    explanation_mode: ExplanationMode
    explanation_job_id: str | None = None
    escalation_required: bool = False
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def _expected_cost(action: DecisionAction, probability: float, model: CostModel) -> float:
    fraud_loss = probability * model.fraud_loss_minor
    if action == DecisionAction.ALLOW:
        return fraud_loss
    if action == DecisionAction.MONITOR:
        return model.monitor_cost_minor + fraud_loss * model.monitor_residual_fraud_rate
    if action == DecisionAction.CHALLENGE:
        return model.challenge_cost_minor + fraud_loss * model.challenge_residual_fraud_rate
    if action == DecisionAction.REVIEW:
        return model.review_cost_minor + fraud_loss * model.review_residual_fraud_rate
    if action == DecisionAction.DECLINE:
        return (1 - probability) * model.false_decline_loss_minor
    return model.reversal_cost_minor + fraud_loss * model.reversal_residual_fraud_rate


def _candidate_actions(band: RiskBand) -> list[DecisionAction]:
    """Legacy candidate set retained for clients that submit RiskBand only."""
    if band == RiskBand.APPROVE:
        return [DecisionAction.ALLOW, DecisionAction.MONITOR]
    if band == RiskBand.VERIFY:
        return [DecisionAction.MONITOR, DecisionAction.CHALLENGE, DecisionAction.REVIEW]
    return [DecisionAction.REVIEW, DecisionAction.DECLINE]


def _candidate_actions_for_tier(tier: RiskTier) -> list[DecisionAction]:
    return list(allowed_actions_for_tier(tier))


def _forced_response(
    request: DecisionRequest,
    action: DecisionAction,
    reason: DecisionReason,
    *,
    explanation_mode: ExplanationMode,
    explanation_job_id: str | None = None,
    escalation_required: bool = False,
) -> DecisionResponse:
    assert request.risk_tier is not None
    assert request.processing_path is not None
    policy = policy_for_tier(request.risk_tier)
    cost = _expected_cost(action, request.risk_score / 100, request.cost_model)
    return DecisionResponse(
        transaction_id=request.transaction_id,
        action=action,
        risk_score=request.risk_score,
        risk_band=request.risk_band or band_for_tier(request.risk_tier),
        risk_tier=request.risk_tier,
        reason_code=reason,
        expected_cost_minor=cost,
        candidates=[DecisionCandidate(action=action, expected_cost_minor=cost)],
        friction=policy.friction,
        workflow=policy.workflow,
        timeout_seconds=policy.timeout_seconds,
        timeout_fallback=policy.timeout_fallback,
        processing_path=request.processing_path,
        explanation_mode=explanation_mode,
        explanation_job_id=explanation_job_id,
        escalation_required=escalation_required,
    )


def _derived_path(request: DecisionRequest) -> ProcessingPath:
    return request.processing_path or ProcessingPath.FAST


def decide(request: DecisionRequest) -> DecisionResponse:
    """Select an action while honoring hard controls and tier-required friction."""
    assert request.risk_tier is not None
    path = _derived_path(request)
    request.processing_path = path
    matrix_mode = (
        request.risk_band is None
        or request.risk_tier != tier_from_band(request.risk_band)
    )
    explanation_mode = (
        ExplanationMode.ASYNC if path == ProcessingPath.FAST else ExplanationMode.IN_BAND
    )
    explanation_job_id = (
        f"explain_{uuid4().hex}"
        if path == ProcessingPath.FAST and not request.explanation_available
        else None
    )

    if request.is_reversal:
        return _forced_response(
            request,
            DecisionAction.REVERSE,
            DecisionReason.REVERSAL_REQUEST,
            explanation_mode=explanation_mode,
            explanation_job_id=explanation_job_id,
        )
    if request.compliance_blocked:
        return _forced_response(
            request,
            DecisionAction.DECLINE,
            DecisionReason.COMPLIANCE_BLOCK,
            explanation_mode=explanation_mode,
            explanation_job_id=explanation_job_id,
        )
    if not request.evidence_available:
        return _forced_response(
            request,
            DecisionAction.REVIEW,
            DecisionReason.EVIDENCE_UNAVAILABLE,
            explanation_mode=explanation_mode,
            explanation_job_id=explanation_job_id,
            escalation_required=request.risk_tier == RiskTier.HIGH,
        )
    if path == ProcessingPath.SECONDARY and not request.explanation_available:
        return _forced_response(
            request,
            DecisionAction.REVIEW,
            DecisionReason.EVIDENCE_UNAVAILABLE,
            explanation_mode=explanation_mode,
            escalation_required=True,
        )
    if request.verification_outcome in (
        VerificationOutcome.DENIED,
        VerificationOutcome.TIMED_OUT,
        VerificationOutcome.EXPIRED,
        VerificationOutcome.LOCKED,
    ):
        reason = (
            DecisionReason.VERIFICATION_TIMEOUT
            if request.verification_outcome
            in (VerificationOutcome.TIMED_OUT, VerificationOutcome.EXPIRED)
            else DecisionReason.VERIFICATION_DENIED
        )
        return _forced_response(
            request,
            DecisionAction.REVIEW if request.risk_tier == RiskTier.HIGH else DecisionAction.DECLINE,
            reason,
            explanation_mode=explanation_mode,
            escalation_required=(request.risk_tier == RiskTier.HIGH),
        )
    if request.verification_outcome == VerificationOutcome.ESCALATED:
        return _forced_response(
            request,
            DecisionAction.REVIEW,
            DecisionReason.VERIFICATION_ESCALATED,
            explanation_mode=explanation_mode,
            escalation_required=True,
        )
    if request.verification_outcome == VerificationOutcome.APPROVED:
        return _forced_response(
            request,
            DecisionAction.ALLOW,
            DecisionReason.VERIFICATION_APPROVED,
            explanation_mode=explanation_mode,
            explanation_job_id=explanation_job_id,
        )

    if matrix_mode:
        actions = _candidate_actions_for_tier(request.risk_tier)
    else:
        actions = _candidate_actions(request.risk_band or RiskBand.APPROVE)
    probability = request.risk_score / 100
    candidates = [
        DecisionCandidate(
            action=action,
            expected_cost_minor=_expected_cost(action, probability, request.cost_model),
        )
        for action in actions
    ]
    selected = min(candidates, key=lambda candidate: candidate.expected_cost_minor)
    policy = policy_for_tier(request.risk_tier)
    if (
        matrix_mode
        and request.risk_tier != RiskTier.NO_RISK
        and selected.action == DecisionAction.ALLOW
    ):
        challenge = next(
            (candidate for candidate in candidates if candidate.action == DecisionAction.CHALLENGE),
            None,
        )
        if challenge is not None:
            selected = challenge
    if not matrix_mode:
        reason = DecisionReason.COST_MINIMIZED
    elif path == ProcessingPath.SECONDARY:
        reason = DecisionReason.SECONDARY_PATH_IN_BAND_EXPLANATION
    elif request.risk_tier != RiskTier.NO_RISK:
        reason = DecisionReason.FAST_PATH_ASYNC_EXPLANATION
    else:
        reason = DecisionReason.COST_MINIMIZED
    return DecisionResponse(
        transaction_id=request.transaction_id,
        action=selected.action,
        risk_score=request.risk_score,
        risk_band=request.risk_band or band_for_tier(request.risk_tier),
        risk_tier=request.risk_tier,
        reason_code=reason,
        expected_cost_minor=selected.expected_cost_minor,
        candidates=candidates,
        friction=policy.friction,
        workflow=policy.workflow,
        timeout_seconds=policy.timeout_seconds,
        timeout_fallback=policy.timeout_fallback,
        processing_path=path,
        explanation_mode=explanation_mode,
        explanation_job_id=explanation_job_id,
        escalation_required=policy.analyst_escalation and selected.action == DecisionAction.REVIEW,
    )
