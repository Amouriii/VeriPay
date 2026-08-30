"""Smoke test: the service package imports and the app boots."""

from veripay_investigation_agent.main import app, create_app


def test_app_factory() -> None:
    a = create_app()
    assert a.title == "veripay-investigation_agent"


def test_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_investigate_endpoint() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post(
        "/api/v1/investigate",
        json={
            "transaction_id": "tx_1",
            "transaction": {"amount_minor": 4999, "merchant_id": "m_amazon"},
            "transaction_history": [],
            "risk_score": 42,
            "macro_context": {"country": "US"},
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["model_name"] == "local-governed-explainer"
    assert payload["prompt_version"] == "fraud-explanation-v1"
    assert "RISK_SCORE_MODERATE" in payload["regulatory_reason_codes"]
    assert "MACRO_CONTEXT_CONSIDERED" in payload["regulatory_reason_codes"]
