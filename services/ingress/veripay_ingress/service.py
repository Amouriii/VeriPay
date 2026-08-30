"""Transaction ingress domain logic with blueprint rail-aware authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from veripay_common.enums import (
    Channel,
    DecisionAction,
    ExplanationMode,
    Mti,
    PaymentRail,
    ProcessingPath,
    RiskBand,
    RiskTier,
)
from veripay_common.risk_policy import (
    band_for_tier,
    policy_for_tier,
    processing_path_for_rail,
    tier_for_score,
)


class Transaction(BaseModel):
    """Canonical transaction payload accepted by the ingress API.

    The rail fields are optional for compatibility with clients using the
    original contract. New adapters should always send ``payment_rail``.
    """

    model_config = ConfigDict(use_enum_values=True)

    transaction_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant_id: str | None = None
    mti: Mti = Mti.AUTHORIZATION_REQUEST
    channel: Channel = Channel.CARD_NOT_PRESENT
    payment_rail: PaymentRail | None = None
    processing_path: ProcessingPath | None = None


class ComponentScore(BaseModel):
    component: str
    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    available: bool = True
    reason_code: str | None = None


class RiskScore(BaseModel):
    transaction_id: str
    unified_score: int = Field(ge=0, le=100)
    band: RiskBand
    tier: RiskTier
    components: list[ComponentScore] = Field(default_factory=list)


class AuthorizationResponse(BaseModel):
    transaction_id: str
    decision: DecisionAction
    risk_score: int = Field(ge=0, le=100)
    reason_code: str
    challenge_id: str | None = None
    risk_tier: RiskTier | None = None
    friction: str | None = None
    workflow: str | None = None
    verification_timeout_seconds: int = Field(default=0, ge=0)
    processing_path: ProcessingPath | None = None
    explanation_mode: ExplanationMode | None = None
    explanation_job_id: str | None = None
    escalation_required: bool = False


class TransactionRepository(Protocol):
    def save(self, transaction: Transaction) -> Transaction: ...

    def list(self) -> list[Transaction]: ...

    def get(self, transaction_id: str) -> Transaction | None: ...


@dataclass
class InMemoryTransactionRepository:
    """Temporary adapter used until the populated database adapter is wired."""

    transactions: dict[str, Transaction] = field(default_factory=dict)

    def save(self, transaction: Transaction) -> Transaction:
        self.transactions[transaction.transaction_id] = transaction
        return transaction

    def list(self) -> list[Transaction]:
        return list(self.transactions.values())

    def get(self, transaction_id: str) -> Transaction | None:
        return self.transactions.get(transaction_id)


def calculate_risk(transaction: Transaction) -> RiskScore:
    """Return a deterministic baseline score pending full ML provider wiring."""
    score = 0
    reason: str | None = None
    if transaction.amount_minor >= 100_000:
        score += 35
        reason = "HIGH_VALUE"
    if transaction.channel == Channel.CARD_NOT_PRESENT:
        score += 10
        reason = reason or "CARD_NOT_PRESENT"
    score = min(score, 100)
    tier = tier_for_score(score)
    component = ComponentScore(
        component="ingress_baseline",
        score=score,
        weight=1.0,
        reason_code=reason,
    )
    return RiskScore(
        transaction_id=transaction.transaction_id,
        unified_score=score,
        band=band_for_tier(tier),
        tier=tier,
        components=[component],
    )


def _legacy_authorize(transaction: Transaction, risk: RiskScore) -> AuthorizationResponse:
    """Keep the original response semantics for pre-rail clients."""
    if risk.band == RiskBand.BLOCK:
        decision = DecisionAction.DECLINE
        challenge_id = None
        reason_code = "RISK_THRESHOLD"
    elif risk.band == RiskBand.VERIFY:
        decision = DecisionAction.CHALLENGE
        challenge_id = f"challenge_{uuid4().hex}"
        reason_code = "RISK_THRESHOLD"
    else:
        decision = DecisionAction.ALLOW
        challenge_id = None
        reason_code = "BASELINE_APPROVED"
    policy = policy_for_tier(risk.tier)
    return AuthorizationResponse(
        transaction_id=transaction.transaction_id,
        decision=decision,
        risk_score=risk.unified_score,
        reason_code=reason_code,
        challenge_id=challenge_id,
        risk_tier=risk.tier,
        friction=policy.friction,
        workflow=policy.workflow,
        verification_timeout_seconds=policy.timeout_seconds,
        processing_path=ProcessingPath.FAST,
        explanation_mode=ExplanationMode.ASYNC,
    )


def authorize(transaction: Transaction) -> AuthorizationResponse:
    """Authorize with the blueprint matrix for explicit rail-aware requests."""
    risk = calculate_risk(transaction)
    if transaction.payment_rail is None:
        return _legacy_authorize(transaction, risk)
    path = transaction.processing_path or processing_path_for_rail(transaction.payment_rail)
    policy = policy_for_tier(risk.tier)
    if risk.tier == RiskTier.NO_RISK:
        decision = DecisionAction.ALLOW
        reason_code = "BASELINE_APPROVED"
        challenge_id = None
    elif risk.tier in (RiskTier.LOW, RiskTier.MODERATE):
        decision = DecisionAction.CHALLENGE
        reason_code = "RISK_TIER_VERIFICATION_REQUIRED"
        challenge_id = f"challenge_{uuid4().hex}"
    else:
        decision = DecisionAction.REVIEW
        reason_code = "HIGH_RISK_ANALYST_REVIEW_REQUIRED"
        challenge_id = f"challenge_{uuid4().hex}"
    explanation_job_id = f"explain_{uuid4().hex}" if path == ProcessingPath.FAST else None
    return AuthorizationResponse(
        transaction_id=transaction.transaction_id,
        decision=decision,
        risk_score=risk.unified_score,
        reason_code=reason_code,
        challenge_id=challenge_id,
        risk_tier=risk.tier,
        friction=policy.friction,
        workflow=policy.workflow,
        verification_timeout_seconds=policy.timeout_seconds,
        processing_path=path,
        explanation_mode=(
            ExplanationMode.ASYNC if path == ProcessingPath.FAST else ExplanationMode.IN_BAND
        ),
        explanation_job_id=explanation_job_id,
        escalation_required=risk.tier == RiskTier.HIGH,
    )
