"""Financial and behavioral context normalization. PLAN §17."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ContextAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class FinancialContextRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    average_amount_minor: float | None = Field(default=None, ge=0)
    available_balance_minor: int | None = Field(default=None, ge=0)
    daily_spend_minor: int | None = Field(default=None, ge=0)
    account_age_days: int | None = Field(default=None, ge=0)
    observed_at: datetime | None = None
    now: datetime | None = None
    max_age_seconds: int = Field(default=300, ge=1)


class FinancialContextResponse(BaseModel):
    transaction_id: str
    availability: ContextAvailability
    normalized_score: int = Field(ge=0, le=100)
    deviation_ratio: float | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0, le=1)
    reason_code: str
    provenance: str
    observed_at: datetime | None = None


def _now(request: FinancialContextRequest) -> datetime:
    value = request.now or datetime.now(UTC)
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def evaluate_financial_context(request: FinancialContextRequest) -> FinancialContextResponse:
    """Return a bounded behavioral deviation without making an authorization decision."""
    observed_at = request.observed_at
    if observed_at is not None and observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    if observed_at is None:
        return FinancialContextResponse(
            transaction_id=request.transaction_id,
            availability=ContextAvailability.UNAVAILABLE,
            normalized_score=50,
            confidence=0,
            reason_code="BASELINE_UNAVAILABLE",
            provenance="financial-context",
        )
    if (_now(request) - observed_at).total_seconds() > request.max_age_seconds:
        return FinancialContextResponse(
            transaction_id=request.transaction_id,
            availability=ContextAvailability.STALE,
            normalized_score=50,
            confidence=0.1,
            reason_code="BASELINE_STALE",
            provenance="financial-context",
            observed_at=observed_at,
        )
    if request.average_amount_minor is None or request.average_amount_minor == 0:
        return FinancialContextResponse(
            transaction_id=request.transaction_id,
            availability=ContextAvailability.UNAVAILABLE,
            normalized_score=50,
            confidence=0,
            reason_code="AVERAGE_AMOUNT_UNAVAILABLE",
            provenance="financial-context",
            observed_at=observed_at,
        )

    ratio = request.amount_minor / request.average_amount_minor
    score = min(100, round(max(0, (ratio - 1) * 35)))
    if (
        request.available_balance_minor is not None
        and request.amount_minor > request.available_balance_minor
    ):
        score = 90
        reason = "AMOUNT_EXCEEDS_AVAILABLE_BALANCE"
    elif (
        request.daily_spend_minor is not None
        and request.daily_spend_minor + request.amount_minor > request.average_amount_minor * 5
    ):
        score = max(score, 75)
        reason = "DAILY_SPEND_DEVIATION"
    elif ratio > 1:
        reason = "AMOUNT_ABOVE_BASELINE"
    else:
        reason = "WITHIN_BEHAVIORAL_BASELINE"
    confidence = 0.8 if request.account_age_days is None or request.account_age_days >= 30 else 0.55
    return FinancialContextResponse(
        transaction_id=request.transaction_id,
        availability=ContextAvailability.AVAILABLE,
        normalized_score=score,
        deviation_ratio=round(ratio, 4),
        confidence=confidence,
        reason_code=reason,
        provenance="financial-context",
        observed_at=observed_at,
    )
