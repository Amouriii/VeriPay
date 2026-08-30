"""Smoke tests: the model monitor app boots and endpoints respond."""

from __future__ import annotations

from veripay_model_monitor.main import app, create_app


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-model_monitor"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_record_and_list_observations() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.post(
        "/api/v1/monitor/observations",
        json={"transaction_id": "tx_1", "features": {"amount_log": 8.0}, "score": 42},
    )
    assert resp.status_code == 200
    assert resp.json()["transaction_id"] == "tx_1"
    listed = client.get("/api/v1/monitor/observations").json()
    assert [obs["transaction_id"] for obs in listed] == ["tx_1"]


def test_feedback_endpoint() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    resp = client.post(
        "/api/v1/monitor/feedback",
        params={"transaction_id": "tx_1", "label": "CONFIRMED_FRAUD"},
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "CONFIRMED_FRAUD"


def test_drift_no_reference_profile(monkeypatch, tmp_path) -> None:
    from fastapi.testclient import TestClient
    from veripay_model_monitor import config

    monkeypatch.setattr(config.settings, "REGISTRY_PATH", tmp_path / "nope.json")
    monkeypatch.setattr(config.settings, "MODEL_DIR", tmp_path / "models")
    client = TestClient(create_app())
    resp = client.get("/api/v1/monitor/drift")
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "NO_REFERENCE_PROFILE"
