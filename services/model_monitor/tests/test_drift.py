"""Drift tests: PSI math, feature drift, verdicts, profile loading."""

from __future__ import annotations

import json

import numpy as np
from veripay_model_monitor.service import (
    PSI_TRIGGER,
    Observation,
    WindowedObservationStore,
    drift_report,
    feature_drift,
    load_reference_profile,
    psi,
)

FEATURES = ["amount_log", "velocity_5m"]


def _profile_from(observations: list[Observation]) -> dict:
    """Build a reference profile from a sample (mirrors ml/drift/profile.py)."""
    features = {}
    for column in FEATURES:
        values = np.asarray(
            [float(observation.features.get(column, 0.0)) for observation in observations]
        )
        edges = np.unique(np.quantile(values, np.linspace(0.0, 1.0, 4)))
        counts, _ = np.histogram(values, bins=edges)
        features[column] = {
            "edges": [float(edge) for edge in edges],
            "counts": [int(count) for count in counts],
        }
    return {"version": "v1", "features": features}


def _observations(amount_mean: float, velocity_mean: float, n: int = 40) -> list[Observation]:
    rng = np.random.default_rng(7)
    return [
        Observation(
            transaction_id=f"tx_{i}",
            features={
                "amount_log": float(rng.normal(amount_mean, 0.5)),
                "velocity_5m": float(rng.poisson(velocity_mean)),
            },
            score=50.0,
        )
        for i in range(n)
    ]


def test_psi_identical_and_shifted() -> None:
    assert psi([10, 10, 10], [10, 10, 10]) < 1e-6
    assert psi([10, 0, 0], [0, 0, 10]) > PSI_TRIGGER
    assert psi([0, 0], [5, 5]) == float("inf")


def test_drift_report_verdicts() -> None:
    reference = _observations(7.0, 3.0)
    profile = _profile_from(reference)

    stable = drift_report(profile, _observations(7.0, 3.0))
    assert stable["verdict"] == "STABLE"

    drifted = drift_report(profile, _observations(14.0, 18.0))
    assert drifted["verdict"] == "DRIFT"
    assert drifted["feature_psi"]["amount_log"] > PSI_TRIGGER

    tiny = drift_report(profile, _observations(14.0, 18.0, n=10), min_window=30)
    assert tiny["verdict"] == "INSUFFICIENT_DATA"


def test_missing_features_are_counted() -> None:
    profile = _profile_from(_observations(7.0, 3.0))
    observations = _observations(7.0, 3.0, n=40)
    observations[0].features.pop("velocity_5m")
    per_feature, missing_rate = feature_drift(profile, observations)
    assert per_feature["velocity_5m"] >= 0.0
    assert missing_rate > 0.0


def test_load_reference_profile_from_registry(tmp_path) -> None:
    registry = tmp_path / "registry.json"
    model_dir = tmp_path / "models"
    profile_dir = model_dir / "supervised" / "latest"
    profile_dir.mkdir(parents=True)
    profile = {"version": "v9", "features": {}}
    (profile_dir / "reference_profile.json").write_text(json.dumps(profile))
    registry.write_text(
        json.dumps(
            {
                "models": {
                    "supervised": {
                        "latest": "v9",
                        "versions": {
                            "v9": {"reference_profile": str(profile_dir / "reference_profile.json")}
                        },
                    }
                }
            }
        )
    )
    loaded = load_reference_profile(registry, "supervised", model_dir=model_dir)
    assert loaded is not None
    assert loaded["version"] == "v9"


def test_store_is_bounded() -> None:
    store = WindowedObservationStore(maxlen=3)
    for i in range(5):
        store.add(Observation(transaction_id=f"tx_{i}", features={}, score=10.0))
    assert len(store.list()) == 3
    assert store.list()[0].transaction_id == "tx_2"
