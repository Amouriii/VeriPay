"""Feature builder for the analyst score pipeline.

Derives the shared model feature matrix (``FEATURE_COLUMNS`` used by the
supervised and anomaly services) from a raw transaction plus that customer's
already-recorded history. Causality is guaranteed by construction: only
transactions that occurred strictly before this one are ever referenced, so a
later transaction can never change an earlier feature vector (this mirrors the
``_causal_window.py`` guarantee described in the architecture).
"""

from __future__ import annotations

import math
from datetime import timedelta
from typing import Any

from veripay_analyst_api.models import FeatureRow, GeoPoint, TransactionInput
from veripay_analyst_api.profiles import BaselineMetrics, StoredTransaction, haversine_km

FEATURE_COLUMNS: tuple[str, ...] = (
    "amount_log",
    "mcc_risk",
    "velocity_5m",
    "device_trust",
    "network_trust",
    "impossible_travel",
    "new_device",
    "hour_of_day",
    "weekend",
    "distance_km",
)


def build_features(
    transaction: TransactionInput,
    history: list[StoredTransaction],
    metrics: BaselineMetrics | None = None,
) -> dict[str, float]:
    """Build the ordered model feature matrix from raw inputs + past history.

    ``amount_log`` uses minor currency units (cents) to match the training
    matrix exactly: ``ml/datasets/generate_synthetic.py`` derives
    ``amount_log = log1p(amount_minor)`` where ``amount_minor`` is the cent
    value. Feeding dollars here would shift every vector ~4.6 units below the
    trained distribution and collapse both models' scores.
    """
    prior = [tx for tx in history if tx.timestamp < transaction.timestamp]
    velocity_5m = sum(
        1 for tx in prior if (transaction.timestamp - tx.timestamp) <= timedelta(minutes=5)
    )
    home = _centroid_location(prior)
    distance_km = _distance_km(transaction, home)
    return {
        "amount_log": round(math.log1p(max(0.0, transaction.amount * 100.0)), 4),
        "mcc_risk": round(float(transaction.mcc_risk), 4),
        "velocity_5m": float(velocity_5m),
        "device_trust": float(transaction.device_trust),
        "network_trust": float(transaction.network_trust),
        "impossible_travel": float(transaction.impossible_travel),
        "new_device": float(transaction.new_device),
        "hour_of_day": float(transaction.timestamp.hour),
        "weekend": float(1 if transaction.timestamp.weekday() >= 5 else 0),
        "distance_km": round(distance_km, 2),
    }


def describe_features(
    features: dict[str, float],
    metrics: BaselineMetrics | None,
) -> list[FeatureRow]:
    """Render the feature vector as analyst-friendly rows with baselines."""
    baseline = metrics or BaselineMetrics()
    typical_hours = (
        f"{baseline.hour_low:02d}:00–{baseline.hour_high:02d}:00" if baseline.count else "—"
    )
    rows: list[FeatureRow] = [
        FeatureRow(name="amount", value=_fmt(features.get("amount_log")), unit="log($)"),
        FeatureRow(
            name="hour_of_day", value=f"{int(features.get('hour_of_day', 0))}:00", unit="hour"
        ),
        FeatureRow(name="weekend", value=_fmt(features.get("weekend")), unit="0/1"),
        FeatureRow(name="mcc_risk", value=_fmt(features.get("mcc_risk")), unit="0–1"),
        FeatureRow(name="velocity_5m", value=_fmt(features.get("velocity_5m")), unit="txns"),
        FeatureRow(name="distance_km", value=_fmt(features.get("distance_km")), unit="km"),
        FeatureRow(name="new_device", value=_fmt(features.get("new_device")), unit="0/1"),
        FeatureRow(
            name="impossible_travel", value=_fmt(features.get("impossible_travel")), unit="0/1"
        ),
        FeatureRow(
            name="median_amount_90d",
            value=_fmt(math.log1p(max(0.0, baseline.median_amount * 100.0))),
            customer_baseline=typical_hours,
            unit="log(¢)/typical hours",
        ),
    ]
    return rows


def _centroid_location(history: list[StoredTransaction]) -> GeoPoint | None:
    points: list[GeoPoint] = []
    for tx in history:
        point = tx.location or tx.merchant_location
        if point is not None:
            points.append(point)
    if not points:
        return None
    return GeoPoint(
        lat=sum(p.lat for p in points) / len(points),
        lon=sum(p.lon for p in points) / len(points),
    )


def _distance_km(transaction: TransactionInput, home: GeoPoint | None) -> float:
    merchant = transaction.merchant_location
    if merchant is None:
        return 0.0
    if home is not None:
        return haversine_km(home, merchant)
    if transaction.location is not None:
        return haversine_km(transaction.location, merchant)
    return 0.0


def _fmt(value: Any) -> str:
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return "—"


__all__ = ["FEATURE_COLUMNS", "build_features", "describe_features"]
