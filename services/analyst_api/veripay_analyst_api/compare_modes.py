"""Head-to-head comparison of the *basic* vs *rich* feature engines.

Both modes are derived from the same transaction + causal history and collapse
onto the same ``FEATURE_COLUMNS`` model vector. A head-to-head on decisions is
therefore primarily a check of **model-input equivalence**: the two engines are
designed to feed identical vectors to the supervised/anomaly models, so a
decision-level metric (FPR / fraud-catch / decision divergence) is expected —
and defended — to be unchanged when rich mode is enabled.

This module generates deterministic seeded customer timelines, derives both
vectors and both deterministic reference risks, and measures, at a fixed
threshold: decision divergence (how often the two modes disagree), the
false-positive rate, and the fraud-catch rate for each mode.

The consequence for the dashboard default: because the two engines are
decision-equivalent, the default should be chosen on operational grounds
(``basic`` = no merchant/category/coordinates or long history required; cheaper
and robust to sparse data), while ``rich`` remains an explainability opt-in
that surfaces the full 16-feature table. We only recommend flipping the default
if this run shows material divergence the basic engine fails to capture.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from veripay_analyst_api.features import build_features
from veripay_analyst_api.features16 import compute_features16, map_to_model
from veripay_analyst_api.models import Decision, GeoPoint, TransactionInput
from veripay_analyst_api.profiles import ProfileStore, StoredTransaction

_THRESHOLD = 50

# Deterministic reference risk over the shared model columns. Mirrors the
# heuristic fallback the deployed supervised service uses, so the comparison is
# referee-independent of any single ML artifact.
_REFERENCE_WEIGHTS: dict[str, float] = {
    "amount_log": 2.0,
    "mcc_risk": 30.0,
    "velocity_5m": 2.0,
    "impossible_travel": 20.0,
    "new_device": 15.0,
    "hour_of_day": 0.4,
    "weekend": 3.0,
    "distance_km": 0.01,
}
_TRUST_RISK: dict[str, tuple[float, float]] = {
    "device_trust": (12.0, 4.0),
    "network_trust": (10.0, 3.0),
}

_MODERATE_MCC = 0.35
_HOME_BASE = GeoPoint(lat=40.7, lon=-74.0)


@dataclass
class TimelineRow:
    transaction_id: str
    is_fraud: bool
    basic_risk: int
    rich_risk: int
    vectors_equal: bool


@dataclass
class Comparison:
    total: int
    fraud: int
    basic_false_positive: int
    rich_false_positive: int
    basic_fraud_flagged: int
    rich_fraud_flagged: int
    decisions_differ: int
    vectors_identical: bool
    vector_mismatches: int

    @property
    def basic_fpr(self) -> float:
        legit = self.total - self.fraud
        return self.basic_false_positive / legit if legit else 0.0

    @property
    def rich_fpr(self) -> float:
        legit = self.total - self.fraud
        return self.rich_false_positive / legit if legit else 0.0

    @property
    def basic_catch(self) -> float:
        return self.basic_fraud_flagged / self.fraud if self.fraud else 0.0

    @property
    def rich_catch(self) -> float:
        return self.rich_fraud_flagged / self.fraud if self.fraud else 0.0


def reference_risk(features: dict[str, float]) -> int:
    """Deterministic 0-100 risk derived from the shared model columns."""
    total = 0.0
    for column, weight in _REFERENCE_WEIGHTS.items():
        total += float(features.get(column, 0.0)) * weight
    for column, (untrusted, unknown) in _TRUST_RISK.items():
        value = float(features.get(column, -1.0))
        if value == 0.0:
            total += untrusted
        elif value < 0.0:
            total += unknown
    return max(0, min(100, int(round(total))))


def _point(transaction: TransactionInput) -> GeoPoint | None:
    return transaction.location or transaction.merchant_location


def _ko(_: str) -> Decision:
    return Decision.PASS


def generate_timelines(n_customers: int = 120, seed: int = 7) -> list[TimelineRow]:
    """Build deterministic per-customer timelines and score both feature modes."""
    rng = random.Random(seed)
    rows: list[TimelineRow] = []
    store = ProfileStore()
    base = datetime(2026, 1, 6, 12, 0, tzinfo=UTC)  # Tuesday noon

    for customer in range(n_customers):
        cc = 2000 + customer
        home = GeoPoint(lat=_HOME_BASE.lat + rng.uniform(-0.05, 0.05), lon=_HOME_BASE.lon)
        merchants = [f"m_{customer}_{i}" for i in range(5)]
        categories = [f"cat_{i % 3}" for i in range(5)]
        now = base + timedelta(days=customer)
        history: list[StoredTransaction] = []

        for txn_index in range(9):
            now += timedelta(minutes=rng.choice([8, 20, 45, 120, 400]))
            # A later large/foreign transaction is the usual fraud shape.
            spike = txn_index >= 6 and rng.random() < 0.5
            amount = 6000.0 if spike else rng.uniform(5.0, 220.0)
            merchant = (f"m_foreign_{customer}") if spike else rng.choice(merchants)
            category = rng.choice(categories)
            # A spike transaction lands far from a long-serving merchant; this
            # is the case rich mode's geographic/velocity features could, in
            # principle, encode more sharply.
            foreign_location = rng.random() < 0.5
            merchant_location = (
                GeoPoint(lat=51.5, lon=-0.1)
                if spike and foreign_location
                else GeoPoint(lat=home.lat, lon=home.lon)
            )
            new_device = spike
            impossible_travel = 1.0 if (spike and foreign_location) else 0.0
            transaction = TransactionInput(
                transaction_id=f"tx_{customer}_{txn_index}",
                cc_num=cc,
                amount=round(amount, 2),
                merchant=merchant,
                category=category,
                timestamp=now,
                location=home,
                merchant_location=merchant_location,
                mcc_risk=round(_MODERATE_MCC, 3),
                device_trust=-1.0 if rng.random() < 0.3 else 1.0,
                network_trust=-1.0 if rng.random() < 0.25 else 1.0,
                new_device=new_device,
                impossible_travel=impossible_travel,
            )
            metrics = store.metrics(history)
            basic = dict(build_features(transaction, history, metrics))
            rich_map = compute_features16(transaction, history, metrics)
            rich = map_to_model(rich_map, transaction, history)

            vectors_equal = basic == rich
            basic_risk = reference_risk(basic)
            rich_risk = reference_risk(rich)

            # Ground-truth label with mild noise so FPR/catch are informative.
            # Thresholds calibrated to the corrected amount_log scale (cents),
            # where the reference risk sits ~10 points higher than before.
            risk = basic_risk
            fraud = (risk >= 70 and rng.random() < 0.75) or (risk <= 28 and rng.random() < 0.03)

            rows.append(
                TimelineRow(
                    transaction_id=transaction.transaction_id,
                    is_fraud=fraud,
                    basic_risk=basic_risk,
                    rich_risk=rich_risk,
                    vectors_equal=vectors_equal,
                )
            )
            history.append(
                StoredTransaction(
                    transaction_id=transaction.transaction_id,
                    cc_num=cc,
                    amount=transaction.amount,
                    merchant=transaction.merchant,
                    category=transaction.category,
                    timestamp=transaction.timestamp,
                    location=_point(transaction),
                    merchant_location=merchant_location,
                    decision=_ko(transaction.merchant),
                )
            )
    return rows


def evaluate(rows: list[TimelineRow], threshold: int = _THRESHOLD) -> Comparison:
    """Measure FPR, fraud-catch and decision divergence at a risk threshold."""
    total = len(rows)
    fraud = sum(1 for row in rows if row.is_fraud)

    basic_false_positive = sum(
        1 for row in rows if not row.is_fraud and row.basic_risk >= threshold
    )
    rich_false_positive = sum(1 for row in rows if not row.is_fraud and row.rich_risk >= threshold)
    basic_fraud_flagged = sum(1 for row in rows if row.is_fraud and row.basic_risk >= threshold)
    rich_fraud_flagged = sum(1 for row in rows if row.is_fraud and row.rich_risk >= threshold)
    decisions_differ = sum(
        1 for row in rows if (row.basic_risk >= threshold) != (row.rich_risk >= threshold)
    )
    identical = all(row.vectors_equal for row in rows)
    mismatches = sum(1 for row in rows if not row.vectors_equal)
    return Comparison(
        total=total,
        fraud=fraud,
        basic_false_positive=basic_false_positive,
        rich_false_positive=rich_false_positive,
        basic_fraud_flagged=basic_fraud_flagged,
        rich_fraud_flagged=rich_fraud_flagged,
        decisions_differ=decisions_differ,
        vectors_identical=identical,
        vector_mismatches=mismatches,
    )


def run() -> Comparison:
    return evaluate(generate_timelines())


__all__ = [
    "Comparison",
    "TimelineRow",
    "evaluate",
    "generate_timelines",
    "reference_risk",
    "run",
]
