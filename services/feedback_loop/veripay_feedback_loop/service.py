"""Append-only analyst feedback boundary. PLAN §21."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class ReviewLabel(StrEnum):
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    LEGITIMATE = "LEGITIMATE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class FeedbackSubmission(BaseModel):
    idempotency_key: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    analyst_id: str = Field(min_length=1)
    label: ReviewLabel
    reason_codes: list[str] = Field(default_factory=list)
    decision_action: str = Field(min_length=1)
    created_at: datetime | None = None


class FeedbackRecord(BaseModel):
    event_id: str
    idempotency_key: str
    transaction_id: str
    analyst_id: str
    label: ReviewLabel
    reason_codes: list[str]
    decision_action: str
    created_at: datetime


class FeedbackRepository(Protocol):
    def append(self, submission: FeedbackSubmission) -> FeedbackRecord: ...

    def list(self, transaction_id: str | None = None) -> list[FeedbackRecord]: ...


@dataclass
class InMemoryFeedbackRepository:
    records: list[FeedbackRecord] = field(default_factory=list)
    by_key: dict[str, FeedbackRecord] = field(default_factory=dict)

    def append(self, submission: FeedbackSubmission) -> FeedbackRecord:
        existing = self.by_key.get(submission.idempotency_key)
        if existing is not None:
            return existing
        record = FeedbackRecord(
            event_id=f"feedback_{len(self.records) + 1}",
            idempotency_key=submission.idempotency_key,
            transaction_id=submission.transaction_id,
            analyst_id=submission.analyst_id,
            label=submission.label,
            reason_codes=list(submission.reason_codes),
            decision_action=submission.decision_action,
            created_at=submission.created_at or datetime.now(UTC),
        )
        self.records.append(record)
        self.by_key[record.idempotency_key] = record
        return record

    def list(self, transaction_id: str | None = None) -> list[FeedbackRecord]:
        if transaction_id is None:
            return list(self.records)
        return [record for record in self.records if record.transaction_id == transaction_id]


def export_feedback(
    repository: FeedbackRepository,
    transaction_id: str | None = None,
    label: ReviewLabel | None = None,
) -> list[FeedbackRecord]:
    records = repository.list(transaction_id)
    if label is not None:
        records = [record for record in records if record.label == label]
    return records
