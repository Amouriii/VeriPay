"""External economic, seasonal, and geographic context. PLAN §17."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExternalAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class ExternalContextRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    region: str | None = Field(default=None, min_length=2, max_length=64)
    economic_risk_score: int | None = Field(default=None, ge=0, le=100)
    seasonal_risk_score: int | None = Field(default=None, ge=0, le=100)
    geographic_risk_score: int | None = Field(default=None, ge=0, le=100)
    observed_at: datetime | None = None
    now: datetime | None = None
    max_age_seconds: int = Field(default=900, ge=1)
    provenance: str = Field(default="external-context", min_length=1)


class ExternalContextResponse(BaseModel):
    transaction_id: str
    availability: ExternalAvailability
    normalized_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    reason_code: str
    provenance: str
    region: str | None = None
    observed_at: datetime | None = None


def evaluate_external_context(request: ExternalContextRequest) -> ExternalContextResponse:
    observed_at = request.observed_at
    if observed_at is not None and observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    now = request.now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    if observed_at is None:
        return ExternalContextResponse(
            transaction_id=request.transaction_id,
            availability=ExternalAvailability.UNAVAILABLE,
            normalized_score=50,
            confidence=0,
            reason_code="EXTERNAL_CONTEXT_UNAVAILABLE",
            provenance=request.provenance,
            region=request.region,
        )
    if (now - observed_at).total_seconds() > request.max_age_seconds:
        return ExternalContextResponse(
            transaction_id=request.transaction_id,
            availability=ExternalAvailability.STALE,
            normalized_score=50,
            confidence=0.1,
            reason_code="EXTERNAL_CONTEXT_STALE",
            provenance=request.provenance,
            region=request.region,
            observed_at=observed_at,
        )
    values = [
        value
        for value in (
            request.economic_risk_score,
            request.seasonal_risk_score,
            request.geographic_risk_score,
        )
        if value is not None
    ]
    if not values:
        return ExternalContextResponse(
            transaction_id=request.transaction_id,
            availability=ExternalAvailability.UNAVAILABLE,
            normalized_score=50,
            confidence=0,
            reason_code="EXTERNAL_SIGNALS_MISSING",
            provenance=request.provenance,
            region=request.region,
            observed_at=observed_at,
        )
    score = round(sum(values) / len(values))
    contradictory = len(values) > 1 and max(values) - min(values) >= 60
    return ExternalContextResponse(
        transaction_id=request.transaction_id,
        availability=ExternalAvailability.AVAILABLE,
        normalized_score=score,
        confidence=0.1 if contradictory else min(1.0, 0.4 + len(values) * 0.2),
        reason_code=(
            "EXTERNAL_SIGNALS_CONTRADICTORY" if contradictory else "EXTERNAL_CONTEXT_NORMALIZED"
        ),
        provenance=request.provenance,
        region=request.region,
        observed_at=observed_at,
    )
