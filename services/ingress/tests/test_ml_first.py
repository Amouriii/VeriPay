from typing import Any

from veripay_ingress.service import Transaction, calculate_risk


class Settings:
    SUPERVISED_URL = "http://supervised"
    ANOMALY_URL = "http://anomaly"
    RISK_FUSION_URL = "http://fusion"
    ML_TIMEOUT_SECONDS = 1.0


def _tx() -> Transaction:
    return Transaction(
        transaction_id="tx_ml",
        user_id="user_1",
        amount_minor=1000,
        currency="USD",
    )


def test_ml_scores_are_used_before_legacy_baseline(monkeypatch: Any) -> None:
    calls: list[str] = []

    def post(url: str, path: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        calls.append(url)
        if url == "http://supervised":
            return {"fraud_probability": 0.9, "model_available": True, "model_name": "supervised", "model_version": "v7"}
        if url == "http://anomaly":
            return {"anomaly_score": 0.8, "model_available": True, "model_name": "anomaly", "model_version": "v3"}
        return {"unified_score": 85, "band": "BLOCK", "tier": "HIGH"}

    monkeypatch.setattr("veripay_ingress.service._post_json", post)
    result = calculate_risk(_tx(), settings=Settings())
    assert result.unified_score == 85
    assert calls == ["http://supervised", "http://anomaly", "http://fusion"]
    assert {component.component for component in result.components} == {"supervised", "anomaly"}


def test_ml_failure_falls_back_to_legacy_scheme(monkeypatch: Any) -> None:
    def unavailable(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise OSError("model unavailable")

    monkeypatch.setattr("veripay_ingress.service._post_json", unavailable)
    result = calculate_risk(_tx(), settings=Settings())
    assert result.unified_score == 10
    assert result.components[0].component == "ingress_baseline"
