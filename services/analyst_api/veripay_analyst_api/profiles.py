"""Customer profile store (baseline, recent behavior, drift, trust).

A deterministic in-memory adapter, consistent with the repository convention of
injectable repository/provider boundaries until the populated database schema
is wired. It backs ``/customer/{cc_num}/profile`` and the live drift/feedback
adjustments applied at scoring time.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from veripay_analyst_api.adjustments import is_benign, is_confirmed_fraud
from veripay_analyst_api.models import Decision, GeoPoint

_SUDDEN_DISTANCE_KM = 250.0
_SUDDEN_TIME_MINUTES = 15.0
_GRADUAL_LOCATION_KM = 100.0


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance in kilometres between two points."""
    import math

    lat1, lon1, lat2, lon2 = map(math.radians, [a.lat, a.lon, b.lat, b.lon])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


@dataclass(frozen=True)
class StoredTransaction:
    transaction_id: str
    cc_num: int
    amount: float
    merchant: str
    category: str
    timestamp: datetime
    location: GeoPoint | None
    merchant_location: GeoPoint | None
    decision: Decision | str


@dataclass
class StoredFeedback:
    transaction_id: str
    cc_num: int
    analyst_decision: str
    decision: Decision
    notes: str
    timestamp: datetime


@dataclass
class BaselineMetrics:
    median_amount: float = 0.0
    mean_amount: float = 0.0
    amount_std: float = 0.0
    hour_low: int = 0  # 25th percentile hour (0-23)
    hour_high: int = 23  # 75th percentile hour (0-23)
    hour_mode: int = -1  # most common hour (0-23); -1 when none
    distinct_merchants: int = 0
    daily_txn_count: float = 0.0
    count: int = 0


@dataclass
class DriftReport:
    kind: str  # "gradual" | "sudden"
    severity: str  # "yellow" | "red"
    message: str


@dataclass
class TrustStatus:
    level: str  # "normal" | "boosted" | "alert"
    message: str


class ProfileStore:
    """In-memory per-customer transaction + feedback accumulation."""

    def __init__(self) -> None:
        self._transactions: dict[int, list[StoredTransaction]] = {}
        self._feedback: list[StoredFeedback] = []
        self._customer_by_tx: dict[str, int] = {}

    # ---- transactions ---------------------------------------------------
    def add_transaction(self, tx: StoredTransaction) -> None:
        self._transactions.setdefault(tx.cc_num, []).append(tx)
        self._customer_by_tx[tx.transaction_id] = tx.cc_num

    def history(self, customer: int) -> list[StoredTransaction]:
        return sorted(self._transactions.get(customer, []), key=lambda t: t.timestamp)

    def recent(self, customer: int, days: int) -> list[StoredTransaction]:
        from datetime import timedelta

        history = self.history(customer)
        if not history:
            return []
        cutoff = history[-1].timestamp - timedelta(days=days)
        return [tx for tx in history if tx.timestamp >= cutoff]

    def metrics(self, transactions: list[StoredTransaction]) -> BaselineMetrics:
        """Summarise a set of transactions into a behavioural baseline."""
        import statistics

        if not transactions:
            return BaselineMetrics()
        amounts = [float(tx.amount) for tx in transactions]
        hours = [int(tx.timestamp.hour) for tx in transactions]
        days = {tx.timestamp.date() for tx in transactions}
        distinct = {tx.merchant for tx in transactions}
        if hours:
            hour_counts = Counter(hours)
            hour_mode = hour_counts.most_common(1)[0][0]
        else:
            hour_mode = -1
        return BaselineMetrics(
            median_amount=statistics.median(amounts),
            mean_amount=statistics.mean(amounts),
            amount_std=statistics.stdev(amounts) if len(amounts) >= 2 else 0.0,
            hour_low=max(0, min(23, int(statistics.quantiles(hours, n=4)[0])))
            if len(hours) >= 4
            else (min(hours) if hours else 0),
            hour_high=max(0, min(23, int(statistics.quantiles(hours, n=4)[1])))
            if len(hours) >= 4
            else (max(hours) if hours else 23),
            hour_mode=hour_mode,
            distinct_merchants=len(distinct),
            daily_txn_count=round(len(transactions) / max(1, len(days)), 2),
            count=len(transactions),
        )

    # ---- feedback -------------------------------------------------------
    def record_feedback(self, feedback: StoredFeedback) -> None:
        self._feedback.append(feedback)

    def feedback_for_customer(self, customer: int) -> list[str]:
        # Records are appended chronologically; preserving append order keeps
        # them oldest → newest for this customer.
        return [fb.analyst_decision for fb in self._feedback if fb.cc_num == customer]

    def recent_benign(self, customer: int, window: int = 3) -> bool:
        labels = self.feedback_for_customer(customer)
        return len(labels) >= window and all(is_benign(label) for label in labels[-window:])

    def has_confirmed_fraud(self, customer: int) -> bool:
        return any(is_confirmed_fraud(label) for label in self.feedback_for_customer(customer))

    def all_feedback(self) -> list[StoredFeedback]:
        return list(self._feedback)

    def customer_for_transaction(self, transaction_id: str) -> int | None:
        return self._customer_by_tx.get(transaction_id)

    # ---- drift + trust --------------------------------------------------
    def detect_drift(self, customer: int) -> DriftReport | None:
        """Compare recent (30d) behaviour against the long-term (90d) baseline."""
        history = self.history(customer)
        if len(history) < 5:
            return None
        recent = self.recent(customer, 30)
        long_term = [tx for tx in history if (history[-1].timestamp - tx.timestamp).days <= 90]

        # Sudden: two consecutive transactions within minutes but kilometres apart.
        for prev, curr in zip(recent, recent[1:], strict=False):
            if _minutes_between(prev, curr) > _SUDDEN_TIME_MINUTES:
                continue
            prev_point = _point(prev)
            curr_point = _point(curr)
            if prev_point is None or curr_point is None:
                continue
            distance = haversine_km(prev_point, curr_point)
            if distance >= _SUDDEN_DISTANCE_KM:
                severity = "red" if distance >= 1000.0 else "yellow"
                return DriftReport(
                    kind="sudden",
                    severity=severity,
                    message=(
                        f"Location jumped {distance:.0f} km in under "
                        f"{int(_SUDDEN_TIME_MINUTES)} minutes."
                    ),
                )

        reset_metrics = self.metrics(recent)
        baseline_metrics = self.metrics(long_term)
        if reset_metrics.count >= 5 and baseline_metrics.count >= 5:
            reasons: list[str] = []
            if (
                baseline_metrics.median_amount
                and not 0.5 <= reset_metrics.median_amount / baseline_metrics.median_amount <= 2.0
            ):
                reasons.append("spending level changed")
            recent_center = _centroid(recent)
            long_center = _centroid(long_term)
            if (
                recent_center is not None
                and long_center is not None
                and haversine_km(recent_center, long_center) >= _GRADUAL_LOCATION_KM
            ):
                reasons.append("active area relocated")
            if reasons:
                return DriftReport(
                    kind="gradual",
                    severity="yellow",
                    message="Gradual drift: " + "; ".join(reasons) + " from long-term baseline.",
                )
        return None

    def trust_status(self, customer: int, window: int = 3) -> TrustStatus:
        if self.has_confirmed_fraud(customer):
            return TrustStatus("alert", "Confirmed fraud on this account; alerts are heightened.")
        if self.recent_benign(customer, window):
            return TrustStatus(
                "boosted", "Recent false alarms confirmed as legitimate; trust boosted."
            )
        return TrustStatus("normal", "No recent feedback; normal trust level.")


def _minutes_between(a: StoredTransaction, b: StoredTransaction) -> float:
    return (b.timestamp - a.timestamp).total_seconds() / 60.0


def _point(tx: StoredTransaction) -> GeoPoint | None:
    return tx.location or tx.merchant_location


def _centroid(transactions: list[StoredTransaction]) -> GeoPoint | None:
    points = [p for tx in transactions if (p := _point(tx)) is not None]
    if not points:
        return None
    return GeoPoint(
        lat=sum(p.lat for p in points) / len(points),
        lon=sum(p.lon for p in points) / len(points),
    )


__all__ = [
    "BaselineMetrics",
    "DriftReport",
    "ProfileStore",
    "StoredFeedback",
    "StoredTransaction",
    "TrustStatus",
    "haversine_km",
]
