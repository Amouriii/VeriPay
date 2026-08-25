from datetime import UTC, datetime

from fastapi.testclient import TestClient
from veripay_business_portal.main import create_app
from veripay_business_portal.service import (
    BusinessPolicyView,
    BusinessTransactionView,
    InMemoryBusinessPortalRepository,
    SpendSummary,
    WebhookStatusView,
)
from veripay_common.enums import DecisionAction, RiskBand, WebhookDecision


def test_business_portal_views() -> None:
    repository = InMemoryBusinessPortalRepository()
    repository.save_transaction(
        BusinessTransactionView(
            transaction_id="tx-1",
            merchant_id="merchant-1",
            amount_minor=250,
            currency="USD",
            risk_band=RiskBand.APPROVE,
            decision=DecisionAction.ALLOW,
            status="SETTLED",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    repository.save_spend_summary(
        SpendSummary(
            merchant_id="merchant-1",
            period="DAILY",
            spent_minor=250,
            limit_minor=1_000,
            remaining_minor=750,
            currency="USD",
        )
    )
    repository.save_policy(
        BusinessPolicyView(
            lock_id="lock-1",
            merchant_id="merchant-1",
            allowed_mccs="5411,5812",
            max_spend_per_txn_minor=500,
        )
    )
    repository.save_webhook(
        WebhookStatusView(
            event_id="event-1",
            merchant_id="merchant-1",
            decision=WebhookDecision.ALLOW,
            delivery_status="DELIVERED",
            attempts=1,
        )
    )
    client = TestClient(create_app(repository))
    assert (
        client.get("/api/v1/business/transactions?merchant_id=merchant-1").json()[0][
            "transaction_id"
        ]
        == "tx-1"
    )
    assert client.get("/api/v1/business/spend/merchant-1").json()["remaining_minor"] == 750
    assert len(client.get("/api/v1/business/policies").json()) == 1
    assert client.get("/api/v1/business/webhooks").json()[0]["delivery_status"] == "DELIVERED"
    assert client.get("/api/v1/business/access-policy").json()["portal"] == "BUSINESS"


def test_missing_spend_summary_is_not_found() -> None:
    response = TestClient(create_app()).get("/api/v1/business/spend/missing")
    assert response.status_code == 404
