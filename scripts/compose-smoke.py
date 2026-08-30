"""Strict HTTP smoke test for the compose CI job.

Walks a representative slice of the VeriPay risk pipeline over HTTP and FAILS
(exit 1) if any service is unreachable or any endpoint returns an unexpected
response: health -> rules -> supervised model -> anomaly model -> risk fusion
-> decision engine -> investigation agent.

This test intentionally needs no trained model artifacts (the scoring services
serve a deterministic fallback) and no LLM key (the investigation agent falls
back to its governed explainer), so it runs in CI on the built images.

Services are contacted on their documented ports (override with
VERIPAY_<SERVICE>_URL, e.g. VERIPAY_RULE_ENGINE_URL=http://localhost:8005).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

SERVICES: dict[str, tuple[str, int]] = {
    "rule_engine": ("/api/v1/rules/evaluate", 8005),
    "supervised_model": ("/api/v1/score", 8006),
    "anomaly_model": ("/api/v1/score", 8007),
    "risk_fusion": ("/api/v1/risk/fuse", 8012),
    "decision_engine": ("/api/v1/decision/evaluate", 8013),
    "investigation_agent": ("/api/v1/investigate", 8014),
}

HIGH_RISK_FEATURES: dict[str, float] = {
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


def _base(name: str) -> str:
    return os.getenv(f"VERIPAY_{name.upper()}_URL", f"http://localhost:{SERVICES[name][1]}")


def _request(
    name: str, method: str, path: str, payload: dict[str, Any] | None
) -> tuple[int, dict[str, Any]]:
    """Return (status, json) or raise if the service is unreachable."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        _base(name) + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def wait_for_health(name: str, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            status, _ = _request(name, "GET", "/health", None)
            if status == 200:
                return
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError):
            pass
        time.sleep(2)
    raise SystemExit(f"FAIL: {name} did not become healthy within {timeout:.0f}s")


def assert_field(response: dict[str, Any], key: str, service: str) -> None:
    if key not in response:
        raise SystemExit(f"FAIL: {service} response missing '{key}': {response}")


def main() -> int:
    print("VeriPay compose HTTP smoke test")
    print("=" * 60)

    # 1. All services must report healthy (are the images actually serving?).
    for name in SERVICES:
        wait_for_health(name)
        print(f"  ok  {name} -> /health 200")

    # 2. Walk the risk pipeline end-to-end over HTTP.
    rules: dict[str, Any]
    _, rules = _request(
        "rule_engine",
        "POST",
        SERVICES["rule_engine"][0],
        {
            "dcvv_match": True,
            "merchant_allowed": True,
            "velocity_count_5m": 14,
            "impossible_travel": True,
            "device_trusted": False,
            "network_trusted": False,
        },
    )
    assert_field(rules, "findings", "rule_engine")
    rl = rules["findings"]
    if not rl:
        raise SystemExit("FAIL: rule_engine returned no findings")
    triggered = [f.get("code") for f in rl if f.get("triggered")]
    print(f"  ok  rule_engine  -> {len(rl)} findings, triggered={triggered}")

    sc_payload = {"transaction_id": "tx_smoke_high", "features": HIGH_RISK_FEATURES}

    _, supervised = _request(
        "supervised_model", "POST", SERVICES["supervised_model"][0], sc_payload
    )
    assert_field(supervised, "fraud_probability", "supervised_model")
    print(f"  ok  supervised_model -> fraud_probability={supervised['fraud_probability']}")

    _, anomaly = _request("anomaly_model", "POST", SERVICES["anomaly_model"][0], sc_payload)
    assert_field(anomaly, "anomaly_score", "anomaly_model")
    print(f"  ok  anomaly_model -> anomaly_score={anomaly['anomaly_score']}")

    _, fusion = _request(
        "risk_fusion",
        "POST",
        SERVICES["risk_fusion"][0],
        {
            "transaction_id": "tx_smoke_high",
            "components": [
                {"component": "rules", "score": 60, "weight": 0.25, "available": True},
                {"component": "supervised", "score": 21, "weight": 0.30, "available": True},
                {"component": "anomaly", "score": 54, "weight": 0.25, "available": True},
                {"component": "device_integrity", "score": 50, "weight": 0.20, "available": True},
            ],
        },
    )
    assert_field(fusion, "unified_score", "risk_fusion")
    print(f"  ok  risk_fusion -> unified_score={fusion['unified_score']}")

    _, decision = _request(
        "decision_engine",
        "POST",
        SERVICES["decision_engine"][0],
        {
            "transaction_id": "tx_smoke_high",
            "risk_score": fusion["unified_score"],
            "payment_rail": "CARD",
        },
    )
    assert_field(decision, "action", "decision_engine")
    print(f"  ok  decision_engine -> action={decision['action']}")

    _, investigation = _request(
        "investigation_agent",
        "POST",
        SERVICES["investigation_agent"][0],
        {
            "transaction_id": "tx_smoke_high",
            "transaction": {"amount_minor": 499900, "merchant_id": "m_amazon"},
            "transaction_history": [],
            "risk_score": fusion["unified_score"],
            "macro_context": {"country": "US"},
        },
    )
    assert_field(investigation, "summary", "investigation_agent")
    print(f"  ok  investigation_agent -> model={investigation.get('model_name')}")

    print("\ncompose HTTP smoke test OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
