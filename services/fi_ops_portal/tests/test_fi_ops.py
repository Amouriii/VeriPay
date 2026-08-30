from datetime import UTC, datetime

from fastapi.testclient import TestClient
from veripay_common.enums import DecisionAction, DisputeReason, DisputeStatus, RiskBand
from veripay_fi_ops_portal.auth import ConfigTokenAuthenticator
from veripay_fi_ops_portal.main import create_app
from veripay_fi_ops_portal.service import (
    InMemoryFiOpsRepository,
    OpsDisputeView,
    OpsRiskComponent,
    OpsTransactionView,
)


def _authenticator() -> ConfigTokenAuthenticator:
    return ConfigTokenAuthenticator({"t": frozenset({"FI_OPS", "ADMIN"})})


def test_fi_ops_views_and_report() -> None:
    repository = InMemoryFiOpsRepository()
    repository.save_transaction(
        OpsTransactionView(
            transaction_id="tx-1",
            user_id="user-1",
            amount_minor=1_000,
            currency="USD",
            risk_score=90,
            risk_band=RiskBand.BLOCK,
            decision=DecisionAction.DECLINE,
            reason_codes=["DCVV_MISMATCH"],
            components=[OpsRiskComponent(component="rules", score=100)],
        )
    )
    repository.save_dispute(
        OpsDisputeView(
            dispute_id="dispute-1",
            transaction_id="tx-1",
            amount_minor=1_000,
            currency="USD",
            status=DisputeStatus.OPENED,
            reason=DisputeReason.FRAUD,
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    client = TestClient(create_app(repository, authenticator=_authenticator()))
    auth = {"Authorization": "Bearer t"}
    transaction = client.get("/api/v1/fi-ops/transactions/tx-1", headers=auth)
    report = client.get("/api/v1/fi-ops/reports/regulatory", headers=auth)
    policy = client.get("/api/v1/fi-ops/access-policy")
    assert transaction.status_code == 200
    assert transaction.json()["reason_codes"] == ["DCVV_MISMATCH"]
    assert report.json()["blocked_transaction_count"] == 1
    assert report.json()["disputed_amount_minor"] == 1_000
    assert policy.json()["required_roles"] == ["FI_OPS", "ADMIN"]


def test_missing_fi_ops_transaction_is_not_found() -> None:
    client = TestClient(create_app(authenticator=_authenticator()))
    response = client.get(
        "/api/v1/fi-ops/transactions/missing", headers={"Authorization": "Bearer t"}
    )
    assert response.status_code == 404
