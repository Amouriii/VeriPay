"""Integration tests for the rich feature-engine path.

Two layers:

1. **In-process (always runs in CI)** — drives the full orchestrator pipeline in
   rich mode behind a client that validates the exact model vector the
   orchestrator sends to the supervised/anomaly services. Because those
   services consume ``FEATURE_COLUMNS`` by position, any missing, extra, or
   non-finite column would silently mis-score — this pins the schema contract
   so the rich path provably still scores end-to-end.

2. **Live stack (env-gated)** — points at a running Compose ``analyst_api``
   (``VERIPAY_ANALYST_API_URL``, default ``http://localhost:8026``) and asserts
   a full ``/score`` round-trip returns rich mode with 16 causal features and
   both model axes available. Skipped unless the variable is set so CI without
   the stack stays green.
"""

from __future__ import annotations

import json
import math
import os
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from veripay_analyst_api.config import Settings
from veripay_analyst_api.features import FEATURE_COLUMNS
from veripay_analyst_api.features16 import FEATURES16
from veripay_analyst_api.models import Decision, GeoPoint, RiskLevel, ScoreRequest, TransactionInput
from veripay_analyst_api.profiles import ProfileStore, StoredTransaction
from veripay_analyst_api.service import AnalystOrchestrator

LIVE_URL = os.getenv("VERIPAY_ANALYST_API_URL", "http://localhost:8026")


class SchemaValidatingClient:
    """Pipeline client that fails if the rich-mode vector breaks the model contract."""

    def __init__(self) -> None:
        self.supervised_vectors: list[dict[str, float]] = []
        self.anomaly_vectors: list[dict[str, float]] = []

    def _check(self, features: dict[str, float]) -> None:
        # The model services consume FEATURE_COLUMNS positionally; the vector
        # must be exactly the schema — no missing, extra, or non-finite values.
        assert set(features) == set(FEATURE_COLUMNS), (
            f"vector keys {sorted(features)} != {list(FEATURE_COLUMNS)}"
        )
        for column in FEATURE_COLUMNS:
            assert column in features, f"missing model column {column}"
            assert math.isfinite(float(features[column])), f"non-finite {column}={features[column]}"

    def supervised_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        self._check(features)
        self.supervised_vectors.append(dict(features))
        fraud = 0.9 if features["amount_log"] > 8.0 else 0.05
        return {
            "transaction_id": transaction_id,
            "fraud_probability": fraud,
            "risk_score": round(fraud * 100),
            "model_available": True,
            "fallback": False,
        }

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        self._check(features)
        self.anomaly_vectors.append(dict(features))
        return {
            "transaction_id": transaction_id,
            "anomaly_score": 0.05,
            "risk_score": 5,
            "is_anomaly": False,
            "model_available": True,
            "fallback": False,
        }

    def fuse_risk(self, transaction_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        available = [c for c in components if c["available"]]
        weights = sum(c["weight"] for c in available)
        score = round(sum(c["score"] * c["weight"] for c in available) / weights)
        tier = "NO_RISK" if score < 33 else "MODERATE" if score < 66 else "HIGH"
        band = "APPROVE" if score < 33 else "VERIFY" if score < 66 else "BLOCK"
        return {
            "transaction_id": transaction_id,
            "unified_score": score,
            "band": band,
            "tier": tier,
            "components": components,
        }

    def decide(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "transaction_id": request["transaction_id"],
            "action": "ALLOW" if request["risk_score"] < 66 else "DECLINE",
            "risk_band": request["risk_band"],
            "risk_tier": request["risk_tier"],
            "reason_code": "TEST",
        }

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "", "fallback": False}

    def retrain(self, version: str | None = None) -> dict[str, Any]:
        return {"status": "ok"}

    def append_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "recorded"}

    def record_monitor_label(self, transaction_id: str, label: str) -> dict[str, Any]:
        return {"transaction_id": transaction_id, "label": label}

    def graph_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"network_risk_score": 0.0, "available": False, "findings": []}

    def graph_observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "recorded"}

    def health(self) -> dict[str, dict[str, Any]]:
        return {
            "supervised": {"status": "ok"},
            "anomaly": {"status": "ok"},
            "investigation": {"status": "ok"},
            "feedback": {"status": "ok"},
        }


def _transaction(cc_num: int = 21, amount: float = 120.0) -> TransactionInput:
    home = GeoPoint(lat=40.7, lon=-74.0)
    return TransactionInput(
        transaction_id=f"itx_{cc_num}",
        cc_num=cc_num,
        amount=amount,
        merchant="m_integration",
        category="ecommerce",
        timestamp=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
        location=home,
        merchant_location=GeoPoint(lat=40.7, lon=-73.9),
        mcc_risk=0.35,
        device_trust=-1.0,
        network_trust=-1.0,
    )


def _rich_settings() -> Settings:
    configured = Settings()
    configured.FEATURE_MODE = "rich"
    return configured


# ---- layer 1: in-process schema + end-to-end pipeline ---------------------


def test_rich_vector_satisfies_model_contract_and_scores() -> None:
    client = SchemaValidatingClient()
    store = ProfileStore()
    # Seed a little past history so the causal engine has velocity/amount data.
    base = datetime(2026, 8, 12, 10, 0, tzinfo=UTC)
    home = GeoPoint(lat=40.7, lon=-74.0)
    for i in range(4):
        store.add_transaction(
            StoredTransaction(
                transaction_id=f"itx_hist_{i}",
                cc_num=21,
                amount=30.0 + i,
                merchant="m_history",
                category="retail",
                timestamp=base - timedelta(days=7 - i, hours=1),
                location=home,
                merchant_location=GeoPoint(lat=40.7, lon=-73.9),
                decision=Decision.PASS,
            )
        )
    orch = AnalystOrchestrator(client=client, store=store, settings=_rich_settings())
    resp = orch.score(ScoreRequest(transaction=_transaction(21, 420.0)))

    # The rich-mode vector was sent to both model services and satisfied the
    # exact FEATURE_COLUMNS schema on every call.
    assert client.supervised_vectors and client.anomaly_vectors
    for vector in client.supervised_vectors + client.anomaly_vectors:
        assert list(vector) == list(FEATURE_COLUMNS)

    # The vector actually scored: both axes available, decision produced, and
    # the whole fused decision surfaced.
    assert resp.feature_mode == "rich"
    assert resp.model_available is True
    assert {row.name for row in resp.features} == set(FEATURES16)
    assert len(resp.features16) == 16
    assert resp.decision in (
        Decision.BLOCK,
        Decision.REVIEW_STEALTH,
        Decision.REVIEW_UNUSUAL,
        Decision.PASS,
    )
    assert resp.risk_level in (RiskLevel.HIGH, RiskLevel.MODERATE, RiskLevel.LOW)
    assert 0 <= resp.fraud_probability <= 1
    assert 0 <= resp.anomaly_score <= 1
    assert 0 <= resp.fused_risk_score <= 100


def test_rich_vector_matches_basic_vector_keys() -> None:
    """Rich mode emits the same column schema as basic mode (only values differ)."""
    client = SchemaValidatingClient()
    orch = AnalystOrchestrator(client=client, store=ProfileStore(), settings=_rich_settings())
    orch.score(ScoreRequest(transaction=_transaction(22, 88.0)))
    vector = client.supervised_vectors[0]
    assert list(vector) == list(FEATURE_COLUMNS)
    # Rich mode must populate the same columns with real signal — the amount,
    # risk, trust, hour, and geo-derived distance columns all carry values for
    # a fresh customer (the velocity/device columns are legitimately 0).
    assert vector["amount_log"] > 0.0
    assert vector["mcc_risk"] > 0.0
    assert vector["device_trust"] < 0.0  # unknown device trust passed through
    assert vector["distance_km"] > 0.0  # derived from the rich geo engine


# ---- layer 2: live Compose stack (env-gated) ------------------------------


def _live_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{LIVE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _live_get(path: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{LIVE_URL}{path}", timeout=10) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


@pytest.mark.skipif(
    not os.getenv("VERIPAY_ANALYST_API_URL"),
    reason="live Compose stack not configured (set VERIPAY_ANALYST_API_URL)",
)
def test_live_rich_score_scores_end_to_end() -> None:
    health = _live_get("/health")
    assert health["status"] == "ok"
    assert "supervised" in health["models_loaded"]
    assert "anomaly" in health["models_loaded"]

    tx = _transaction(cc_num=91, amount=360.0)
    body = {"transaction": json.loads(tx.model_dump_json())}
    result = _live_post("/score", body)

    assert result["transaction_id"] == tx.transaction_id
    assert result["feature_mode"] == "rich", "Compose analyst_api must run FEATURE_MODE=rich"
    assert len(result["features16"]) == 16
    assert {row["name"] for row in result["features16"]} == set(FEATURES16)
    assert result["model_available"] is True
    assert result["decision"] in ("BLOCK", "REVIEW_STEALTH", "REVIEW_UNUSUAL", "PASS")
    assert 0 <= result["fraud_probability"] <= 1
    assert 0 <= result["anomaly_score"] <= 1
    assert 0 <= result["fused_risk_score"] <= 100
