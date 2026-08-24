"""Smoke test: the service package imports and the app boots."""
from veripay_external_context.main import app, create_app


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-external_context"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
