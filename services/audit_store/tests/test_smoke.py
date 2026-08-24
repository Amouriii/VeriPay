"""Smoke test: the service package imports and the app boots."""

from veripay_audit_store.main import app, create_app


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-audit_store"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
