"""Isolation Forest anomaly scoring. PLAN §11.

Loads the artifact trained by ``ml/anomaly/train.py`` and serves per-transaction
anomaly scores (0–1) plus a 0–100 risk contribution. If no artifact is present
(or scikit-learn is not installed), a deterministic fallback reports an
unavailable model rather than failing the request.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

# Must match ``ml/supervised/features.py`` exactly (single source of truth
# for the feature ordering used by both training pipelines).
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

_FALLBACK_RISK = 20  # conservative neutral score when the model is unavailable


class AnomalyRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    features: dict[str, float]


class AnomalyResponse(BaseModel):
    transaction_id: str
    anomaly_score: float = Field(ge=0, le=1)
    risk_score: int = Field(ge=0, le=100)
    is_anomaly: bool
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
    return Path(__file__).resolve().parents[3] / "ml" / "models" / "anomaly" / "latest"


def _read_sidecar(model_dir: Path) -> dict[str, Any]:
    sidecar = model_dir / "model.json"
    if not sidecar.exists():
        return {}
    return json.loads(sidecar.read_text(encoding="utf-8"))


def _load_model() -> _ModelBundle:
    """Load the Isolation Forest artifact lazily; never raise for a missing model."""
    model_dir = default_model_path()
    artifact = model_dir / "model.joblib"
    if not artifact.exists():
        return _ModelBundle(None, version="unavailable", available=False)
    try:
        import joblib

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


def _sigmoid(value: float) -> float:
    """Map a raw anomaly magnitude to (0, 1)."""
    try:
        return 1.0 / (1.0 + math.exp(-value))
    except OverflowError:
        return 1.0 if value > 0 else 0.0


def evaluate(request: AnomalyRequest) -> AnomalyResponse:
    """Score a transaction: trained model when available, neutral fallback otherwise."""
    bundle = _load_model()
    if not bundle.available:
        return AnomalyResponse(
            transaction_id=request.transaction_id,
            anomaly_score=0.0,
            risk_score=_FALLBACK_RISK,
            is_anomaly=False,
            model_name="anomaly-unavailable",
            model_version="fallback",
            model_available=False,
            fallback=True,
        )
    raw = -float(bundle.model.decision_function(_feature_vector(request.features))[0])
    anomaly_score = round(_sigmoid(raw), 4)
    risk_score = int(round(anomaly_score * 100))
    return AnomalyResponse(
        transaction_id=request.transaction_id,
        anomaly_score=anomaly_score,
        risk_score=max(0, min(100, risk_score)),
        is_anomaly=raw > 0.0,
        model_name="anomaly",
        model_version=bundle.version,
        model_available=True,
        fallback=False,
    )


__all__ = [
    "AnomalyRequest",
    "AnomalyResponse",
    "FEATURE_COLUMNS",
    "default_model_path",
    "evaluate",
]
