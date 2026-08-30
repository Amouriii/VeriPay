"""Canonical model feature ordering (PLAN §10, §11).

Single source of truth for the ordered model matrix. ``services/supervised_model``
and ``services/anomaly_model`` mirror this ordering at their serving boundary;
keep the two lists identical.
"""

from __future__ import annotations

FEATURE_COLUMNS: list[str] = [
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
]

# Columns present in the raw dataset but excluded from the model matrix
# (identifiers, or raw columns already transformed into features).
NON_FEATURE_COLUMNS: list[str] = [
    "transaction_id",
    "amount_minor",
    "mcc",
]

__all__ = ["FEATURE_COLUMNS", "NON_FEATURE_COLUMNS"]
