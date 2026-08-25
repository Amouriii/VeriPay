from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from veripay_financial_context.main import create_app
from veripay_financial_context.service import (
    ContextAvailability,
    FinancialContextRequest,
    evaluate_financial_context,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_normal_baseline_is_available() -> None:
    result = evaluate_financial_context(
        FinancialContextRequest(
            transaction_id="tx-1",
            amount_minor=120,
            average_amount_minor=100,
            observed_at=NOW,
            now=NOW,
        )
    )
    assert result.availability == ContextAvailability.AVAILABLE
    assert result.normalized_score == 7


def test_stale_and_missing_baselines_are_explicit() -> None:
    stale = evaluate_financial_context(
        FinancialContextRequest(
            transaction_id="tx-stale",
            amount_minor=100,
            average_amount_minor=100,
            observed_at=NOW - timedelta(minutes=10),
            now=NOW,
        )
    )
    missing = evaluate_financial_context(
        FinancialContextRequest(transaction_id="tx-missing", amount_minor=100)
    )
    assert stale.availability == ContextAvailability.STALE
    assert missing.availability == ContextAvailability.UNAVAILABLE


def test_balance_deviation_is_high_risk_context() -> None:
    result = evaluate_financial_context(
        FinancialContextRequest(
            transaction_id="tx-balance",
            amount_minor=1_000,
            average_amount_minor=100,
            available_balance_minor=500,
            observed_at=NOW,
            now=NOW,
        )
    )
    assert result.normalized_score == 90
    assert result.reason_code == "AMOUNT_EXCEEDS_AVAILABLE_BALANCE"


def test_financial_context_endpoint() -> None:
    response = TestClient(create_app()).post(
        "/api/v1/context/financial/evaluate",
        json={"transaction_id": "tx-api", "amount_minor": 100},
    )
    assert response.status_code == 200
    assert response.json()["availability"] == "UNAVAILABLE"
