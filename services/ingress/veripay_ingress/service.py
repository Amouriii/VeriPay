"""Transaction ingress domain logic.

The repository protocol deliberately keeps persistence out of the HTTP layer so
this service can run against the seeded database once its adapter is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from veripay_common.enums import Channel, DecisionAction, Mti, RiskBand


class Transaction(BaseModel):
    """Canonical transaction payload accepted by the ingress API."""

    model_config = ConfigDict(use_enum_values=True)

    transaction_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant_id: str | None = None
    mti: Mti = Mti.AUTHORIZATION_REQUEST
    channel: Channel = Channel.CARD_NOT_PRESENT


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
    components: list[ComponentScore] = Field(default_factory=list)


class AuthorizationResponse(BaseModel):
    transaction_id: str
    decision: DecisionAction
    risk_score: int = Field(ge=0, le=100)
    reason_code: str
    challenge_id: str | None = None


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
    """Return a deterministic baseline score pending ML/rule-engine integration."""
    score = 0
    reason: str | None = None
    if transaction.amount_minor >= 100_000:
        score += 35
        reason = "HIGH_VALUE"
    if transaction.channel == Channel.CARD_NOT_PRESENT:
        score += 10
        reason = reason or "CARD_NOT_PRESENT"
    score = min(score, 100)
    band = RiskBand.APPROVE if score < 40 else RiskBand.VERIFY if score < 70 else RiskBand.BLOCK
    component = ComponentScore(
        component="ingress_baseline",
        score=score,
        weight=1.0,
        reason_code=reason,
    )
    return RiskScore(
        transaction_id=transaction.transaction_id,
        unified_score=score,
        band=band,
        components=[component],
    )


def authorize(transaction: Transaction) -> AuthorizationResponse:
    """Map the baseline risk band to the frozen authorization response."""
    risk = calculate_risk(transaction)
    if risk.band == RiskBand.BLOCK:
        return AuthorizationResponse(
            transaction_id=transaction.transaction_id,
            decision=DecisionAction.DECLINE,
            risk_score=risk.unified_score,
            reason_code="RISK_THRESHOLD",
        )
    if risk.band == RiskBand.VERIFY:
        return AuthorizationResponse(
            transaction_id=transaction.transaction_id,
            decision=DecisionAction.CHALLENGE,
            risk_score=risk.unified_score,
            reason_code="RISK_THRESHOLD",
            challenge_id=f"challenge_{uuid4().hex}",
        )
    return AuthorizationResponse(
        transaction_id=transaction.transaction_id,
        decision=DecisionAction.ALLOW,
        risk_score=risk.unified_score,
        reason_code="BASELINE_APPROVED",
    )
