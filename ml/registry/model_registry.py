"""Model versioning + rollback registry (PLAN §10 governance).

Models are versioned with training dataset snapshots, artifact paths, and
evaluation metrics. ``latest`` is a pointer that training advances and
``rollback`` can rewind, so serving always reads a named, auditable version.

Registry file: ``<repo>/ml/models/registry.json`` (override with the
``VERIPAY_MODEL_REGISTRY`` environment variable, useful in tests).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def registry_path() -> Path:
    """Return the registry JSON path (env-overridable for tests)."""
    env = os.getenv("VERIPAY_MODEL_REGISTRY")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "ml" / "models" / "registry.json"


def _load() -> dict[str, Any]:
    path = registry_path()
    if not path.exists():
        return {"models": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(payload: dict[str, Any]) -> None:
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def register(
    model_name: str,
    version: str | None = None,
    *,
    artifact_path: str | None = None,
    metrics: dict[str, float] | None = None,
    dataset_path: str | None = None,
    dataset_fingerprint: str | None = None,
    trained_at: str | None = None,
    reference_profile: str | None = None,
) -> dict[str, Any]:
    """Register (or overwrite) a model version and point ``latest`` at it.

    ``version`` defaults to a UTC timestamp when omitted. Returns the stored
    version record. ``reference_profile`` records the path to the drift
    reference profile JSON (see ``ml/drift``), consumed by the model monitor.
    """
    resolved_version = version or _utc_now()
    payload = _load()
    entry: dict[str, Any] = {
        "version": resolved_version,
        "trained_at": trained_at or _utc_now(),
        "artifact_path": artifact_path,
        "metrics": metrics or {},
        "dataset_path": dataset_path,
        "dataset_fingerprint": dataset_fingerprint,
        "reference_profile": reference_profile,
    }
    model = payload["models"].setdefault(model_name, {"latest": None, "versions": {}})
    model["versions"][resolved_version] = entry
    model["latest"] = resolved_version
    _save(payload)
    return dict(entry)


def rollback(model_name: str, to_version: str) -> dict[str, Any]:
    """Point ``latest`` at a previously registered version. Raises on unknown version."""
    payload = _load()
    model = payload["models"].get(model_name)
    if model is None:
        raise KeyError(f"Unknown model: {model_name!r}")
    if to_version not in model["versions"]:
        raise KeyError(f"Unknown version {to_version!r} for model {model_name!r}")
    model["latest"] = to_version
    _save(payload)
    return dict(model["versions"][to_version])


def latest(model_name: str) -> dict[str, Any] | None:
    """Return the latest registered version record, or ``None`` if unregistered."""
    model = _load()["models"].get(model_name)
    if model is None or model["latest"] is None:
        return None
    return model["versions"][model["latest"]]


def all_versions(model_name: str) -> dict[str, dict[str, Any]]:
    """Return every registered version record for ``model_name`` (may be empty)."""
    model = _load()["models"].get(model_name)
    if model is None:
        return {}
    return model["versions"]


__all__ = [
    "all_versions",
    "latest",
    "register",
    "registry_path",
    "rollback",
]
