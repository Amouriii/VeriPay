from fastapi.testclient import TestClient
from veripay_compliance_engine.main import create_app
from veripay_compliance_engine.service import (
    ComplianceOutcome,
    ComplianceRequest,
    evaluate_compliance,
)


def test_tokenization_failure_rejects() -> None:
    result = evaluate_compliance(
        ComplianceRequest(transaction_id="tx-1", amount_minor=100, currency="USD", tokenized=False)
    )
    assert result.outcome == ComplianceOutcome.REJECT
    assert result.blocking is True


def test_high_value_unauthenticated_payment_requires_challenge() -> None:
    result = evaluate_compliance(
        ComplianceRequest(transaction_id="tx-2", amount_minor=10_000, currency="USD")
    )
    assert result.outcome == ComplianceOutcome.CHALLENGE
    assert result.blocking is True


def test_untrusted_network_rejects_and_missing_network_is_unavailable() -> None:
    rejected = evaluate_compliance(
        ComplianceRequest(
            transaction_id="tx-3", amount_minor=100, currency="USD", network_trusted=False
        )
    )
    unavailable = evaluate_compliance(
        ComplianceRequest(
            transaction_id="tx-4", amount_minor=100, currency="USD", network_trusted=None
        )
    )
    assert rejected.outcome == ComplianceOutcome.REJECT
    assert unavailable.outcome == ComplianceOutcome.UNAVAILABLE
    assert unavailable.blocking is True


def test_compliance_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/compliance/evaluate",
        json={"transaction_id": "tx-api", "amount_minor": 100, "currency": "USD"},
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "PASS"
