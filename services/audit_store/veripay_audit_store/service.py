"""Audit and transaction-state domain logic.

The in-memory adapter mirrors the append-only and state-transition semantics
that the PostgreSQL adapter will implement against the populated database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field


class TransactionState(BaseModel):
    transaction_id: str = Field(min_length=1)
    state: str = Field(min_length=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}")
    transaction_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, str] = Field(default_factory=dict)


class AuditRepository(Protocol):
    def record_event(self, event: AuditEvent) -> AuditEvent: ...

    def events_for(self, transaction_id: str) -> list[AuditEvent]: ...

    def save_state(self, state: TransactionState) -> TransactionState: ...

    def get_state(self, transaction_id: str) -> TransactionState | None: ...


@dataclass
class InMemoryAuditRepository:
    events: list[AuditEvent] = field(default_factory=list)
    states: dict[str, TransactionState] = field(default_factory=dict)

    def record_event(self, event: AuditEvent) -> AuditEvent:
        if any(existing.event_id == event.event_id for existing in self.events):
            raise ValueError("Audit event already exists")
        self.events.append(event)
        return event

    def events_for(self, transaction_id: str) -> list[AuditEvent]:
        return [event for event in self.events if event.transaction_id == transaction_id]

    def save_state(self, state: TransactionState) -> TransactionState:
        self.states[state.transaction_id] = state
        return state

    def get_state(self, transaction_id: str) -> TransactionState | None:
        return self.states.get(transaction_id)
