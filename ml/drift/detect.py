"""PSI-based drift detection (PLAN §10, §21).

``services/model_monitor`` mirrors this PSI math against the reference profile
JSON produced here; keep both implementations identical.

Thresholds follow the standard PSI convention: < 0.1 no shift, 0.1-0.25
moderate, > 0.25 significant. ``PSI_TRIGGER`` is the boundary at which the
monitor recommends retraining.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

PSI_TRIGGER = 0.25
EPSILON = 1e-6


def psi(reference_counts: list[int] | np.ndarray, current_counts: list[int] | np.ndarray) -> float:
    """Population Stability Index between two count histograms over the same bins."""
    reference = np.asarray(reference_counts, dtype=np.float64)
    current = np.asarray(current_counts, dtype=np.float64)
    if reference.sum() <= 0 or current.sum() <= 0:
        return float("inf")
    reference_p = reference / reference.sum() + EPSILON
    current_p = current / current.sum() + EPSILON
    return float(np.sum((current_p - reference_p) * np.log(current_p / reference_p)))


def feature_drift(
    profile: dict[str, Any],
    current_frame: pd.DataFrame,
    feature_columns: list[str],
) -> dict[str, float]:
    """Per-feature PSI between the reference profile and the current frame."""
    features = profile.get("features", {})
    result: dict[str, float] = {}
    for column in feature_columns:
        reference = features.get(column)
        if reference is None or column not in current_frame.columns:
            continue
        counts, _ = np.histogram(
            current_frame[column].to_numpy(dtype=np.float64), bins=reference["edges"]
        )
        result[column] = psi(reference["counts"], counts)
    return result


def drift_report(
    profile: dict[str, Any],
    current_frame: pd.DataFrame,
    feature_columns: list[str],
    *,
    min_window: int = 30,
    psi_threshold: float = PSI_TRIGGER,
) -> dict[str, Any]:
    """Classify the current window against the reference profile.

    Verdict is ``INSUFFICIENT_DATA`` below ``min_window`` rows, otherwise
    ``DRIFT`` when any feature PSI meets the threshold, else ``STABLE``.
    """
    window_size = len(current_frame)
    if window_size < min_window:
        return {
            "verdict": "INSUFFICIENT_DATA",
            "feature_psi": {},
            "max_psi": None,
            "window_size": window_size,
            "min_window": min_window,
            "missing_rate": 0.0,
        }
    per_feature = feature_drift(profile, current_frame, feature_columns)
    max_psi = max(per_feature.values()) if per_feature else 0.0
    missing = current_frame[feature_columns].isna().any(axis=1).mean()
    return {
        "verdict": "DRIFT" if max_psi >= psi_threshold else "STABLE",
        "feature_psi": per_feature,
        "max_psi": float(max_psi),
        "window_size": window_size,
        "min_window": min_window,
        "missing_rate": float(missing),
        "psi_threshold": psi_threshold,
    }


__all__ = ["PSI_TRIGGER", "drift_report", "feature_drift", "psi"]
