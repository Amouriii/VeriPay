"""Cost-aware authorization decision routing. PLAN §19."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field
from veripay_common.enums import DecisionAction, RiskBand


class DecisionReason(StrEnum):
    REVERSAL_REQUEST = "REVERSAL_REQUEST"
    COMPLIANCE_BLOCK = "COMPLIANCE_BLOCK"
    MANDATORY_CHALLENGE = "MANDATORY_CHALLENGE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
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
    risk_band: RiskBand
    is_reversal: bool = False
    compliance_blocked: bool = False
    mandatory_challenge: bool = False
    evidence_available: bool = True
    cost_model: CostModel = Field(default_factory=CostModel)


class DecisionCandidate(BaseModel):
    action: DecisionAction
    expected_cost_minor: float = Field(ge=0)


class DecisionResponse(BaseModel):
    transaction_id: str
    action: DecisionAction
    risk_score: int = Field(ge=0, le=100)
    risk_band: RiskBand
    reason_code: DecisionReason
    expected_cost_minor: float = Field(ge=0)
    candidates: list[DecisionCandidate] = Field(default_factory=list)


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
    if band == RiskBand.APPROVE:
        return [DecisionAction.ALLOW, DecisionAction.MONITOR]
    if band == RiskBand.VERIFY:
        return [DecisionAction.MONITOR, DecisionAction.CHALLENGE, DecisionAction.REVIEW]
    return [DecisionAction.REVIEW, DecisionAction.DECLINE]


def _forced_response(
    request: DecisionRequest,
    action: DecisionAction,
    reason: DecisionReason,
) -> DecisionResponse:
    cost = _expected_cost(action, request.risk_score / 100, request.cost_model)
    return DecisionResponse(
        transaction_id=request.transaction_id,
        action=action,
        risk_score=request.risk_score,
        risk_band=request.risk_band,
        reason_code=reason,
        expected_cost_minor=cost,
        candidates=[DecisionCandidate(action=action, expected_cost_minor=cost)],
    )


def decide(request: DecisionRequest) -> DecisionResponse:
    """Select an action while honoring hard security and lifecycle controls."""
    if request.is_reversal:
        return _forced_response(request, DecisionAction.REVERSE, DecisionReason.REVERSAL_REQUEST)
    if request.compliance_blocked:
        return _forced_response(request, DecisionAction.DECLINE, DecisionReason.COMPLIANCE_BLOCK)
    if request.mandatory_challenge:
        return _forced_response(
            request, DecisionAction.CHALLENGE, DecisionReason.MANDATORY_CHALLENGE
        )
    if not request.evidence_available:
        return _forced_response(request, DecisionAction.REVIEW, DecisionReason.EVIDENCE_UNAVAILABLE)

    probability = request.risk_score / 100
    candidates = [
        DecisionCandidate(
            action=action,
            expected_cost_minor=_expected_cost(action, probability, request.cost_model),
        )
        for action in _candidate_actions(request.risk_band)
    ]
    selected = min(candidates, key=lambda candidate: candidate.expected_cost_minor)
    return DecisionResponse(
        transaction_id=request.transaction_id,
        action=selected.action,
        risk_score=request.risk_score,
        risk_band=request.risk_band,
        reason_code=DecisionReason.COST_MINIMIZED,
        expected_cost_minor=selected.expected_cost_minor,
        candidates=candidates,
    )
