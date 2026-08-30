"""Drift detection tests: reference profiles and PSI classification."""

from __future__ import annotations

import numpy as np
import pandas as pd

from drift.detect import PSI_TRIGGER, drift_report, feature_drift, psi
from drift.profile import compute_reference_profile, load_profile, save_profile

FEATURES = ["amount_log", "velocity_5m", "device_trust"]


def _frame(amount_mean: float, velocity_mean: float, n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "amount_log": rng.normal(amount_mean, 0.8, size=n),
            "velocity_5m": rng.poisson(velocity_mean, size=n).astype(float),
            "device_trust": rng.choice([-1.0, 0.0, 1.0], size=n, p=[0.1, 0.2, 0.7]),
        }
    )


def test_psi_identical_distributions_is_near_zero() -> None:
    counts = [100, 100, 100]
    assert psi(counts, counts) < 1e-6


def test_psi_shifted_distribution_is_large() -> None:
    assert psi([100, 0, 0], [0, 0, 100]) > PSI_TRIGGER


def test_psi_empty_histogram_is_infinite() -> None:
    assert psi([0, 0], [5, 5]) == float("inf")


def test_profile_roundtrip_and_consumption(tmp_path) -> None:
    reference = _frame(amount_mean=8.0, velocity_mean=2.0)
    profile = compute_reference_profile(reference, FEATURES, model_name="supervised", version="v1")
    path = tmp_path / "reference_profile.json"
    save_profile(profile, path)
    loaded = load_profile(path)
    assert loaded["features"]["amount_log"]["edges"] == profile["features"]["amount_log"]["edges"]

    same_population = _frame(amount_mean=8.0, velocity_mean=2.0)
    drift_same = feature_drift(loaded, same_population, FEATURES)
    assert all(value < 0.2 for value in drift_same.values())

    drifted_population = _frame(amount_mean=11.0, velocity_mean=20.0)
    drift_moved = feature_drift(loaded, drifted_population, FEATURES)
    assert drift_moved["amount_log"] > PSI_TRIGGER
    assert drift_moved["velocity_5m"] > PSI_TRIGGER


def test_drift_report_verdicts() -> None:
    reference = _frame(amount_mean=8.0, velocity_mean=2.0)
    profile = compute_reference_profile(reference, FEATURES, version="v1")

    stable = drift_report(profile, _frame(amount_mean=8.0, velocity_mean=2.0), FEATURES)
    assert stable["verdict"] == "STABLE"

    drifted = drift_report(profile, _frame(amount_mean=12.0, velocity_mean=25.0), FEATURES)
    assert drifted["verdict"] == "DRIFT"
    assert drifted["max_psi"] >= PSI_TRIGGER

    tiny = drift_report(profile, _frame(amount_mean=12.0, velocity_mean=25.0, n=10), FEATURES)
    assert tiny["verdict"] == "INSUFFICIENT_DATA"
