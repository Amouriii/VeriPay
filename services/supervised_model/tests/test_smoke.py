"""Smoke + scoring tests for the supervised fraud model service."""

from __future__ import annotations

from veripay_supervised_model.main import app, create_app
from veripay_supervised_model.service import (
    ScoreRequest,
    _ModelBundle,
    evaluate,
)


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-supervised_model"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def _high_risk_features() -> dict[str, float]:
    return {
        "amount_log": 11.5,
        "mcc_risk": 0.9,
        "velocity_5m": 14.0,
        "device_trust": 0.0,
        "network_trust": 0.0,
        "impossible_travel": 1.0,
        "new_device": 1.0,
        "hour_of_day": 3.0,
        "weekend": 1.0,
        "distance_km": 1200.0,
    }


def test_evaluate_uses_trained_model_when_available(monkeypatch) -> None:
    import numpy as np

    class _FakeModel:
        def predict_proba(self, matrix):  # type: ignore[no-untyped-def]
            # matrix shape (1, 10); fraud class is column 1
            return np.array([[0.35, 0.65]])

    monkeypatch.setattr(
        "veripay_supervised_model.service._load_model",
        lambda: _ModelBundle(_FakeModel(), version="test-v1", available=True),
    )
    response = evaluate(ScoreRequest(transaction_id="tx_1", features=_high_risk_features()))
    assert response.fraud_probability == 0.65
    assert response.risk_score == 65
    assert response.model_name == "supervised"
    assert response.model_version == "test-v1"
    assert response.model_available is True
    assert response.fallback is False


def test_evaluate_falls_back_to_heuristic_when_model_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "veripay_supervised_model.service._load_model",
        lambda: _ModelBundle(None, version="unavailable", available=False),
    )
    response = evaluate(ScoreRequest(transaction_id="tx_1", features=_high_risk_features()))
    assert response.model_available is False
    assert response.fallback is True
    # Heuristic must still be a bounded 0-100 score.
    assert 0 <= response.risk_score <= 100
    assert response.fraud_probability == round(response.risk_score / 100, 4)


def test_heuristic_trust_semantics() -> None:
    from veripay_supervised_model.service import _heuristic_risk

    trusted = _heuristic_risk({"device_trust": 1.0, "network_trust": 1.0})
    unknown = _heuristic_risk({"device_trust": -1.0, "network_trust": -1.0})
    untrusted = _heuristic_risk({"device_trust": 0.0, "network_trust": 0.0})
    assert untrusted > unknown >= trusted


def test_score_endpoint(monkeypatch) -> None:
    import numpy as np
    from fastapi.testclient import TestClient

    class _FakeModel:
        def predict_proba(self, matrix):  # type: ignore[no-untyped-def]
            return np.array([[0.5, 0.5]])

    monkeypatch.setattr(
        "veripay_supervised_model.service._load_model",
        lambda: _ModelBundle(_FakeModel(), version="test-v1", available=True),
    )
    client = TestClient(app)
    resp = client.post(
        "/api/v1/score",
        json={"transaction_id": "tx_1", "features": _high_risk_features()},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["fraud_probability"] == 0.5
    assert payload["risk_score"] == 50
    assert payload["model_version"] == "test-v1"


def test_score_endpoint_rejects_missing_transaction_id() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post("/api/v1/score", json={"features": {}})
    assert resp.status_code == 422
