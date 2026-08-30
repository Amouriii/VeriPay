from datetime import UTC, datetime

from fastapi.testclient import TestClient
from veripay_common.enums import DisputeReason, DisputeStatus
from veripay_fi_ops_portal.auth import ConfigTokenAuthenticator
from veripay_fi_ops_portal.main import create_app
from veripay_fi_ops_portal.service import (
    InMemoryFiOpsRepository,
    OpsAuditEventView,
    OpsDisputeView,
    OpsTransactionStateView,
    OpsTransactionView,
)


def test_fi_ops_operational_views_and_dispute_transition() -> None:
    repository = InMemoryFiOpsRepository()
    repository.save_transaction(
        OpsTransactionView(
            transaction_id="tx-ops",
            user_id="user-ops",
            amount_minor=100,
            currency="USD",
            risk_score=20,
            risk_band="APPROVE",
            decision="ALLOW",
        )
    )
    repository.save_audit_event(
        OpsAuditEventView(
            event_id="evt-ops",
            transaction_id="tx-ops",
            event_type="AUTHORIZED",
            actor="system",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    repository.save_transaction_state(
        OpsTransactionStateView(
            transaction_id="tx-ops",
            state="AUTHORIZED",
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    repository.save_dispute(
        OpsDisputeView(
            dispute_id="dispute-ops",
            transaction_id="tx-ops",
            amount_minor=100,
            currency="USD",
            status=DisputeStatus.OPENED,
            reason=DisputeReason.FRAUD,
        )
    )
    client = TestClient(
        create_app(repository, authenticator=ConfigTokenAuthenticator({"t": frozenset({"FI_OPS"})}))
    )
    auth = {"Authorization": "Bearer t"}
    assert (
        client.get("/api/v1/fi-ops/transactions/tx-ops/audit", headers=auth).json()[0]["event_id"]
        == "evt-ops"
    )
    assert (
        client.get("/api/v1/fi-ops/transactions/tx-ops/state", headers=auth).json()["state"]
        == "AUTHORIZED"
    )
    response = client.post(
        "/api/v1/fi-ops/disputes/dispute-ops/transition",
        json={"status": "REPRESENTED", "actor": "operator-1"},
        headers=auth,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REPRESENTED"
