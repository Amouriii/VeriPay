"""End-to-end demo driver for the VeriPay risk pipeline.

Submits demo transactions and walks every stage of the pipeline against the
locally running services: ingress -> rules -> supervised model -> anomaly
model -> risk fusion -> decision engine -> LLM investigation agent.

Prerequisites (see docs/demo.md):

    make up
    pip install -e "ml[training]"
    python ml/datasets/generate_synthetic.py
    python ml/supervised/train.py
    python ml/anomaly/train.py

Run:

    python scripts/seed-demo.py

Services are contacted on their documented ports (override with
VERIPAY_<SERVICE>_URL, e.g. VERIPAY_INGRESS_URL=http://localhost:8001).
Stages skip gracefully with a hint if a service is not running.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

SERVICES: dict[str, int] = {
    "ingress": 8001,
    "rule_engine": 8005,
    "supervised_model": 8006,
    "anomaly_model": 8007,
    "risk_fusion": 8012,
    "decision_engine": 8013,
    "investigation_agent": 8014,
}


def _base(name: str) -> str:
    return os.getenv(f"VERIPAY_{name.upper()}_URL", f"http://localhost:{SERVICES[name]}")


def _post(name: str, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    url = f"{_base(name)}{path}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Generous timeout: the first ML score cold-loads xgboost + the model
        # artifact (several seconds), and the demo should not race it.
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"  ! {name} unavailable ({exc}); start it with `make up` and retry.")
        return None


def _print_stage(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body)


def _transaction(amount_minor: int, transaction_id: str, user_id: str = "u_100") -> dict[str, Any]:
    return {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "amount_minor": amount_minor,
        "currency": "USD",
        "merchant_id": "m_amazon",
        "channel": "CARD_NOT_PRESENT",
        "payment_rail": "CARD",
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

LOW_RISK_FEATURES: dict[str, float] = {
    "amount_log": 6.0,
    "mcc_risk": 0.1,
    "velocity_5m": 1.0,
    "device_trust": 1.0,
    "network_trust": 1.0,
    "impossible_travel": 0.0,
    "new_device": 0.0,
    "hour_of_day": 14.0,
    "weekend": 0.0,
    "distance_km": 3.0,
}


def main() -> int:
    print("VeriPay end-to-end demo")
    print("=" * 60)

    # 1. Ingress: authorize two transactions
    for label, tx in (
        ("high-risk", _transaction(499_900, "tx_demo_high")),
        ("clean", _transaction(4_999, "tx_demo_clean")),
    ):
        response = _post("ingress", "/api/v1/transactions", tx)
        if response is not None:
            _print_stage(
                f"Ingress authorization ({label})",
                json.dumps(response, indent=2, sort_keys=True),
            )

    # 2. Deterministic rules
    rules = _post(
        "rule_engine",
        "/api/v1/rules/evaluate",
        {
            "dcvv_match": True,
            "merchant_allowed": True,
            "velocity_count_5m": 14,
            "impossible_travel": True,
            "device_trusted": False,
            "network_trusted": False,
        },
    )
    if rules is not None:
        triggered = [f["code"] for f in rules["findings"] if f["triggered"]]
        _print_stage(
            "Rule engine (hard rules)",
            f"triggered={rules['triggered']} findings={triggered}",
        )

    # 3. ML model scores (supervised + anomaly) on the same features
    supervised = _post(
        "supervised_model",
        "/api/v1/score",
        {"transaction_id": "tx_demo_high", "features": HIGH_RISK_FEATURES},
    )
    if supervised is not None:
        _print_stage(
            "Supervised model (XGBoost)",
            "fraud_probability="
            f"{supervised['fraud_probability']} risk_score={supervised['risk_score']} "
            f"model={supervised['model_name']}@{supervised['model_version']}",
        )
    anomaly = _post(
        "anomaly_model",
        "/api/v1/score",
        {"transaction_id": "tx_demo_high", "features": HIGH_RISK_FEATURES},
    )
    if anomaly is not None:
        _print_stage(
            "Anomaly model (Isolation Forest)",
            f"anomaly_score={anomaly['anomaly_score']} is_anomaly={anomaly['is_anomaly']} "
            f"risk_score={anomaly['risk_score']}",
        )

    # 4. Risk fusion -> unified 0-100 score
    components = [
        {"component": "rules", "score": 60, "weight": 0.25, "available": True},
        {
            "component": "supervised",
            "score": 21,
            "weight": 0.30,
            "available": supervised is not None,
        },
        {"component": "anomaly", "score": 54, "weight": 0.25, "available": anomaly is not None},
        {"component": "device_integrity", "score": 50, "weight": 0.20, "available": True},
    ]
    fusion = _post(
        "risk_fusion",
        "/api/v1/risk/fuse",
        {"transaction_id": "tx_demo_high", "components": components},
    )
    if fusion is not None:
        _print_stage(
            "Risk fusion (unified score)",
            f"score={fusion['unified_score']} band={fusion['band']} tier={fusion['tier']}",
        )

    # 5. Cost-aware decision
    decision = _post(
        "decision_engine",
        "/api/v1/decision/evaluate",
        {
            "transaction_id": "tx_demo_high",
            "risk_score": fusion["unified_score"] if fusion else 42,
            "payment_rail": "CARD",
        },
    )
    if decision is not None:
        _print_stage(
            "Decision engine (cost-aware)",
            f"action={decision['action']} reason={decision['reason_code']} "
            f"expected_cost={decision['expected_cost_minor']} workflow={decision['workflow']}",
        )

    # 6. LLM investigation agent explanation
    investigation = _post(
        "investigation_agent",
        "/api/v1/investigate",
        {
            "transaction_id": "tx_demo_high",
            "transaction": {"amount_minor": 499900, "merchant_id": "m_amazon"},
            "transaction_history": [],
            "risk_score": fusion["unified_score"] if fusion else 42,
            "macro_context": {"country": "US"},
        },
    )
    if investigation is not None:
        _print_stage(
            "LLM investigation agent",
            f"summary: {investigation['summary']}\n"
            f"reason_codes={investigation['regulatory_reason_codes']}\n"
            f"model={investigation['model_name']} prompt={investigation['prompt_version']}",
        )

    print("\nDemo complete. Next: open the web dashboard (`cd web && npm run dev`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
