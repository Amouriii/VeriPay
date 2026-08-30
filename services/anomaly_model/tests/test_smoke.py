"""Smoke + scoring tests for the anomaly model service."""

from __future__ import annotations

from veripay_anomaly_model.main import app, create_app
from veripay_anomaly_model.service import (
    AnomalyRequest,
    _ModelBundle,
    evaluate,
)


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-anomaly_model"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def _outlier_features() -> dict[str, float]:
    return {
        "amount_log": 12.0,
        "mcc_risk": 0.9,
        "velocity_5m": 20.0,
        "device_trust": 0.0,
        "network_trust": -1.0,
        "impossible_travel": 1.0,
        "new_device": 1.0,
        "hour_of_day": 2.0,
        "weekend": 1.0,
        "distance_km": 3000.0,
    }


def test_evaluate_uses_trained_model_when_available(monkeypatch) -> None:
    class _FakeModel:
        def decision_function(self, matrix):  # type: ignore[no-untyped-def]
            return [0.4]  # negative => anomaly; -decision = -0.4

    monkeypatch.setattr(
        "veripay_anomaly_model.service._load_model",
        lambda: _ModelBundle(_FakeModel(), version="test-v1", available=True),
    )
    response = evaluate(AnomalyRequest(transaction_id="tx_1", features=_outlier_features()))
    assert response.model_available is True
    assert 0.0 < response.anomaly_score < 1.0
    assert 0 <= response.risk_score <= 100
    assert response.is_anomaly is False  # decision 0.4 => not anomalous


def test_evaluate_falls_back_when_model_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "veripay_anomaly_model.service._load_model",
        lambda: _ModelBundle(None, version="unavailable", available=False),
    )
    response = evaluate(AnomalyRequest(transaction_id="tx_1", features=_outlier_features()))
    assert response.model_available is False
    assert response.fallback is True
    assert response.is_anomaly is False


def test_score_endpoint(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    class _FakeModel:
        def decision_function(self, matrix):  # type: ignore[no-untyped-def]
            return [-0.8]  # negative => anomalous

    monkeypatch.setattr(
        "veripay_anomaly_model.service._load_model",
        lambda: _ModelBundle(_FakeModel(), version="test-v1", available=True),
    )
    client = TestClient(app)
    resp = client.post(
        "/api/v1/score",
        json={"transaction_id": "tx_1", "features": _outlier_features()},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["is_anomaly"] is True
    assert payload["model_version"] == "test-v1"
    assert 0.0 < payload["anomaly_score"] < 1.0


def test_score_endpoint_rejects_missing_transaction_id() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post("/api/v1/score", json={"features": {}})
    assert resp.status_code == 422
