"""Shared deterministic fake + fixtures for the analyst API service tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from veripay_common.risk_policy import band_for_tier, tier_for_score


class FakeClient:
    def __init__(
        self,
        *,
        fraud: float = 0.05,
        anomaly: float = 0.05,
        action: str = "ALLOW",
        summary: str = "Risk profile is unremarkable for this customer.",
        network_risk: float = 0.0,
        network_available: bool = False,
        graph_fails: bool = False,
    ) -> None:
        self.fraud = fraud
        self.anomaly = anomaly
        self.action = action
        self.summary = summary
        self.network_risk = network_risk
        self.network_available = network_available
        self.graph_fails = graph_fails
        self.supervised_calls = 0
        self.anomaly_calls = 0
        self.feedback_appends = 0
        self.monitor_labels: list[str] = []
        self.graph_calls = 0

    def supervised_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        self.supervised_calls += 1
        return {
            "transaction_id": transaction_id,
            "fraud_probability": self.fraud,
            "risk_score": round(self.fraud * 100),
            "model_name": "supervised",
            "model_version": "v1",
            "model_available": True,
            "fallback": False,
        }

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        self.anomaly_calls += 1
        return {
            "transaction_id": transaction_id,
            "anomaly_score": self.anomaly,
            "risk_score": round(self.anomaly * 100),
            "is_anomaly": self.anomaly > 0.5,
            "model_name": "anomaly",
            "model_version": "v1",
            "model_available": True,
            "fallback": False,
        }

    def fuse_risk(self, transaction_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        available = [c for c in components if c["available"]]
        weights = sum(c["weight"] for c in available)
        score = round(sum(c["score"] * c["weight"] for c in available) / weights)
        tier = tier_for_score(score)
        band = band_for_tier(tier)
        return {
            "transaction_id": transaction_id,
            "unified_score": score,
            "band": band.value,
            "tier": tier.value,
            "components": components,
        }

    def decide(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "transaction_id": request["transaction_id"],
            "action": self.action,
            "risk_band": request["risk_band"],
            "risk_tier": request["risk_tier"],
            "reason_code": "COST_MINIMIZED",
            "expected_cost_minor": 10.0,
            "candidates": [],
            "friction": "NONE",
            "workflow": "SILENT_PASS",
            "timeout_seconds": 0,
            "timeout_fallback": "STANDARD_AUDIT",
            "processing_path": "FAST",
            "explanation_mode": "ASYNC",
            "evaluated_at": datetime.now(UTC).isoformat(),
        }

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "regulatory_reason_codes": [],
            "model_name": "fake",
            "prompt_version": "v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "fallback": False,
        }

    def retrain(self, version: str | None = None) -> dict[str, Any]:
        return {
            "status": "ok",
            "message": "retrained on feedback",
            "new_version": "v39",
            "metrics": {"roc_auc": 0.93, "pr_auc": 0.54, "precision": 0.52},
        }

    def append_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.feedback_appends += 1
        return {"status": "recorded", "transaction_id": payload["transaction_id"]}

    def record_monitor_label(self, transaction_id: str, label: str) -> dict[str, Any]:
        self.monitor_labels.append(label)
        return {"transaction_id": transaction_id, "label": label}

    def graph_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.graph_calls += 1
        if self.graph_fails:
            raise RuntimeError("graph engine unavailable")
        return {
            "transaction_id": payload["transaction_id"],
            "cc_num": payload["cc_num"],
            "network_risk_score": self.network_risk,
            "available": self.network_available,
            "findings": (
                [
                    "Shares merchant(s) with 1 confirmed-fraud account (flagged exposure 50%).",
                    "Connected to 1 other customer(s) via 1 shared merchant(s).",
                ]
                if self.network_available
                else []
            ),
            "features": {
                "merchant_degree": 1,
                "shared_counterparty_count": 1 if self.network_available else 0,
            },
            "ego": {
                "nodes": [
                    {
                        "id": f"c:{payload['cc_num']}",
                        "kind": "customer",
                        "label": str(payload["cc_num"]),
                        "status": "self",
                    },
                ],
                "edges": [],
            },
        }

    def graph_observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "recorded", "transaction_id": payload["transaction_id"]}

    def graph_ego(self, cc_num: int) -> dict[str, Any]:
        return {
            "cc_num": cc_num,
            "network_risk_score": self.network_risk,
            "available": self.network_available,
            "findings": (
                [
                    "Shares merchant(s) with 1 confirmed-fraud account (flagged exposure 50%).",
                ]
                if self.network_available
                else []
            ),
            "features": {
                "merchant_degree": 1,
                "shared_counterparty_count": 1 if self.network_available else 0,
            },
            "ego": {
                "nodes": [
                    {
                        "id": f"c:{cc_num}",
                        "kind": "customer",
                        "label": str(cc_num),
                        "status": "self",
                    },
                ],
                "edges": [],
            },
        }

    def graph_community(self, cc_num: int) -> dict[str, Any]:
        return {
            "graph": {
                "nodes": [
                    {
                        "id": f"c:{cc_num}",
                        "kind": "customer",
                        "label": str(cc_num),
                        "status": "self",
                    },
                ],
                "edges": [],
            },
            "stats": {
                "cluster_size": 2,
                "flagged_count": 1,
                "flagged_ratio": 0.5,
                "distinct_shared_merchants": 1,
                "total_volume": 760.0,
                "dominant_pattern": "fraud_ring",
            },
            "members": [
                {"cc_num": cc_num, "status": "self"},
                {"cc_num": 2, "status": "flagged"},
            ],
        }

    def health(self) -> dict[str, dict[str, Any]]:
        return {
            "supervised": {"status": "ok"},
            "anomaly": {"status": "ok"},
            "investigation": {"status": "ok"},
            "feedback": {"status": "ok"},
        }


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()
