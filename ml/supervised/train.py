"""Train + evaluate XGBoost supervised fraud model (PLAN §10, §20).

Pipeline: load the labeled synthetic dataset -> stratified 70/15/15 split ->
train XGBoost with early stopping on validation -> evaluate on the held-out
test set (ROC-AUC, PR-AUC, precision/recall/F1 at the validation-optimal
threshold) -> persist the artifact + sidecar metadata -> register the version.

Run from the repository root (after ``pip install -e "ml[training]"``):

    python ml/supervised/train.py
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
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from drift.profile import compute_reference_profile, save_profile
from registry.model_registry import register
from supervised.features import FEATURE_COLUMNS

DEFAULT_DATASET = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "transactions_labeled.csv"
)
DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "ml" / "models"

MODEL_NAME = "supervised"
SPLIT_SEED = 42
MODEL_SEED = 42


def load_dataset(path: str | Path = DEFAULT_DATASET) -> pd.DataFrame:
    """Load and validate the labeled transaction dataset."""
    frame = pd.read_csv(path)
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset missing feature columns: {missing}")
    if "is_fraud" not in frame.columns:
        raise ValueError("Dataset is missing the 'is_fraud' label column")
    if frame[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Dataset contains missing feature values")
    if not set(frame["is_fraud"].unique()).issubset({0, 1}):
        raise ValueError("Label column must be binary (0/1)")
    return frame


def prepare_features(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return the ordered model matrix ``x`` and label vector ``y``."""
    x = frame[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y = frame["is_fraud"].to_numpy(dtype=np.int64)
    return x, y


def split_indices(
    y: np.ndarray, split_seed: int = SPLIT_SEED
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stratified 70/15/15 index split (single source of truth for train and tests).

    Returns ``(train_idx, val_idx, test_idx)`` so evaluation code (e.g., the
    rules-only baseline in ``ml/tests/test_baseline.py``) can re-derive the
    exact held-out rows ``train`` evaluated on.
    """
    idx = np.arange(len(y))
    idx_train, idx_test = train_test_split(idx, test_size=0.30, stratify=y, random_state=split_seed)
    idx_val, idx_test = train_test_split(
        idx_test, test_size=0.50, stratify=y[idx_test], random_state=split_seed
    )
    return idx_train, idx_val, idx_test


def split_data(
    x: np.ndarray, y: np.ndarray, split_seed: int = SPLIT_SEED
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Stratified 70/15/15 train/validation/test split."""
    idx_train, idx_val, idx_test = split_indices(y, split_seed)
    return (
        x[idx_train],
        x[idx_val],
        x[idx_test],
        y[idx_train],
        y[idx_val],
        y[idx_test],
    )


def _dataset_fingerprint(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def best_threshold(y_val: np.ndarray, proba: np.ndarray) -> float:
    """Pick the threshold maximizing F1 on the validation set."""
    precisions, recalls, thresholds = precision_recall_curve(y_val, proba)
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
    n_estimators: int = 80,
    max_depth: int = 4,
    split_seed: int = SPLIT_SEED,
    version: str | None = None,
) -> dict[str, Any]:
    """Train, evaluate, and register the supervised model.

    Returns evaluation metrics plus artifact/registry metadata.
    """
    frame = load_dataset(dataset_path)
    x, y = prepare_features(frame)
    idx_train, idx_val, idx_test = split_indices(y, split_seed)
    x_train, x_val, x_test = x[idx_train], x[idx_val], x[idx_test]
    y_train, y_val, y_test = y[idx_train], y[idx_val], y[idx_test]

    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=MODEL_SEED,
        n_jobs=1,
        verbosity=0,
    )
    # No early stopping: the artifact must predict identically to the model
    # that was evaluated (served == evaluated), so the persisted model and the
    # reported metrics always agree.
    model.fit(x_train, y_train)

    proba_val = model.predict_proba(x_val)[:, 1]
    threshold = best_threshold(y_val, proba_val)
    proba_test = model.predict_proba(x_test)[:, 1]
    predictions = (proba_test >= threshold).astype(int)

    metrics: dict[str, float] = {
        "roc_auc": float(roc_auc_score(y_test, proba_test)),
        "pr_auc": float(average_precision_score(y_test, proba_test)),
        "precision_at_threshold": float(precision_score(y_test, predictions, zero_division=0)),
        "recall_at_threshold": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_at_threshold": float(f1_score(y_test, predictions, zero_division=0)),
        "threshold": threshold,
        "test_fraud_rate": float(y_test.mean()),
        "n_estimators": float(n_estimators),
    }

    resolved_version = version or datetime.now(UTC).isoformat()
    model_path = Path(model_dir) / MODEL_NAME / "latest"
    model_path.mkdir(parents=True, exist_ok=True)
    artifact = model_path / "model.joblib"
    joblib.dump(model, artifact)
    profile_path = model_path / "reference_profile.json"
    save_profile(
        compute_reference_profile(
            frame.iloc[idx_train], FEATURE_COLUMNS, model_name=MODEL_NAME, version=resolved_version
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
        description="Train and register the XGBoost supervised fraud model."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--n-estimators", type=int, default=80)
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
