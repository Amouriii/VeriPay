"""Model monitoring: drift detection and gated retraining. PLAN §10, §21.

Tracks scored transactions (observations), detects feature drift against the
reference profile of the latest registered model (``ml/drift``), and retrains
through the training CLI when triggered. A new model is promoted to ``latest``
only when its held-out metrics clear a gate versus the current champion —
a worse retrain never replaces a good model. Analyst labels are joined from
the feedback loop by transaction id.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel, Field

# Mirrors ``ml/supervised/features.py`` (single source of truth for ordering).
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

# PSI conventions: < 0.1 no shift, 0.1-0.25 moderate, > 0.25 significant.
PSI_TRIGGER = 0.25
_EPSILON = 1e-6

# Mirrors ``ml/datasets/generate_synthetic.py`` MCC_RISK (inverse lookup).
_MCC_BY_RISK: list[tuple[float, int]] = [
    (0.10, 5411),
    (0.10, 4900),
    (0.20, 4121),
    (0.20, 5412),
    (0.25, 5712),
    (0.30, 5814),
    (0.30, 7995),
    (0.35, 5691),
    (0.40, 5311),
    (0.45, 5812),
    (0.55, 4814),
    (0.70, 5968),
    (0.80, 4829),
    (0.85, 6011),
]

_DATASET_COLUMNS = [
    "transaction_id",
    "amount_minor",
    "amount_log",
    "mcc",
    "mcc_risk",
    "hour_of_day",
    "weekend",
    "velocity_5m",
    "device_trust",
    "network_trust",
    "impossible_travel",
    "new_device",
    "distance_km",
    "is_fraud",
]


class MonitorLabel(StrEnum):
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    LEGITIMATE = "LEGITIMATE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Observation(BaseModel):
    transaction_id: str = Field(min_length=1)
    features: dict[str, float]
    score: float = Field(ge=0, le=100)
    label: MonitorLabel | None = None
    observed_at: datetime | None = None


class ObservationStore(Protocol):
    def add(self, observation: Observation) -> Observation: ...

    def list(self) -> list[Observation]: ...


@dataclass
class WindowedObservationStore:
    """Bounded, deterministic in-memory observation window."""

    maxlen: int = 1_000
    observations: deque[Observation] = field(default_factory=deque)

    def add(self, observation: Observation) -> Observation:
        self.observations.append(observation)
        while len(self.observations) > self.maxlen:
            self.observations.popleft()
        return observation

    def list(self) -> list[Observation]:
        return list(self.observations)


# --------------------------------------------------------------------------- drift


def psi(reference_counts: list[int] | np.ndarray, current_counts: list[int] | np.ndarray) -> float:
    """Population Stability Index between two count histograms (mirrors ml/drift)."""
    reference = np.asarray(reference_counts, dtype=np.float64)
    current = np.asarray(current_counts, dtype=np.float64)
    if reference.sum() <= 0 or current.sum() <= 0:
        return float("inf")
    reference_p = reference / reference.sum() + _EPSILON
    current_p = current / current.sum() + _EPSILON
    return float(np.sum((current_p - reference_p) * np.log(current_p / reference_p)))


def _feature_values(observations: list[Observation], column: str) -> tuple[np.ndarray, float]:
    values = np.asarray(
        [float(observation.features.get(column, 0.0)) for observation in observations],
        dtype=np.float64,
    )
    missing = sum(1 for observation in observations if column not in observation.features)
    return values, missing / max(len(observations), 1)


def feature_drift(
    profile: dict[str, Any],
    observations: list[Observation],
    feature_columns: list[str] = FEATURE_COLUMNS,
) -> tuple[dict[str, float], float]:
    """Per-feature PSI vs the reference profile plus overall missing rate."""
    features = profile.get("features", {})
    per_feature: dict[str, float] = {}
    missing_count = 0
    for column in feature_columns:
        reference = features.get(column)
        if reference is None:
            continue
        values, _ = _feature_values(observations, column)
        counts, _ = np.histogram(values, bins=reference["edges"])
        per_feature[column] = psi(reference["counts"], counts)
        missing_count += sum(
            1 for observation in observations if column not in observation.features
        )
    missing_rate = missing_count / max(len(observations) * len(feature_columns), 1)
    return per_feature, float(missing_rate)


def drift_report(
    profile: dict[str, Any],
    observations: list[Observation],
    feature_columns: list[str] = FEATURE_COLUMNS,
    *,
    min_window: int = 30,
    psi_threshold: float = PSI_TRIGGER,
) -> dict[str, Any]:
    """Classify the observation window against the reference profile."""
    window_size = len(observations)
    if window_size < min_window:
        return {
            "verdict": "INSUFFICIENT_DATA",
            "feature_psi": {},
            "max_psi": None,
            "window_size": window_size,
            "min_window": min_window,
            "missing_rate": 0.0,
        }
    per_feature, missing_rate = feature_drift(profile, observations, feature_columns)
    max_psi = max(per_feature.values()) if per_feature else 0.0
    return {
        "verdict": "DRIFT" if max_psi >= psi_threshold else "STABLE",
        "feature_psi": per_feature,
        "max_psi": float(max_psi),
        "window_size": window_size,
        "min_window": min_window,
        "missing_rate": missing_rate,
        "psi_threshold": psi_threshold,
    }


def load_reference_profile(
    registry_path: Path,
    model_name: str,
    *,
    model_dir: Path,
) -> dict[str, Any] | None:
    """Load the reference profile of the latest registered model version."""
    entry = _latest_registry_entry(registry_path, model_name)
    profile_path = None
    if entry is not None:
        profile_path = entry.get("reference_profile")
    if not profile_path:
        fallback = model_dir / model_name / "latest" / "reference_profile.json"
        if fallback.exists():
            profile_path = str(fallback)
    if not profile_path or not Path(profile_path).exists():
        return None
    return json.loads(Path(profile_path).read_text(encoding="utf-8"))


def _latest_registry_entry(registry_path: Path, model_name: str) -> dict[str, Any] | None:
    if not registry_path.exists():
        return None
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    model = payload.get("models", {}).get(model_name)
    if model is None or model.get("latest") is None:
        return None
    return model["versions"].get(model["latest"])


# ----------------------------------------------------------------- retraining


class RetrainResult(BaseModel):
    version: str
    metrics: dict[str, float]
    scratch_dir: str
    dataset_path: str


class Retrainer(Protocol):
    def retrain(
        self,
        dataset_path: Path,
        version: str,
        model_name: str,
        scratch_dir: Path,
    ) -> RetrainResult: ...


class SubprocessRetrainer:
    """Runs the ml training CLI into a caller-provided scratch directory."""

    def __init__(self, repo_root: Path, python: str | None = None) -> None:
        self.repo_root = repo_root
        self.python = python or sys.executable

    def retrain(
        self,
        dataset_path: Path,
        version: str,
        model_name: str,
        scratch_dir: Path,
    ) -> RetrainResult:
        script = self.repo_root / "ml" / model_name / "train.py"
        env = os.environ.copy()
        env["VERIPAY_MODEL_REGISTRY"] = str(scratch_dir / "registry.json")
        completed = subprocess.run(
            [
                self.python,
                str(script),
                "--dataset",
                str(dataset_path),
                "--model-dir",
                str(scratch_dir / "models"),
                "--version",
                version,
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            timeout=900,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"training failed: {completed.stderr[-2000:]}")
        sidecar_path = scratch_dir / "models" / model_name / "latest" / "model.json"
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        return RetrainResult(
            version=sidecar["version"],
            metrics=sidecar["metrics"],
            scratch_dir=str(scratch_dir / "models"),
            dataset_path=str(dataset_path),
        )


class PromoteOutcome(BaseModel):
    gate_passed: bool
    version: str
    metrics: dict[str, float]
    latest_metrics: dict[str, float] | None = None
    reason: str


def _register_version(
    registry_path: Path,
    model_name: str,
    entry: dict[str, Any],
) -> None:
    payload: dict[str, Any] = {"models": {}}
    if registry_path.exists():
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    model = payload["models"].setdefault(model_name, {"latest": None, "versions": {}})
    model["versions"][entry["version"]] = entry
    model["latest"] = entry["version"]
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def promote_if_better(
    result: RetrainResult,
    *,
    model_name: str,
    latest_dir: Path,
    registry_path: Path,
    tolerance: float = 0.01,
) -> PromoteOutcome:
    """Copy the retrained artifacts into ``latest`` only if the gate passes.

    The gate compares held-out ROC-AUC (PR-AUC as fallback) against the
    current champion; without a champion the retrain is promoted by default.
    """
    latest = _latest_registry_entry(registry_path, model_name)
    latest_metrics = latest.get("metrics") if latest is not None else None
    new_metrics = result.metrics
    gate_passed = True
    reason = "first version (no champion to compare)"
    if latest_metrics:
        latest_auc = latest_metrics.get("roc_auc")
        new_auc = new_metrics.get("roc_auc")
        if latest_auc is not None and new_auc is not None:
            gate_passed = new_auc >= latest_auc - tolerance
            reason = f"roc_auc {new_auc:.4f} vs champion {latest_auc:.4f} (tolerance {tolerance})"
        else:
            latest_pr = latest_metrics.get("pr_auc")
            new_pr = new_metrics.get("pr_auc")
            if latest_pr is not None and new_pr is not None:
                gate_passed = new_pr >= latest_pr - tolerance
                reason = f"pr_auc {new_pr:.4f} vs champion {latest_pr:.4f} (tolerance {tolerance})"
    if not gate_passed:
        return PromoteOutcome(
            gate_passed=False,
            version=result.version,
            metrics=new_metrics,
            latest_metrics=latest_metrics,
            reason=reason,
        )

    scratch = Path(result.scratch_dir) / model_name / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("model.joblib", "model.json", "reference_profile.json"):
        source = scratch / filename
        if source.exists():
            shutil.copyfile(source, latest_dir / filename)
    sidecar_path = latest_dir / "model.json"
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    sidecar["reference_profile"] = str(latest_dir / "reference_profile.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    _register_version(
        registry_path,
        model_name,
        {
            "version": result.version,
            "trained_at": datetime.now(UTC).isoformat(),
            "artifact_path": str(latest_dir / "model.joblib"),
            "metrics": new_metrics,
            "dataset_path": result.dataset_path,
            "dataset_fingerprint": _fingerprint(result.dataset_path),
            "reference_profile": sidecar["reference_profile"],
        },
    )
    return PromoteOutcome(
        gate_passed=True,
        version=result.version,
        metrics=new_metrics,
        latest_metrics=latest_metrics,
        reason=reason,
    )


# ------------------------------------------------------- labeled data + dataset


class FeedbackProvider(Protocol):
    """Source of analyst labels joined onto observations by transaction id."""

    def labeled_transactions(self) -> dict[str, str]: ...


class HttpFeedbackProvider:
    """Pulls labels from the feedback loop's append-only export endpoint."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def labeled_transactions(self) -> dict[str, str]:
        url = f"{self.base_url}/api/v1/feedback"
        request = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                records = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return {}
        result: dict[str, str] = {}
        for record in records:
            label = record.get("label")
            if label in {str(value) for value in MonitorLabel}:
                result[record["transaction_id"]] = label
        return result


def _label_to_flag(label: MonitorLabel | str | None) -> int | None:
    if label in (MonitorLabel.CONFIRMED_FRAUD, "CONFIRMED_FRAUD"):
        return 1
    if label in (
        MonitorLabel.LEGITIMATE,
        MonitorLabel.FALSE_POSITIVE,
        "LEGITIMATE",
        "FALSE_POSITIVE",
    ):
        return 0
    return None


def collect_labeled(
    observations: list[Observation],
    feedback_labels: dict[str, str],
) -> list[tuple[Observation, int]]:
    """Merge feedback-loop labels onto observations; label wins over local."""
    labeled: list[tuple[Observation, int]] = []
    for observation in observations:
        flag = _label_to_flag(feedback_labels.get(observation.transaction_id))
        if flag is None:
            flag = _label_to_flag(observation.label)
        if flag is not None:
            labeled.append((observation, flag))
    return labeled


def _nearest_mcc(mcc_risk: float) -> int:
    return min(_MCC_BY_RISK, key=lambda pair: abs(pair[0] - mcc_risk))[1]


def observation_to_row(observation: Observation, flag: int) -> dict[str, Any]:
    """Map an observation back to the dataset schema (inverse transforms).

    ``amount_minor`` and ``mcc`` are reconstructed from the model features so
    the augmented retraining CSV keeps the exact schema the pipeline expects.
    """
    features = observation.features
    amount_log = float(features.get("amount_log", 0.0))
    return {
        "transaction_id": observation.transaction_id,
        "amount_minor": int(round(math.expm1(amount_log))),
        "amount_log": round(amount_log, 6),
        "mcc": _nearest_mcc(float(features.get("mcc_risk", 0.0))),
        "mcc_risk": round(float(features.get("mcc_risk", 0.0)), 6),
        "hour_of_day": int(features.get("hour_of_day", 0.0)),
        "weekend": int(features.get("weekend", 0.0)),
        "velocity_5m": int(features.get("velocity_5m", 0.0)),
        "device_trust": int(features.get("device_trust", -1.0)),
        "network_trust": int(features.get("network_trust", -1.0)),
        "impossible_travel": int(features.get("impossible_travel", 0.0)),
        "new_device": int(features.get("new_device", 0.0)),
        "distance_km": round(float(features.get("distance_km", 0.0)), 2),
        "is_fraud": flag,
    }


def build_augmented_dataset(
    base_csv: Path, labeled_rows: list[dict[str, Any]], output: Path
) -> int:
    """Write base rows followed by labeled feedback rows to ``output``."""
    with base_csv.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or _DATASET_COLUMNS
        with output.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                writer.writerow(row)
            for row in labeled_rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
    return len(labeled_rows)


def _fingerprint(path: str | Path) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        # Dataset may live in a scratch dir cleaned after promotion.
        return "unavailable"


def retrain_and_promote(
    *,
    observations: list[Observation],
    feedback_labels: dict[str, str],
    retrainer: Retrainer,
    base_dataset: Path,
    model_name: str,
    model_dir: Path,
    registry_path: Path,
    min_labels: int = 10,
    tolerance: float = 0.01,
    version: str | None = None,
) -> dict[str, Any]:
    """Retrain on the base dataset + labeled observations and gate the promotion."""
    labeled = collect_labeled(observations, feedback_labels)
    if len(labeled) < min_labels:
        return {
            "triggered": False,
            "reason": f"only {len(labeled)} labeled observation(s) (minimum {min_labels})",
            "labeled_count": len(labeled),
        }
    resolved_version = version or f"retrain-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    scratch_dir = Path(tempfile.mkdtemp(prefix="veripay-retrain-"))
    try:
        augmented = scratch_dir / "augmented_dataset.csv"
        build_augmented_dataset(
            base_dataset, [observation_to_row(obs, flag) for obs, flag in labeled], augmented
        )
        result = retrainer.retrain(augmented, resolved_version, model_name, scratch_dir)
        outcome = promote_if_better(
            result,
            model_name=model_name,
            latest_dir=model_dir / model_name / "latest",
            registry_path=registry_path,
            tolerance=tolerance,
        )
        return {
            "triggered": True,
            "version": resolved_version,
            "gate_passed": outcome.gate_passed,
            "reason": outcome.reason,
            "metrics": outcome.metrics,
            "latest_metrics": outcome.latest_metrics,
            "labeled_count": len(labeled),
            "dataset_path": str(augmented),
        }
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


__all__ = [
    "FEATURE_COLUMNS",
    "HttpFeedbackProvider",
    "MonitorLabel",
    "Observation",
    "ObservationStore",
    "PSI_TRIGGER",
    "PromoteOutcome",
    "RetrainResult",
    "Retrainer",
    "SubprocessRetrainer",
    "WindowedObservationStore",
    "build_augmented_dataset",
    "collect_labeled",
    "drift_report",
    "feature_drift",
    "load_reference_profile",
    "observation_to_row",
    "promote_if_better",
    "psi",
    "retrain_and_promote",
]
