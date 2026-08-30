"""Supervised fraud model scoring. PLAN §10, §20.

Loads the XGBoost artifact trained by ``ml/supervised/train.py`` and serves
per-transaction fraud probabilities. If no artifact is present (or the model
dependency is not installed), a deterministic heuristic fallback keeps the
pipeline functional — see ``docs/ai-justification.md`` for the degradation
analysis.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

# Must match ``ml/supervised/features.py`` exactly (single source of truth
# for the training matrix ordering).
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

_HEURISTIC_WEIGHTS: dict[str, float] = {
    "amount_log": 2.0,
    "mcc_risk": 30.0,
    "velocity_5m": 2.0,
    "impossible_travel": 20.0,
    "new_device": 15.0,
    "hour_of_day": 0.4,
    "weekend": 3.0,
    "distance_km": 0.01,
}

# Trust signals are tricategorical (1 = trusted, 0 = untrusted, -1 = unknown).
# Fail-closed fallback: untrusted raises risk, unknown raises a little,
# trusted adds nothing.
_TRUST_RISK: dict[str, tuple[float, float]] = {
    "device_trust": (12.0, 4.0),
    "network_trust": (10.0, 3.0),
}


class ScoreRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    features: dict[str, float]


class ScoreResponse(BaseModel):
    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    risk_score: int = Field(ge=0, le=100)
    model_name: str
    model_version: str
    model_available: bool
    fallback: bool = False


class _ModelBundle:
    def __init__(self, model: Any, *, version: str, available: bool) -> None:
        self.model = model
        self.version = version
        self.available = available


def default_model_path() -> Path:
    """Resolve the trained artifact path (env-overridable, repo-relative default)."""
    env = os.getenv("MODEL_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "ml" / "models" / "supervised" / "latest"


def _read_sidecar(model_dir: Path) -> dict[str, Any]:
    sidecar = model_dir / "model.json"
    if not sidecar.exists():
        return {}
    return json.loads(sidecar.read_text(encoding="utf-8"))


def _load_model() -> _ModelBundle:
    """Load the XGBoost artifact lazily; never raise for a missing model."""
    model_dir = default_model_path()
    artifact = model_dir / "model.joblib"
    if not artifact.exists():
        return _ModelBundle(None, version="unavailable", available=False)
    try:
        import joblib  # noqa: PLC0415

        model = joblib.load(artifact)
    except (ImportError, ModuleNotFoundError, OSError, ValueError):
        return _ModelBundle(None, version="unavailable", available=False)
    sidecar = _read_sidecar(model_dir)
    return _ModelBundle(
        model,
        version=str(sidecar.get("version", "unknown")),
        available=True,
    )


def _feature_vector(features: dict[str, float]) -> np.ndarray:
    """Build the ordered model matrix; missing features default to 0.0."""
    values = [float(features.get(column, 0.0)) for column in FEATURE_COLUMNS]
    return np.asarray([values], dtype=np.float64)


def _heuristic_risk(features: dict[str, float]) -> int:
    """Deterministic fallback score when the trained model is unavailable.

    Trust signals are mapped explicitly (trusted = 0 risk, untrusted = high,
    unknown = mild) so an absent/unknown signal never *lowers* the score.
    """
    total = 0.0
    for column, weight in _HEURISTIC_WEIGHTS.items():
        total += float(features.get(column, 0.0)) * weight
    for column, (untrusted_weight, unknown_weight) in _TRUST_RISK.items():
        value = float(features.get(column, -1.0))
        if value == 0.0:
            total += untrusted_weight
        elif value < 0.0:
            total += unknown_weight
    return max(0, min(100, int(round(total))))


def evaluate(request: ScoreRequest) -> ScoreResponse:
    """Score a transaction: trained model when available, heuristic otherwise."""
    bundle = _load_model()
    if not bundle.available:
        risk_score = _heuristic_risk(request.features)
        return ScoreResponse(
            transaction_id=request.transaction_id,
            fraud_probability=round(risk_score / 100, 4),
            risk_score=risk_score,
            model_name="supervised-heuristic",
            model_version="fallback",
            model_available=False,
            fallback=True,
        )
    probability = float(bundle.model.predict_proba(_feature_vector(request.features))[0, 1])
    risk_score = int(round(probability * 100))
    return ScoreResponse(
        transaction_id=request.transaction_id,
        fraud_probability=round(probability, 4),
        risk_score=max(0, min(100, risk_score)),
        model_name="supervised",
        model_version=bundle.version,
        model_available=True,
        fallback=False,
    )


__all__ = [
    "FEATURE_COLUMNS",
    "ScoreRequest",
    "ScoreResponse",
    "default_model_path",
    "evaluate",
]
