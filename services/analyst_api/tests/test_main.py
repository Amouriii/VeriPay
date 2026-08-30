from typing import Any

from fastapi.testclient import TestClient
from veripay_analyst_api.clients import PipelineClient
from veripay_analyst_api.main import create_app


def _payload(cc_num: int = 1, txid: str = "tx_1") -> dict[str, Any]:
    return {
        "transaction": {
            "transaction_id": txid,
            "cc_num": cc_num,
            "amount": 100.0,
            "merchant": "m_amazon",
            "category": "ecommerce",
            "timestamp": "2026-08-10T10:00:00Z",
        }
    }


def _client(client: PipelineClient) -> TestClient:
    return TestClient(create_app(client=client))


def test_health(fake_client: PipelineClient) -> None:
    response = _client(fake_client).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "supervised" in body["models_loaded"]
    assert "anomaly" in body["models_loaded"]


def test_score(fake_client: PipelineClient) -> None:
    response = _client(fake_client).post("/score", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["transaction_id"] == "tx_1"
    assert body["decision"] == "PASS"
    assert "verification_action" in body


def test_explain(fake_client: PipelineClient) -> None:
    response = _client(fake_client).post("/explain", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["transaction_id"] == "tx_1"
    assert body["case_report"]["verdict"]
    assert body["case_report"]["crosschecked"] is True


def test_feedback_roundtrip(fake_client: PipelineClient) -> None:
    app = _client(fake_client)
    created = app.post("/score", json=_payload(cc_num=5, txid="tx_5"))
    assert created.status_code == 200
    recorded = app.post(
        "/feedback",
        json={
            "transaction_id": "tx_5",
            "cc_num": 5,
            "analyst_decision": "confirmed_fraud",
            "decision": "BLOCK",
        },
    )
    assert recorded.status_code == 200
    stats = app.get("/feedback/stats")
    assert stats.status_code == 200
    assert stats.json()["total_feedback"] == 1


def test_profile(fake_client: PipelineClient) -> None:
    response = _client(fake_client).get("/customer/1/profile")
    assert response.status_code == 200
    assert response.json()["cc_num"] == 1


def test_customer_network(fake_client: PipelineClient) -> None:
    fake_client.network_risk = 0.6  # type: ignore[attr-defined]
    fake_client.network_available = True  # type: ignore[attr-defined]
    response = _client(fake_client).get("/customer/1/network")
    assert response.status_code == 200
    body = response.json()
    assert body["cc_num"] == 1
    assert body["available"] is True
    assert body["network_risk_score"] == 0.6
    assert "nodes" in body["ego"]
    assert body["community"]["stats"]["dominant_pattern"] == "fraud_ring"


def test_customer_network_unavailable(fake_client: PipelineClient) -> None:
    response = _client(fake_client).get("/customer/1/network")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["network_risk_score"] == 0.0


def test_retrain(fake_client: PipelineClient) -> None:
    response = _client(fake_client).post("/retrain")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["new_version"] == "v39"


class _BrokenClient:
    """Minimal client whose first scoring call raises (simulates an outage)."""

    def supervised_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        raise RuntimeError("supervised down")

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        raise RuntimeError("down")

    def fuse_risk(self, transaction_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        raise RuntimeError("down")

    def decide(self, request: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("down")

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("down")

    def retrain(self, version: str | None = None) -> dict[str, Any]:
        raise RuntimeError("down")

    def health(self) -> dict[str, dict[str, Any]]:
        raise RuntimeError("down")


def test_score_returns_502_when_downstream_down() -> None:
    response = _client(_BrokenClient()).post("/score", json=_payload())
    assert response.status_code == 502


class _BlockScoreClient:
    """Minimal client that always scores a high-risk blocked transaction."""

    def supervised_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "fraud_probability": 0.9,
            "risk_score": 90,
            "model_name": "s",
            "model_version": "v",
            "model_available": True,
            "fallback": False,
        }

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "anomaly_score": 0.9,
            "risk_score": 90,
            "is_anomaly": True,
            "model_name": "a",
            "model_version": "v",
            "model_available": True,
            "fallback": False,
        }

    def fuse_risk(self, transaction_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "unified_score": 90,
            "band": "BLOCK",
            "tier": "HIGH",
            "components": components,
        }

    def decide(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "transaction_id": request["transaction_id"],
            "action": "DECLINE",
            "risk_band": request["risk_band"],
            "risk_tier": request["risk_tier"],
            "reason_code": "COST_MINIMIZED",
            "expected_cost_minor": 10.0,
            "friction": "NONE",
            "workflow": "SILENT_PASS",
            "timeout_seconds": 0,
            "timeout_fallback": "STANDARD_AUDIT",
            "processing_path": "FAST",
            "explanation_mode": "ASYNC",
            "evaluated_at": "2026-01-01T00:00:00Z",
        }

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": "High risk.",
            "regulatory_reason_codes": [],
            "model_name": "fake",
            "prompt_version": "v1",
            "generated_at": "2026-01-01T00:00:00Z",
            "fallback": False,
        }

    def retrain(self, version: str | None = None) -> dict[str, Any]:
        return {"status": "ok", "message": "", "new_version": "v", "metrics": {}}

    def health(self) -> dict[str, dict[str, Any]]:
        return {}


def test_alerts_list_scored_blocks_and_contributors() -> None:
    app = TestClient(create_app(client=_BlockScoreClient()))
    scored = app.post("/score", json=_payload(cc_num=1, txid="tx_block_1"))
    assert scored.status_code == 200
    body = scored.json()
    assert body["decision"] == "BLOCK"
    assert body["anomaly_top_contributors"]
    assert body["xgboost_feature_contributions"]

    alerts = app.get("/alerts")
    assert alerts.status_code == 200
    assert "tx_block_1" in [a["transaction_id"] for a in alerts.json()]


def test_score_lookup_by_id_and_404() -> None:
    app = TestClient(create_app(client=_BlockScoreClient()))
    app.post("/score", json=_payload(cc_num=1, txid="tx_block_1"))
    lookup = app.post("/score", json={"transaction_id": "tx_block_1"})
    assert lookup.status_code == 200
    assert lookup.json()["decision"] == "BLOCK"
    missing = app.post("/score", json={"transaction_id": "nope"})
    assert missing.status_code == 404


def test_pass_scores_not_in_alerts(fake_client: PipelineClient) -> None:
    app = _client(fake_client)
    app.post("/score", json=_payload(cc_num=7, txid="tx_pass"))
    assert app.get("/alerts").json() == []
