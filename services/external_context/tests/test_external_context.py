from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from veripay_external_context.main import create_app
from veripay_external_context.service import (
    ExternalAvailability,
    ExternalContextRequest,
    evaluate_external_context,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_external_signals_are_normalized_with_provenance() -> None:
    result = evaluate_external_context(
        ExternalContextRequest(
            transaction_id="tx-1",
            region="US-NY",
            economic_risk_score=20,
            seasonal_risk_score=40,
            geographic_risk_score=60,
            observed_at=NOW,
            now=NOW,
            provenance="fixture-provider",
        )
    )
    assert result.availability == ExternalAvailability.AVAILABLE
    assert result.normalized_score == 40
    assert result.provenance == "fixture-provider"


def test_stale_and_missing_external_signals_are_not_zero_risk() -> None:
    stale = evaluate_external_context(
        ExternalContextRequest(
            transaction_id="tx-stale",
            economic_risk_score=0,
            observed_at=NOW - timedelta(hours=1),
            now=NOW,
        )
    )
    missing = evaluate_external_context(
        ExternalContextRequest(transaction_id="tx-missing", observed_at=NOW, now=NOW)
    )
    assert stale.availability == ExternalAvailability.STALE
    assert stale.normalized_score == 50
    assert missing.availability == ExternalAvailability.UNAVAILABLE


def test_contradictory_external_signals_reduce_confidence() -> None:
    result = evaluate_external_context(
        ExternalContextRequest(
            transaction_id="tx-contradictory",
            economic_risk_score=5,
            geographic_risk_score=95,
            observed_at=NOW,
            now=NOW,
        )
    )
    assert result.reason_code == "EXTERNAL_SIGNALS_CONTRADICTORY"
    assert result.confidence == 0.1


def test_external_context_endpoint() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/context/external/evaluate",
        json={
            "transaction_id": "tx-api",
            "observed_at": "2026-01-01T00:00:00Z",
            "now": "2026-01-01T00:00:00Z",
            "economic_risk_score": 80,
        },
    )
    assert response.status_code == 200
    assert response.json()["normalized_score"] == 80
