"""Reference feature profiles for drift monitoring (PLAN §10, §21).

A reference profile captures the feature distribution the model was trained
on: per-feature histogram edges and counts. At monitoring time, the same bin
edges are applied to the live window and Population Stability Index (PSI) is
computed bin-by-bin (see ``ml/drift/detect.py``).

The profile JSON is the contract shared with ``services/model_monitor``
(which mirrors the PSI math), so the format here must not change without
updating the service.

Profile shape::

    {
      "model_name": "supervised",
      "version": "2026-...",
      "created_at": "...",
      "features": {
        "amount_log": {"edges": [...], "counts": [...]},
        ...
      }
    }
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_BINS = 10


def compute_reference_profile(
    frame: pd.DataFrame,
    feature_columns: list[str],
    *,
    bins: int = DEFAULT_BINS,
    model_name: str = "supervised",
    version: str = "unknown",
) -> dict[str, Any]:
    """Compute per-feature histogram profiles from a training frame.

    Quantile bin edges keep every bin populated in the reference, which makes
    PSI robust even for skewed features (amount, distance).
    """
    features: dict[str, dict[str, Any]] = {}
    for column in feature_columns:
        values = frame[column].to_numpy(dtype=np.float64)
        quantiles = np.linspace(0.0, 1.0, bins + 1)
        edges = np.quantile(values, quantiles)
        edges = np.unique(edges)
        if len(edges) < 2:
            # Constant feature: a single widened bin.
            edges = np.array([float(values.min()), float(values.max()) + 1.0])
        counts, _ = np.histogram(values, bins=edges)
        features[column] = {
            "edges": [float(edge) for edge in edges],
            "counts": [int(count) for count in counts],
        }
    return {
        "model_name": model_name,
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "features": features,
    }


def save_profile(profile: dict[str, Any], path: str | Path) -> None:
    """Persist the profile as JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")


def load_profile(path: str | Path) -> dict[str, Any]:
    """Load a profile JSON (raises FileNotFoundError when absent)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


__all__ = ["compute_reference_profile", "load_profile", "save_profile"]
