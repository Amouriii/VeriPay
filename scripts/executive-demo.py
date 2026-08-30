"""Board-ready VeriPay demo runner.

Offline mode is deterministic and requires no services. Live mode reuses the
Analyst API when it is available and reports unavailable optional stages.

Examples:
    python scripts/executive-demo.py --offline
    python scripts/executive-demo.py --live
    python scripts/executive-demo.py --offline --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    name: str
    area: str
    outcome: str
    evidence: str
    endpoint: str | None = None


OFFLINE_SCENARIOS = [
    Scenario(
        "clean_approval",
        "trust",
        "PASS",
        "Trusted device, known merchant, normal amount and velocity.",
    ),
    Scenario(
        "card_testing",
        "trust",
        "BLOCK",
        "96.8% fraud probability; 6 transactions/hour; 12.4x baseline; shared-fraud merchant.",
    ),
    Scenario(
        "stealth_fraud",
        "trust",
        "REVIEW_STEALTH",
        (
            "High fraud likelihood with low anomaly signal; route to human review "
            "and biometric verification."
        ),
    ),
    Scenario(
        "network_ring",
        "platform",
        "NETWORK RISK",
        "Graph axis identifies flagged neighbors and a 50% confirmed-fraud community.",
    ),
    Scenario(
        "customer_verification",
        "trust",
        "CUSTOMER SAFE",
        "Push/biometric verification gives the customer a low-friction recovery path.",
    ),
    Scenario(
        "fi_ops_controls",
        "operations",
        "AUDITABLE",
        "FI Ops covers transactions, disputes, regulatory reporting, and immutable audit history.",
    ),
    Scenario(
        "business_treasury",
        "operations",
        "CONTROLLED SPEND",
        "Business policy, merchant limits, VCN controls, webhooks, and dispute transitions.",
    ),
    Scenario(
        "resilience",
        "platform",
        "DEGRADED SAFE",
        "Unavailable graph/model signals are marked unavailable and fusion redistributes weight.",
    ),
    Scenario(
        "feedback_learning",
        "platform",
        "GOVERNED LEARNING",
        "Analyst labels adjust live scoring and feed monitoring/retraining gates.",
    ),
]


def _get(url: str, path: str) -> dict[str, Any] | list[Any] | None:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}{path}", timeout=5) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def _post(url: str, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    request = urllib.request.Request(
        f"{url.rstrip('/')}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            value = json.loads(response.read().decode())
            return value if isinstance(value, dict) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def run_live(base: str) -> list[dict[str, Any]]:
    """Exercise the live analyst boundary, while keeping optional failures visible."""
    result: list[dict[str, Any]] = []
    health = _get(base, "/health")
    result.append(
        {
            "name": "analyst_api_health",
            "area": "platform",
            "outcome": "ONLINE" if health else "UNAVAILABLE",
            "evidence": health or "Start analyst_api on port 8026.",
        }
    )
    alerts = _get(base, "/alerts")
    result.append(
        {
            "name": "alert_queue",
            "area": "trust",
            "outcome": f"{len(alerts)} ALERTS" if isinstance(alerts, list) else "UNAVAILABLE",
            "evidence": (
                alerts[:2]
                if isinstance(alerts, list)
                else "Seed the queue with make seed-analyst."
            ),
        }
    )
    score = _post(base, "/score", {"transaction_id": "tx_9001"})
    result.append(
        {
            "name": "card_testing",
            "area": "trust",
            "outcome": score.get("decision", "UNAVAILABLE") if score else "UNAVAILABLE",
            "evidence": score or "Seeded transaction tx_9001 not found.",
        }
    )
    profile = _get(base, "/customer/4716561796955522/profile")
    result.append(
        {
            "name": "customer_context",
            "area": "trust",
            "outcome": "PROFILE READY" if profile else "UNAVAILABLE",
            "evidence": profile or "Profile unavailable.",
        }
    )
    stats = _get(base, "/feedback/stats")
    result.append(
        {
            "name": "feedback_learning",
            "area": "platform",
            "outcome": "MEASURED" if stats else "UNAVAILABLE",
            "evidence": stats or "Feedback stats unavailable.",
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic fixtures; default mode.",
    )
    mode.add_argument("--live", action="store_true", help="Call the live Analyst API.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--api",
        default=os.getenv("VERIPAY_ANALYST_API_URL", "http://localhost:8026"),
        help="Analyst API base URL for --live.",
    )
    args = parser.parse_args(argv)
    live = args.live
    rows = run_live(args.api) if live else [asdict(item) for item in OFFLINE_SCENARIOS]
    payload = {
        "mode": "live" if live else "offline",
        "api": args.api if live else None,
        "scenarios": rows,
        "coverage": {"trust": 0, "operations": 0, "platform": 0},
    }
    for row in rows:
        if row["area"] in payload["coverage"]:
            payload["coverage"][row["area"]] += 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("VeriPay executive board demo — " + payload["mode"])
        print("=" * 62)
        for row in rows:
            evidence = row["evidence"]
            if not isinstance(evidence, str):
                evidence = json.dumps(evidence, separators=(",", ":"))
            print(f"[{row['area'].upper():10}] {row['name']:<24} {row['outcome']}")
            print(f"             {evidence[:180]}")
        coverage = ", ".join(
            f"{key}={value}" for key, value in payload["coverage"].items()
        )
        print("\nCoverage: " + coverage)
        if live and not any(row["outcome"] != "UNAVAILABLE" for row in rows):
            print(
                "\nNo live stages responded. Start the stack with `make up`, "
                "then `make seed-analyst`."
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
