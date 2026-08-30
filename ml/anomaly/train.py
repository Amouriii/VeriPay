"""Train + evaluate Isolation Forest anomaly model (PLAN §11).

Unsupervised isolation of outliers in the same feature space as the supervised
model. Trains on the full (unlabeled) feature matrix, then evaluates how well
the anomaly score separates fraud from legitimate transactions on the same
stratified split used by ``ml/supervised/train.py``.

Run from the repository root (after ``pip install -e "ml[training]"``):

    python ml/anomaly/train.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from drift.profile import compute_reference_profile, save_profile
from registry.model_registry import register
from supervised.features import FEATURE_COLUMNS
from supervised.train import load_dataset, prepare_features, split_indices

DEFAULT_DATASET = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "transactions_labeled.csv"
)
DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "ml" / "models"

MODEL_NAME = "anomaly"
SPLIT_SEED = 42
MODEL_SEED = 42


def _anomaly_scores(model: IsolationForest, x: np.ndarray) -> np.ndarray:
    """Map IsolationForest decision scores to a positive anomaly magnitude."""
    return -model.decision_function(x)


def _dataset_fingerprint(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def best_threshold(y_val: np.ndarray, scores: np.ndarray) -> float:
    """Pick the anomaly-score threshold maximizing F1 on validation."""
    precisions, recalls, thresholds = precision_recall_curve(y_val, scores)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1 = 2 * precisions * recalls / np.maximum(precisions + recalls, 1e-12)
    best_index = int(np.argmax(f1))
    if best_index >= len(thresholds):
        return 0.5
    return float(thresholds[best_index])


def train(
    dataset_path: str | Path = DEFAULT_DATASET,
    model_dir: str | Path = DEFAULT_MODEL_DIR,
    *,
    n_estimators: int = 200,
    split_seed: int = SPLIT_SEED,
    version: str | None = None,
) -> dict[str, Any]:
    """Train, evaluate, and register the anomaly model.

    Returns evaluation metrics plus artifact/registry metadata.
    """
    frame = load_dataset(dataset_path)
    x, y = prepare_features(frame)
    # Same split as the supervised model for comparable metrics. Isolation
    # Forest is unsupervised: it fits on the full train+validation matrix and
    # is only *evaluated* against the held-out labels.
    idx_train, idx_val, idx_test = split_indices(y, split_seed)
    x_train, x_val, x_test = x[idx_train], x[idx_val], x[idx_test]
    y_val, y_test = y[idx_val], y[idx_test]
    fit_x = np.vstack([x_train, x_val])

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=0.05,
        random_state=MODEL_SEED,
        n_jobs=1,
    )
    model.fit(fit_x)

    scores_val = _anomaly_scores(model, x_val)
    threshold = best_threshold(y_val, scores_val)
    scores_test = _anomaly_scores(model, x_test)
    predictions = (scores_test >= threshold).astype(int)

    metrics: dict[str, float] = {
        "roc_auc": float(roc_auc_score(y_test, scores_test)),
        "pr_auc": float(average_precision_score(y_test, scores_test)),
        "precision_at_threshold": float(precision_score(y_test, predictions, zero_division=0)),
        "recall_at_threshold": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_at_threshold": float(f1_score(y_test, predictions, zero_division=0)),
        "threshold": threshold,
        "test_fraud_rate": float(y_test.mean()),
    }

    resolved_version = version or datetime.now(UTC).isoformat()
    model_path = Path(model_dir) / MODEL_NAME / "latest"
    model_path.mkdir(parents=True, exist_ok=True)
    artifact = model_path / "model.joblib"
    joblib.dump(model, artifact)
    profile_path = model_path / "reference_profile.json"
    save_profile(
        compute_reference_profile(
            frame.iloc[np.concatenate([idx_train, idx_val])],
            FEATURE_COLUMNS,
            model_name=MODEL_NAME,
            version=resolved_version,
        ),
        profile_path,
    )
    sidecar: dict[str, Any] = {
        "model_name": MODEL_NAME,
        "version": resolved_version,
        "features": FEATURE_COLUMNS,
        "metrics": metrics,
        "dataset_path": str(dataset_path),
        "dataset_fingerprint": _dataset_fingerprint(dataset_path),
        "reference_profile": str(profile_path),
    }
    (model_path / "model.json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

    record = register(
        MODEL_NAME,
        resolved_version,
        artifact_path=str(artifact),
        metrics=metrics,
        dataset_path=str(dataset_path),
        dataset_fingerprint=sidecar["dataset_fingerprint"],
        reference_profile=sidecar["reference_profile"],
    )
    return {
        "model_name": MODEL_NAME,
        "version": record["version"],
        "artifact_path": str(artifact),
        "metrics": metrics,
        "reference_profile": str(profile_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train and register the Isolation Forest anomaly model."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--version", default=None)
    args = parser.parse_args()

    result = train(
        args.dataset,
        args.model_dir,
        n_estimators=args.n_estimators,
        version=args.version,
    )
    print(f"Model {result['model_name']}@{result['version']}")
    print(f"Artifact: {result['artifact_path']}")
    for name, value in result["metrics"].items():
        print(f"  {name}: {value:.4f}")


if __name__ == "__main__":
    main()
