"""Seed the analyst console alert queue through the live ``analyst_api`` service.

Scores a realistic, deterministic batch of transactions via ``POST /score`` so
the dashboard's alert queue, scored-transaction lookups, and customer profiles
have data immediately after ``docker compose up`` (the ``seed_analyst``
one-shot service runs this). Each customer gets a short benign history first —
so the rich causal feature engine has velocity/amount/geo baselines — followed
by one or two target transactions spanning the decision vocabulary (PASS,
REVIEW_UNUSUAL, REVIEW_STEALTH, BLOCK).

The exact decisions depend on the deployed supervised/anomaly artifacts (or
their deterministic fallbacks), so the script prints the resulting decision
distribution and the alert queue rather than asserting specific outcomes.

Scaling flags (for larger demo queues):

    python scripts/seed-analyst-queue.py --variants 3 --count 20

``--variants`` repeats the curated scenario set (each with offset customer
numbers, jittered amounts, and shifted timestamps); ``--count`` adds extra
synthetic customers with per-customer merchant/amount variation beyond the
curated ones. All variation is deterministic (seeded per customer/variant).

Run:

    python scripts/seed-analyst-queue.py           # against localhost:8026
    docker compose run --rm seed_analyst           # re-seed the live stack
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

DEFAULT_BASE = "http://localhost:8026"
EXPLAIN_LIMIT = 3  # best-effort /explain calls for the top alerts
BASE_CUSTOMERS = 7  # curated scenarios; --count extends beyond this

# New York home base (lat/lon) shared by the demo customers.
_NY = {"lat": 40.7128, "lon": -74.006}
_LA = {"lat": 34.0522, "lon": -118.2437}
_LONDON = {"lat": 51.5074, "lon": -0.1278}


def _base() -> str:
    return os.getenv("VERIPAY_ANALYST_API_URL", DEFAULT_BASE).rstrip("/")


def _request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    url = f"{_base()}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"  ! analyst_api unavailable ({exc}); is the stack up?", file=sys.stderr)
        return None


def _transaction(
    transaction_id: str,
    cc_num: int,
    amount: float,
    merchant: str,
    category: str,
    timestamp: datetime,
    *,
    location: dict[str, float] | None = None,
    merchant_location: dict[str, float] | None = None,
    mcc_risk: float = 0.3,
    device_trust: float = 1.0,
    network_trust: float = 1.0,
    new_device: float = 0.0,
    impossible_travel: float = 0.0,
) -> dict[str, Any]:
    return {
        "transaction_id": transaction_id,
        "cc_num": cc_num,
        "amount": round(amount, 2),
        "merchant": merchant,
        "category": category,
        "timestamp": timestamp.isoformat(),
        "location": location or _NY,
        "merchant_location": merchant_location,
        "mcc_risk": mcc_risk,
        "device_trust": device_trust,
        "network_trust": network_trust,
        "new_device": new_device,
        "impossible_travel": impossible_travel,
    }


def _history(
    customer: int,
    base: datetime,
    *,
    amounts: tuple[float, ...] = (32.5, 58.0, 24.75, 91.0),
    location: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """A short benign history so the causal engine has real baselines.

    Merchants are unique per customer (``m{cc}_...``) so the graph axis does
    not connect unrelated customers through shared merchant nodes — otherwise
    every benign history row inherits network risk and floods the queue.
    """
    prefix = f"m{customer}"
    merchants = (f"{prefix}_grocery", f"{prefix}_coffee", f"{prefix}_pharmacy", f"{prefix}_online")
    rows: list[dict[str, Any]] = []
    for i, amount in enumerate(amounts):
        rows.append(
            _transaction(
                f"seed_h_{customer}_{i}",
                customer,
                amount,
                merchants[i % len(merchants)],
                "retail" if i < 3 else "ecommerce",
                base - timedelta(days=9 - i * 2, hours=1),
                location=location,
                merchant_location=location if i < 3 else None,
            )
        )
    return rows


def _scenarios(
    now: datetime,
    *,
    offset: int = 0,
    amount_scale: float = 1.0,
    day_offset: int = 0,
) -> list[tuple[int, list[dict[str, Any]]]]:
    """Curated per-customer scenarios: (cc_num, [transactions in order]).

    ``offset`` shifts customer numbers, ``amount_scale`` jitters amounts, and
    ``day_offset`` shifts timestamps so repeated ``--variants`` stay
    deterministic but distinct (and never share merchants across variants).
    """
    ts = now + timedelta(days=day_offset)

    def cc(base: int) -> int:
        return base + offset

    def scaled(amounts: tuple[float, ...]) -> tuple[float, ...]:
        return tuple(round(a * amount_scale, 2) for a in amounts)

    return [
        # Ordinary customer; all targets should pass.
        (
            cc(1001),
            _history(cc(1001), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1001)}_ok",
                    cc(1001),
                    round(45.0 * amount_scale, 2),
                    f"m{cc(1001)}_wholefoods",
                    "retail",
                    ts,
                ),
                _transaction(
                    f"seed_{cc(1001)}_ok2",
                    cc(1001),
                    round(120.0 * amount_scale, 2),
                    f"m{cc(1001)}_online",
                    "ecommerce",
                    ts - timedelta(hours=2),
                ),
            ],
        ),
        # Card-testing burst: rapid small charges, fresh device, 3am.
        (
            cc(1002),
            _history(cc(1002), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1002)}_burst1",
                    cc(1002),
                    round(12.99 * amount_scale, 2),
                    f"m{cc(1002)}_test1",
                    "ecommerce",
                    ts - timedelta(minutes=4),
                    mcc_risk=0.7,
                    device_trust=0.0,
                    network_trust=0.0,
                    new_device=1.0,
                ),
                _transaction(
                    f"seed_{cc(1002)}_burst2",
                    cc(1002),
                    round(27.5 * amount_scale, 2),
                    f"m{cc(1002)}_test2",
                    "ecommerce",
                    ts - timedelta(minutes=2),
                    mcc_risk=0.7,
                    device_trust=0.0,
                    network_trust=0.0,
                    new_device=1.0,
                ),
                _transaction(
                    f"seed_{cc(1002)}_burst3",
                    cc(1002),
                    round(89.0 * amount_scale, 2),
                    f"m{cc(1002)}_test3",
                    "ecommerce",
                    ts,
                    mcc_risk=0.7,
                    device_trust=0.0,
                    network_trust=0.0,
                    new_device=1.0,
                ),
            ],
        ),
        # Large legitimate purchase (furniture, trusted device, day).
        (
            cc(1003),
            _history(cc(1003), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1003)}_large",
                    cc(1003),
                    round(1850.0 * amount_scale, 2),
                    f"m{cc(1003)}_furniture",
                    "retail",
                    ts,
                    merchant_location=_NY,
                    mcc_risk=0.25,
                )
            ],
        ),
        # Account takeover: big foreign purchase, new device, impossible travel.
        (
            cc(1004),
            _history(cc(1004), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1004)}_ato",
                    cc(1004),
                    round(5300.0 * amount_scale, 2),
                    f"m{cc(1004)}_luxury",
                    "ecommerce",
                    ts,
                    merchant_location=_LONDON,
                    mcc_risk=0.85,
                    device_trust=0.0,
                    network_trust=0.0,
                    new_device=1.0,
                    impossible_travel=1.0,
                )
            ],
        ),
        # Repeated gift-card attempts on a new device (may fall under the fraud
        # threshold — a realistic "attempted but missed" outcome).
        (
            cc(1005),
            _history(cc(1005), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1005)}_cards1",
                    cc(1005),
                    round(210.0 * amount_scale, 2),
                    f"m{cc(1005)}_giftcards",
                    "ecommerce",
                    ts - timedelta(minutes=6),
                    mcc_risk=0.6,
                    new_device=1.0,
                ),
                _transaction(
                    f"seed_{cc(1005)}_cards2",
                    cc(1005),
                    round(210.0 * amount_scale, 2),
                    f"m{cc(1005)}_giftcards",
                    "ecommerce",
                    ts,
                    mcc_risk=0.6,
                    new_device=1.0,
                ),
            ],
        ),
        # Unusual but benign: first-ever purchase at a new merchant at night.
        (
            cc(1006),
            _history(cc(1006), ts, amounts=scaled((32.5, 58.0, 24.75, 91.0)))
            + [
                _transaction(
                    f"seed_{cc(1006)}_unusual",
                    cc(1006),
                    round(340.0 * amount_scale, 2),
                    f"m{cc(1006)}_new",
                    "services",
                    ts.replace(hour=2, minute=15),
                    merchant_location=_NY,
                    mcc_risk=0.5,
                    device_trust=-1.0,
                    network_trust=-1.0,
                )
            ],
        ),
        # Stealth (architecture §6): LA history, then a large NY purchase on a
        # trusted device with no impossible travel. Matches known-fraud patterns
        # (fraud probability high from the ~3,900 km distance) while the anomaly
        # axis sees a normal profile → REVIEW_STEALTH, not BLOCK.
        (
            cc(1007),
            [
                _transaction(
                    f"seed_la_{cc(1007)}_{i}",
                    cc(1007),
                    amount,
                    f"m{cc(1007)}_la_shop",
                    "retail",
                    ts - timedelta(days=10 - i),
                    location=_LA,
                    merchant_location=_LA,
                )
                for i, amount in enumerate(scaled((40.0, 55.0, 30.0, 66.0)))
            ]
            + [
                _transaction(
                    f"seed_{cc(1007)}_stealth",
                    cc(1007),
                    round(420.0 * amount_scale, 2),
                    f"m{cc(1007)}_ny_shop",
                    "retail",
                    ts,
                    merchant_location=_NY,
                )
            ],
        ),
    ]


def _extra_customers(
    now: datetime,
    count: int,
    *,
    offset: int = 0,
) -> list[tuple[int, list[dict[str, Any]]]]:
    """Synthetic customers with per-customer merchant/amount variation.

    Each extra customer gets a seeded random history (unique amounts and
    merchants) plus a normal target and, ~half the time, a suspicious
    second target — so larger ``--count`` batches widen the queue without
    repeating the curated shapes exactly.
    """
    customers: list[tuple[int, list[dict[str, Any]]]] = []
    for i in range(count):
        customer = 6000 + offset + i
        rng = random.Random(customer)
        amounts = tuple(round(rng.uniform(15.0, 140.0), 2) for _ in range(4))
        history = _history(customer, now, amounts=amounts)
        targets = [
            _transaction(
                f"seed_{customer}_ok",
                customer,
                round(rng.uniform(25.0, 200.0), 2),
                f"m{customer}_shop",
                "retail",
                now,
                merchant_location=_NY,
                mcc_risk=round(rng.uniform(0.1, 0.4), 2),
            )
        ]
        if rng.random() < 0.5:
            targets.append(
                _transaction(
                    f"seed_{customer}_susp",
                    customer,
                    round(rng.uniform(200.0, 900.0), 2),
                    f"m{customer}_web",
                    "ecommerce",
                    now - timedelta(minutes=5),
                    mcc_risk=round(rng.uniform(0.4, 0.7), 2),
                    device_trust=-1.0,
                    network_trust=-1.0,
                    new_device=1.0,
                )
            )
        customers.append((customer, history + targets))
    return customers


def _print_score(
    row: dict[str, Any],
    explain: dict[str, Any] | None = None,
    tx: dict[str, Any] | None = None,
) -> None:
    decision = row.get("decision", "?")
    risk = row.get("risk_level", "?")
    fraud = row.get("fraud_probability", 0.0)
    anomaly = row.get("anomaly_score", 0.0)
    amount = tx.get("amount", 0.0) if tx else 0.0
    merchant = tx.get("merchant", "") if tx else ""
    print(
        f"  {row['transaction_id']:<20} {decision:<15} {risk:<9} "
        f"fraud={fraud:.3f} anomaly={anomaly:.3f} "
        f"${amount:>10,.2f} {merchant}"
    )
    if explain is not None:
        report = explain.get("case_report", {})
        print(f"    → {report.get('verdict', '')} | {report.get('pattern_match', '')}")


def _build_batch(
    now: datetime, *, count: int, variants: int
) -> list[tuple[int, list[dict[str, Any]]]]:
    """Compose the full batch from curated scenarios + scaling flags."""
    batch: list[tuple[int, list[dict[str, Any]]]] = []
    for variant in range(variants):
        offset = variant * 10_000
        # Variant 0 keeps the exact curated amounts; later variants jitter
        # deterministically so repeated sets stay distinct.
        rng = random.Random(variant)
        amount_scale = 1.0 if variant == 0 else round(rng.uniform(0.85, 1.25), 3)
        batch.extend(_scenarios(now, offset=offset, amount_scale=amount_scale, day_offset=variant))
        batch.extend(_extra_customers(now, max(0, count - BASE_CUSTOMERS), offset=offset))
    return batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the analyst console alert queue.")
    parser.add_argument(
        "--count",
        type=int,
        default=BASE_CUSTOMERS,
        help=f"total customers to seed (default {BASE_CUSTOMERS}); extra customers "
        "get synthetic per-customer merchant/amount variation",
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=1,
        help="repeat the curated scenario set this many times with jittered "
        "amounts, offset customer numbers, and shifted timestamps (default 1)",
    )
    args = parser.parse_args()

    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    batch = _build_batch(now, count=args.count, variants=args.variants)
    print(f"Seeding analyst console via {_base()} (FEATURE_MODE drives the engine)")
    print(f"Batch: {len(batch)} customers, {sum(len(t) for _, t in batch)} transactions\n")

    totals: dict[str, int] = {}
    alerts: list[tuple[dict[str, Any], dict[str, Any]]] = []
    explain_candidates: list[dict[str, Any]] = []

    for _customer, transactions in batch:
        for tx in transactions:
            response = _request("POST", "/score", {"transaction": tx})
            if response is None:
                return 1
            decision = str(response.get("decision", "?"))
            totals[decision] = totals.get(decision, 0) + 1
            if decision != "PASS":
                alerts.append((tx, response))
            if decision != "PASS" and len(explain_candidates) < EXPLAIN_LIMIT:
                explain_candidates.append(tx)

    # Best-effort explanations for the top flagged transactions (console detail).
    explains: dict[str, dict[str, Any]] = {}
    for tx in explain_candidates:
        explain = _request("POST", "/explain", {"transaction": tx})
        if explain is not None:
            explains[str(tx["transaction_id"])] = explain

    print("Scored transactions by decision:")
    for decision in ("PASS", "REVIEW_UNUSUAL", "REVIEW_STEALTH", "BLOCK"):
        print(f"  {decision:<15} {totals.get(decision, 0)}")
    print(f"\nAlert queue ({len(alerts)} non-PASS transactions):")
    for tx, row in sorted(
        alerts,
        key=lambda pair: pair[1].get("fraud_probability", 0) + pair[1].get("anomaly_score", 0),
        reverse=True,
    ):
        _print_score(row, explains.get(str(row["transaction_id"])), tx)

    queue = _request("GET", "/alerts")
    print(f"\n/alerts returns {len(queue) if queue else 0} entries (sorted most suspicious first).")

    print(
        "\nDone. Open the analyst console (`cd web && npm run dev`) — the alert "
        "queue is populated. Re-seed with `docker compose run --rm seed_analyst`."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
