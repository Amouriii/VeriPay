"""Dispute and chargeback lifecycle boundaries. Expansion Dev 5, §3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator
from veripay_common.enums import DisputeReason, DisputeStatus


class DisputeSyncStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


class DisputeCase(BaseModel):
    dispute_id: str = Field(default_factory=lambda: f"dispute_{uuid4().hex}", min_length=1)
    transaction_id: str = Field(min_length=1)
    merchant_id: str | None = None
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    status: DisputeStatus
    reason: DisputeReason
    idempotency_key: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class DisputeTransitionRequest(BaseModel):
    status: DisputeStatus
    actor: str = Field(min_length=1)


class EvidenceSubmission(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"evidence_{uuid4().hex}", min_length=1)
    dispute_id: str = Field(min_length=1)
    evidence_type: str = Field(min_length=1)
    provider_reference: str = Field(min_length=1)
    submitted_by: str = Field(min_length=1)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DisputeReport(BaseModel):
    generated_at: datetime
    case_count: int = Field(ge=0)
    amount_minor: int = Field(ge=0)
    counts_by_status: dict[DisputeStatus, int]
    counts_by_reason: dict[DisputeReason, int]
    sync_status: DisputeSyncStatus


class DisputeSyncProvider(Protocol):
    def submit(self, case: DisputeCase) -> DisputeSyncStatus: ...


class NoopDisputeSyncProvider:
    """Deterministic adapter until card-network and data-lake providers are wired."""

    def submit(self, case: DisputeCase) -> DisputeSyncStatus:
        del case
        return DisputeSyncStatus.PENDING


class DisputeRepository(Protocol):
    def create(self, case: DisputeCase) -> DisputeCase: ...

    def get(self, dispute_id: str) -> DisputeCase | None: ...

    def list(self) -> list[DisputeCase]: ...

    def save(self, case: DisputeCase) -> DisputeCase: ...

    def add_evidence(self, evidence: EvidenceSubmission) -> EvidenceSubmission: ...

    def evidence_for(self, dispute_id: str) -> list[EvidenceSubmission]: ...


@dataclass
class InMemoryDisputeRepository:
    cases: dict[str, DisputeCase] = field(default_factory=dict)
    by_idempotency_key: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, EvidenceSubmission] = field(default_factory=dict)

    def create(self, case: DisputeCase) -> DisputeCase:
        existing_id = self.by_idempotency_key.get(case.idempotency_key)
        if existing_id is not None:
            return self.cases[existing_id]
        if case.dispute_id in self.cases:
            raise ValueError("Dispute ID already exists")
        if case.status != DisputeStatus.OPENED:
            raise ValueError("New disputes must start in OPENED status")
        self.cases[case.dispute_id] = case
        self.by_idempotency_key[case.idempotency_key] = case.dispute_id
        return case

    def get(self, dispute_id: str) -> DisputeCase | None:
        return self.cases.get(dispute_id)

    def list(self) -> list[DisputeCase]:
        return list(self.cases.values())

    def save(self, case: DisputeCase) -> DisputeCase:
        self.cases[case.dispute_id] = case
        return case

    def add_evidence(self, evidence: EvidenceSubmission) -> EvidenceSubmission:
        existing = self.evidence.get(evidence.evidence_id)
        if existing is not None:
            return existing
        self.evidence[evidence.evidence_id] = evidence
        return evidence

    def evidence_for(self, dispute_id: str) -> list[EvidenceSubmission]:
        return [item for item in self.evidence.values() if item.dispute_id == dispute_id]


_ALLOWED_TRANSITIONS: dict[DisputeStatus, set[DisputeStatus]] = {
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


class DisputeService:
    def __init__(
        self,
        repository: DisputeRepository | None = None,
        sync_provider: DisputeSyncProvider | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository or InMemoryDisputeRepository()
        self.sync_provider = sync_provider or NoopDisputeSyncProvider()
        self.now = now or (lambda: datetime.now(UTC))

    def create(self, case: DisputeCase) -> DisputeCase:
        return self.repository.create(case)

    def transition(self, dispute_id: str, request: DisputeTransitionRequest) -> DisputeCase:
        case = self.repository.get(dispute_id)
        if case is None:
            raise KeyError("Dispute not found")
        if request.status == case.status:
            return case
        if request.status not in _ALLOWED_TRANSITIONS[case.status]:
            raise ValueError(f"Invalid transition from {case.status} to {request.status}")
        updated = case.model_copy(update={"status": request.status, "updated_at": self.now()})
        return self.repository.save(updated)

    def add_evidence(self, dispute_id: str, evidence: EvidenceSubmission) -> EvidenceSubmission:
        if self.repository.get(dispute_id) is None:
            raise KeyError("Dispute not found")
        if evidence.dispute_id != dispute_id:
            raise ValueError("Dispute ID does not match path")
        return self.repository.add_evidence(evidence)

    def report(
        self,
        status: DisputeStatus | None = None,
        reason: DisputeReason | None = None,
    ) -> DisputeReport:
        cases = self.repository.list()
        if status is not None:
            cases = [case for case in cases if case.status == status]
        if reason is not None:
            cases = [case for case in cases if case.reason == reason]
        counts_by_status = {
            value: sum(case.status == value for case in cases) for value in DisputeStatus
        }
        counts_by_reason = {
            value: sum(case.reason == value for case in cases) for value in DisputeReason
        }
        sync_results = [self.sync_provider.submit(case) for case in cases]
        if DisputeSyncStatus.FAILED in sync_results:
            sync_status = DisputeSyncStatus.FAILED
        elif DisputeSyncStatus.PENDING in sync_results:
            sync_status = DisputeSyncStatus.PENDING
        else:
            sync_status = DisputeSyncStatus.SUBMITTED
        return DisputeReport(
            generated_at=self.now(),
            case_count=len(cases),
            amount_minor=sum(case.amount_minor for case in cases),
            counts_by_status=counts_by_status,
            counts_by_reason=counts_by_reason,
            sync_status=sync_status,
        )
