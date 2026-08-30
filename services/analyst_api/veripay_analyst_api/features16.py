"""Causal 16-feature engine (architecture section 3) mapped to the model vector.

Computes the full 16 causal-sequence features described in the architecture from
a transaction plus that customer's already-recorded history, then maps them onto
the ordered model feature matrix (``FEATURE_COLUMNS``) consumed by the
supervised and anomaly services.

Causality is guaranteed by construction: only transactions that occurred
strictly before the scored one are referenced when computing velocity, merchant
novelty, geography, and temporal gaps — exactly the ``_causal_window.py``
guarantee from the architecture. This module is only wired into the pipeline
when ``FEATURE_MODE=rich``.
"""

from __future__ import annotations

import math
from datetime import timedelta

from veripay_analyst_api.features import FEATURE_COLUMNS
from veripay_analyst_api.models import FeatureRow, GeoPoint, TransactionInput
from veripay_analyst_api.profiles import BaselineMetrics, StoredTransaction, haversine_km

FEATURES16: tuple[str, ...] = (
    # Velocity — how fast are transactions happening?
    "txn_count_1h",
    "txn_count_24h",
    "amt_sum_1h",
    "amt_sum_24h",
    # Amount — is this normal spending for this person?
    "amt_over_median_90d",
    "amt_zscore_90d",
    # Merchant novelty — has this customer been here before?
    "is_new_merchant",
    "is_new_category",
    "days_since_first_seen_merchant",
    # Geographic — where is this happening?
    "dist_from_home_km",
    "dist_from_prev_txn_km",
    "implied_velocity_kmh",
    # Temporal — when is this happening?
    "hour_of_day",
    "is_night",
    "hours_since_prev_txn",
    "hour_deviation_from_customer_mode",
)

_KMH_CAP = 9999.0
_ZSCORE_CLIP = 10.0


def compute_features16(
    transaction: TransactionInput,
    history: list[StoredTransaction],
    metrics: BaselineMetrics | None = None,
) -> dict[str, float]:
    """Compute the 16 causal features; ``history`` must not contain the txn."""
    prior = [tx for tx in history if tx.timestamp < transaction.timestamp]
    current_ts = transaction.timestamp
    amount = transaction.amount

    def count_within(delta: timedelta) -> int:
        return sum(1 for tx in prior if (current_ts - tx.timestamp) <= delta)

    def amount_within(delta: timedelta) -> float:
        return sum(float(tx.amount) for tx in prior if (current_ts - tx.timestamp) <= delta)

    baseline = metrics or BaselineMetrics()
    has_90d = baseline.count > 0
    median = baseline.median_amount if has_90d else 0.0
    mean = baseline.mean_amount if has_90d else 0.0
    std = baseline.amount_std if has_90d else 0.0
    zscore = ((amount - mean) / std) if std > 0 else 0.0
    zscore = max(-_ZSCORE_CLIP, min(_ZSCORE_CLIP, zscore))

    prior_merchants = {tx.merchant for tx in prior}
    prior_categories = {tx.category for tx in prior if tx.category}
    is_new_merchant = 1.0 if transaction.merchant not in prior_merchants else 0.0
    is_new_category = (
        1.0 if transaction.category and transaction.category not in prior_categories else 0.0
    )
    first_seen = next((tx for tx in prior if tx.merchant == transaction.merchant), None)
    days_since_first = (current_ts - first_seen.timestamp).days if first_seen else 0.0

    home = _centroid(prior)
    dist_home = _distance(home, transaction.merchant_location, transaction.location)

    previous = prior[-1] if prior else None
    prev_point = _point(previous) if previous else None
    current_point = transaction.location or transaction.merchant_location
    dist_prev = haversine_km(prev_point, current_point) if (prev_point and current_point) else 0.0

    hours_since_prev = (
        (current_ts - previous.timestamp).total_seconds() / 3600.0 if previous else 0.0
    )
    implied = (dist_prev / hours_since_prev) if (hours_since_prev > 0 and dist_prev > 0) else 0.0
    implied = min(_KMH_CAP, implied)

    hour_of_day = float(current_ts.hour)
    is_night = 1.0 if 0 <= current_ts.hour <= 5 else 0.0
    mode = baseline.hour_mode if has_90d else -1
    hour_deviation = _hour_deviation(hour_of_day, mode)

    return {
        "txn_count_1h": float(count_within(timedelta(hours=1))),
        "txn_count_24h": float(count_within(timedelta(hours=24))),
        "amt_sum_1h": round(amount_within(timedelta(hours=1)), 2),
        "amt_sum_24h": round(amount_within(timedelta(hours=24)), 2),
        "amt_over_median_90d": round(amount / median, 4) if median else 0.0,
        "amt_zscore_90d": round(zscore, 4),
        "is_new_merchant": is_new_merchant,
        "is_new_category": is_new_category,
        "days_since_first_seen_merchant": round(days_since_first, 2),
        "dist_from_home_km": round(dist_home, 2),
        "dist_from_prev_txn_km": round(dist_prev, 2),
        "implied_velocity_kmh": round(implied, 2),
        "hour_of_day": hour_of_day,
        "is_night": is_night,
        "hours_since_prev_txn": round(hours_since_prev, 2),
        "hour_deviation_from_customer_mode": round(hour_deviation, 2),
    }


def map_to_model(
    features16: dict[str, float],
    transaction: TransactionInput,
    history: list[StoredTransaction],
) -> dict[str, float]:
    """Map the causal features onto the ordered model feature matrix.

    Only ``FEATURE_COLUMNS`` keys are emitted so the returned dict satisfies the
    supervised/anomaly service contract exactly. Raw trust/device signals not
    produced by the causal engine pass through from the transaction input.

    ``amount_log`` is in minor currency units (cents) to match the training
    matrix (``amount_log = log1p(amount_minor)`` in the synthetic generator);
    ``TransactionInput.amount`` is in major units.
    """
    prior = [tx for tx in history if tx.timestamp < transaction.timestamp]
    velocity_5m = sum(
        1 for tx in prior if (transaction.timestamp - tx.timestamp) <= timedelta(minutes=5)
    )
    model = {
        "amount_log": round(math.log1p(max(0.0, transaction.amount * 100.0)), 4),
        "mcc_risk": round(float(transaction.mcc_risk), 4),
        "velocity_5m": float(velocity_5m),
        "device_trust": float(transaction.device_trust),
        "network_trust": float(transaction.network_trust),
        "impossible_travel": float(transaction.impossible_travel),
        "new_device": float(transaction.new_device),
        "hour_of_day": features16["hour_of_day"],
        "weekend": float(1 if transaction.timestamp.weekday() >= 5 else 0),
        "distance_km": features16["dist_from_home_km"],
    }
    return {column: model[column] for column in FEATURE_COLUMNS}


def describe_features16(
    features16: dict[str, float],
    metrics: BaselineMetrics | None,
) -> list[FeatureRow]:
    """Render all 16 causal features as the dashboard's feature table."""
    baseline = metrics or BaselineMetrics()
    median_baseline = f"median ${baseline.median_amount:,.2f}" if baseline.count else "—"
    mode_baseline = f"{baseline.hour_mode:02d}:00 usual hour" if baseline.hour_mode >= 0 else "—"

    def row(name: str, unit: str, value: str, customer_baseline: str = "—") -> FeatureRow:
        return FeatureRow(
            name=name,
            value=value,
            customer_baseline=customer_baseline,
            unit=unit,
        )

    return [
        row("txn_count_1h", "txns", _fmt(features16["txn_count_1h"])),
        row("txn_count_24h", "txns", _fmt(features16["txn_count_24h"])),
        row("amt_sum_1h", "$", _fmt(features16["amt_sum_1h"])),
        row("amt_sum_24h", "$", _fmt(features16["amt_sum_24h"])),
        row("amt_over_median_90d", "×", _fmt(features16["amt_over_median_90d"]), median_baseline),
        row("amt_zscore_90d", "σ", _fmt(features16["amt_zscore_90d"])),
        row("is_new_merchant", "0/1", _fmt(features16["is_new_merchant"])),
        row("is_new_category", "0/1", _fmt(features16["is_new_category"])),
        row(
            "days_since_first_seen_merchant",
            "days",
            _fmt(features16["days_since_first_seen_merchant"]),
        ),
        row("dist_from_home_km", "km", _fmt(features16["dist_from_home_km"])),
        row("dist_from_prev_txn_km", "km", _fmt(features16["dist_from_prev_txn_km"])),
        row("implied_velocity_kmh", "km/h", _fmt(features16["implied_velocity_kmh"])),
        row("hour_of_day", "hour", _fmt(features16["hour_of_day"])),
        row("is_night", "0/1", _fmt(features16["is_night"])),
        row("hours_since_prev_txn", "h", _fmt(features16["hours_since_prev_txn"])),
        row(
            "hour_deviation_from_customer_mode",
            "h",
            _fmt(features16["hour_deviation_from_customer_mode"]),
            mode_baseline,
        ),
    ]


def _hour_deviation(hour: float, mode: int) -> float:
    """Smallest circular distance (0-12h) of ``hour`` from the modal hour."""
    if mode < 0:
        return 0.0
    diff = abs(hour - mode)
    return float(min(diff, 24 - diff))


def _centroid(transactions: list[StoredTransaction]) -> GeoPoint | None:
    points = [point for tx in transactions if (point := _point(tx)) is not None]
    if not points:
        return None
    return GeoPoint(
        lat=sum(point.lat for point in points) / len(points),
        lon=sum(point.lon for point in points) / len(points),
    )


def _point(tx: StoredTransaction) -> GeoPoint | None:
    return tx.location or tx.merchant_location


def _distance(home: GeoPoint | None, merchant: GeoPoint | None, card: GeoPoint | None) -> float:
    """Distance from the customer's home to the transaction's merchant."""
    if merchant is None:
        return 0.0
    if home is not None:
        return haversine_km(home, merchant)
    if card is not None:
        return haversine_km(card, merchant)
    return 0.0


def _fmt(value: float) -> str:
    return f"{float(value):g}"


__all__ = ["FEATURES16", "compute_features16", "describe_features16", "map_to_model"]
