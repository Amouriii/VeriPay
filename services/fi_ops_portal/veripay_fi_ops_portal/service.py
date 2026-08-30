"""Institutional fraud operations read and action boundary. Expansion Dev 5, §2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field
from veripay_common.enums import DecisionAction, DisputeReason, DisputeStatus, RiskBand


class PortalAccessPolicy(BaseModel):
    portal: str
    required_roles: list[str]
    identity_provider: str = "external-auth-boundary"


class OpsRiskComponent(BaseModel):
    component: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    reason_code: str | None = None


class OpsTransactionView(BaseModel):
    transaction_id: str
    user_id: str
    merchant_id: str | None = None
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_score: int = Field(ge=0, le=100)
    risk_band: RiskBand
    decision: DecisionAction
    reason_codes: list[str] = Field(default_factory=list)
    components: list[OpsRiskComponent] = Field(default_factory=list)
    audit_event_count: int = Field(default=0, ge=0)
    transaction_state: str = Field(default="UNKNOWN", min_length=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OpsAuditEventView(BaseModel):
    event_id: str
    transaction_id: str
    event_type: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    occurred_at: datetime
    payload: dict[str, str] = Field(default_factory=dict)


class OpsTransactionStateView(BaseModel):
    transaction_id: str
    state: str = Field(min_length=1)
    updated_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)


class OpsDisputeView(BaseModel):
    dispute_id: str
    transaction_id: str
    merchant_id: str | None = None
    amount_minor: int = Field(ge=0)
    currency: str
    status: DisputeStatus
    reason: DisputeReason
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OpsDisputeTransitionRequest(BaseModel):
    status: DisputeStatus
    actor: str = Field(min_length=1)


class RegulatoryReport(BaseModel):
    generated_at: datetime
    transaction_count: int = Field(ge=0)
    dispute_count: int = Field(ge=0)
    disputed_amount_minor: int = Field(ge=0)
    blocked_transaction_count: int = Field(ge=0)


class FiOpsRepository(Protocol):
    def list_transactions(self) -> list[OpsTransactionView]: ...

    def get_transaction(self, transaction_id: str) -> OpsTransactionView | None: ...

    def list_disputes(self) -> list[OpsDisputeView]: ...

    def get_dispute(self, dispute_id: str) -> OpsDisputeView | None: ...

    def transition_dispute(
        self, dispute_id: str, request: OpsDisputeTransitionRequest
    ) -> OpsDisputeView: ...

    def audit_events_for(self, transaction_id: str) -> list[OpsAuditEventView]: ...

    def get_transaction_state(self, transaction_id: str) -> OpsTransactionStateView | None: ...


@dataclass
class InMemoryFiOpsRepository:
    """Test adapter; production delegates actions to audit/dispute services."""

    transactions: dict[str, OpsTransactionView] = field(default_factory=dict)
    disputes: dict[str, OpsDisputeView] = field(default_factory=dict)
    audit_events: dict[str, list[OpsAuditEventView]] = field(default_factory=dict)
    transaction_states: dict[str, OpsTransactionStateView] = field(default_factory=dict)

    def save_transaction(self, view: OpsTransactionView) -> OpsTransactionView:
        self.transactions[view.transaction_id] = view
        return view

    def list_transactions(self) -> list[OpsTransactionView]:
        return list(self.transactions.values())

    def get_transaction(self, transaction_id: str) -> OpsTransactionView | None:
        return self.transactions.get(transaction_id)

    def save_dispute(self, view: OpsDisputeView) -> OpsDisputeView:
        self.disputes[view.dispute_id] = view
        return view

    def list_disputes(self) -> list[OpsDisputeView]:
        return list(self.disputes.values())

    def get_dispute(self, dispute_id: str) -> OpsDisputeView | None:
        return self.disputes.get(dispute_id)

    def transition_dispute(
        self, dispute_id: str, request: OpsDisputeTransitionRequest
    ) -> OpsDisputeView:
        dispute = self.disputes.get(dispute_id)
        if dispute is None:
            raise KeyError("Dispute not found")
        if request.status == dispute.status:
            return dispute
        allowed = {
            DisputeStatus.OPENED: {
                DisputeStatus.REPRESENTED,
                DisputeStatus.ACCEPTED,
                DisputeStatus.EXPIRED,
            },
            DisputeStatus.REPRESENTED: {
                DisputeStatus.ACCEPTED,
                DisputeStatus.REVERSED,
                DisputeStatus.EXPIRED,
            },
            DisputeStatus.ACCEPTED: {DisputeStatus.REVERSED, DisputeStatus.EXPIRED},
            DisputeStatus.REVERSED: set(),
            DisputeStatus.EXPIRED: set(),
        }
        if request.status not in allowed[dispute.status]:
            raise ValueError(f"Invalid transition from {dispute.status} to {request.status}")
        updated = dispute.model_copy(
            update={"status": request.status, "updated_at": datetime.now(UTC)}
        )
        self.disputes[dispute_id] = updated
        return updated

    def save_audit_event(self, event: OpsAuditEventView) -> OpsAuditEventView:
        self.audit_events.setdefault(event.transaction_id, []).append(event)
        return event

    def audit_events_for(self, transaction_id: str) -> list[OpsAuditEventView]:
        return list(self.audit_events.get(transaction_id, []))

    def save_transaction_state(self, state: OpsTransactionStateView) -> OpsTransactionStateView:
        self.transaction_states[state.transaction_id] = state
        return state

    def get_transaction_state(self, transaction_id: str) -> OpsTransactionStateView | None:
        return self.transaction_states.get(transaction_id)


def build_regulatory_report(repository: FiOpsRepository) -> RegulatoryReport:
    transactions = repository.list_transactions()
    disputes = repository.list_disputes()
    return RegulatoryReport(
        generated_at=datetime.now(UTC),
        transaction_count=len(transactions),
        dispute_count=len(disputes),
        disputed_amount_minor=sum(dispute.amount_minor for dispute in disputes),
        blocked_transaction_count=sum(
            transaction.risk_band == RiskBand.BLOCK for transaction in transactions
        ),
    )
