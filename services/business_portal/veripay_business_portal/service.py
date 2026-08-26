"""Business and merchant treasury read/action boundary. Expansion Dev 5, §2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field
from veripay_common.enums import (
    DecisionAction,
    DisputeReason,
    DisputeStatus,
    RiskBand,
    WebhookDecision,
)


class PortalAccessPolicy(BaseModel):
    portal: str
    required_roles: list[str]
    identity_provider: str = "external-auth-boundary"


class BusinessTransactionView(BaseModel):
    transaction_id: str
    merchant_id: str
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_band: RiskBand
    decision: DecisionAction
    status: str = Field(default="UNKNOWN", min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SpendSummary(BaseModel):
    merchant_id: str
    period: str = Field(min_length=1)
    spent_minor: int = Field(ge=0)
    limit_minor: int | None = Field(default=None, ge=0)
    remaining_minor: int | None = Field(default=None, ge=0)
    currency: str = Field(min_length=3, max_length=3)


class BusinessPolicyView(BaseModel):
    lock_id: str
    merchant_id: str
    allowed_mccs: str | None = None
    max_spend_per_txn_minor: int | None = Field(default=None, ge=0)
    daily_spend_limit_minor: int | None = Field(default=None, ge=0)
    enforce_merchant_lock: bool = True


class BusinessDisputeView(BaseModel):
    dispute_id: str
    transaction_id: str
    merchant_id: str | None = None
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    status: DisputeStatus
    reason: DisputeReason
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BusinessDisputeTransitionRequest(BaseModel):
    status: DisputeStatus
    actor: str = Field(min_length=1)


class WebhookStatusView(BaseModel):
    event_id: str
    merchant_id: str
    decision: WebhookDecision
    delivery_status: str = Field(min_length=1)
    attempts: int = Field(ge=0)
    last_error: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BusinessPortalRepository(Protocol):
    def list_transactions(
        self, merchant_id: str | None = None
    ) -> list[BusinessTransactionView]: ...

    def get_transaction(self, transaction_id: str) -> BusinessTransactionView | None: ...

    def get_spend_summary(self, merchant_id: str, period: str) -> SpendSummary | None: ...

    def list_policies(self, merchant_id: str | None = None) -> list[BusinessPolicyView]: ...

    def save_policy(self, policy: BusinessPolicyView) -> BusinessPolicyView: ...

    def get_policy(self, lock_id: str) -> BusinessPolicyView | None: ...

    def delete_policy(self, lock_id: str) -> bool: ...

    def list_disputes(self, merchant_id: str | None = None) -> list[BusinessDisputeView]: ...

    def get_dispute(self, dispute_id: str) -> BusinessDisputeView | None: ...

    def transition_dispute(
        self, dispute_id: str, request: BusinessDisputeTransitionRequest
    ) -> BusinessDisputeView: ...

    def list_webhooks(self, merchant_id: str | None = None) -> list[WebhookStatusView]: ...


@dataclass
class InMemoryBusinessPortalRepository:
    """Test adapter; production delegates policy/dispute actions to owned services."""

    transactions: dict[str, BusinessTransactionView] = field(default_factory=dict)
    spend_summaries: dict[tuple[str, str], SpendSummary] = field(default_factory=dict)
    policies: dict[str, BusinessPolicyView] = field(default_factory=dict)
    disputes: dict[str, BusinessDisputeView] = field(default_factory=dict)
    webhooks: dict[str, WebhookStatusView] = field(default_factory=dict)

    def save_transaction(self, view: BusinessTransactionView) -> BusinessTransactionView:
        self.transactions[view.transaction_id] = view
        return view

    def list_transactions(self, merchant_id: str | None = None) -> list[BusinessTransactionView]:
        values = list(self.transactions.values())
        if merchant_id is not None:
            values = [value for value in values if value.merchant_id == merchant_id]
        return values

    def get_transaction(self, transaction_id: str) -> BusinessTransactionView | None:
        return self.transactions.get(transaction_id)

    def save_spend_summary(self, summary: SpendSummary) -> SpendSummary:
        self.spend_summaries[(summary.merchant_id, summary.period)] = summary
        return summary

    def get_spend_summary(self, merchant_id: str, period: str) -> SpendSummary | None:
        return self.spend_summaries.get((merchant_id, period))

    def save_policy(self, policy: BusinessPolicyView) -> BusinessPolicyView:
        self.policies[policy.lock_id] = policy
        return policy

    def list_policies(self, merchant_id: str | None = None) -> list[BusinessPolicyView]:
        values = list(self.policies.values())
        if merchant_id is not None:
            values = [value for value in values if value.merchant_id == merchant_id]
        return values

    def get_policy(self, lock_id: str) -> BusinessPolicyView | None:
        return self.policies.get(lock_id)

    def delete_policy(self, lock_id: str) -> bool:
        return self.policies.pop(lock_id, None) is not None

    def save_dispute(self, dispute: BusinessDisputeView) -> BusinessDisputeView:
        self.disputes[dispute.dispute_id] = dispute
        return dispute

    def list_disputes(self, merchant_id: str | None = None) -> list[BusinessDisputeView]:
        values = list(self.disputes.values())
        if merchant_id is not None:
            values = [value for value in values if value.merchant_id == merchant_id]
        return values

    def get_dispute(self, dispute_id: str) -> BusinessDisputeView | None:
        return self.disputes.get(dispute_id)

    def transition_dispute(
        self, dispute_id: str, request: BusinessDisputeTransitionRequest
    ) -> BusinessDisputeView:
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

    def save_webhook(self, webhook: WebhookStatusView) -> WebhookStatusView:
        self.webhooks[webhook.event_id] = webhook
        return webhook

    def list_webhooks(self, merchant_id: str | None = None) -> list[WebhookStatusView]:
        values = list(self.webhooks.values())
        if merchant_id is not None:
            values = [value for value in values if value.merchant_id == merchant_id]
        return values
