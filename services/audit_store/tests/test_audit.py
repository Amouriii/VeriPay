from fastapi.testclient import TestClient
from veripay_audit_store.main import create_app
from veripay_audit_store.service import InMemoryAuditRepository


def test_audit_events_are_append_only_and_queryable() -> None:
    client = TestClient(create_app(InMemoryAuditRepository()))
    payload = {
        "event_id": "evt_001",
        "transaction_id": "tx_001",
        "event_type": "RISK_EVALUATED",
        "actor": "risk_fusion",
        "payload": {"score": "42"},
    }

    response = client.post("/api/v1/audit/events", json=payload)
    assert response.status_code == 201
    event = client.get("/api/v1/audit/transactions/tx_001/events").json()[0]
    assert {key: event[key] for key in payload} == payload

    duplicate = client.post("/api/v1/audit/events", json=payload)
    assert duplicate.status_code == 409


def test_transaction_state_is_saved_and_loaded() -> None:
    client = TestClient(create_app(InMemoryAuditRepository()))
    payload = {"transaction_id": "tx_001", "state": "AUTHORIZED", "metadata": {"source": "ingress"}}

    saved = client.put("/api/v1/audit/transactions/tx_001/state", json=payload)
    assert saved.status_code == 200
    loaded = client.get("/api/v1/audit/transactions/tx_001/state")
    assert loaded.status_code == 200
    assert loaded.json()["state"] == "AUTHORIZED"


def test_state_path_mismatch_and_missing_state() -> None:
    client = TestClient(create_app(InMemoryAuditRepository()))
    mismatch = client.put(
        "/api/v1/audit/transactions/tx_001/state",
        json={"transaction_id": "tx_002", "state": "AUTHORIZED"},
    )
    assert mismatch.status_code == 400
    assert client.get("/api/v1/audit/transactions/missing/state").status_code == 404
