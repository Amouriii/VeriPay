"""Smoke test: the service package imports and the app boots."""
from app.main import app, create_app


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-feedback_loop"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
