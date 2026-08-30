"""Supervised pipeline tests: generator determinism, feature prep, training metrics."""

from __future__ import annotations

import pytest

from datasets.generate_synthetic import generate
from supervised.features import FEATURE_COLUMNS
from supervised.train import load_dataset, prepare_features, train


def test_generator_is_deterministic() -> None:
    first = generate(n_rows=500, seed=42)
    second = generate(n_rows=500, seed=42)
    assert first.equals(second)
    assert first["is_fraud"].mean() > 0.0  # labels exist


def test_generator_columns_and_label_rate(tmp_path) -> None:
    frame = generate(n_rows=2_000, seed=7)
    for column in FEATURE_COLUMNS + ["transaction_id", "is_fraud"]:
        assert column in frame.columns
    assert 0.01 <= frame["is_fraud"].mean() <= 0.10


def test_prepare_features_shape() -> None:
    frame = generate(n_rows=100, seed=7)
    x, y = prepare_features(frame)
    assert x.shape == (100, len(FEATURE_COLUMNS))
    assert y.shape == (100,)


def test_load_dataset_rejects_missing_columns(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    generate(n_rows=10, seed=7).drop(columns=["is_fraud"]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="is_fraud"):
        load_dataset(path)


def test_train_end_to_end_produces_model_and_metrics(tmp_path, monkeypatch) -> None:
    dataset = tmp_path / "small.csv"
    generate(n_rows=2_000, seed=7).to_csv(dataset, index=False)
    model_dir = tmp_path / "models"
    monkeypatch.setenv("VERIPAY_MODEL_REGISTRY", str(tmp_path / "registry.json"))

    result = train(dataset, model_dir, n_estimators=60, version="test-v1")

    assert result["model_name"] == "supervised"
    assert result["version"] == "test-v1"
    assert (model_dir / "supervised" / "latest" / "model.joblib").exists()
    assert (model_dir / "supervised" / "latest" / "model.json").exists()
    metrics = result["metrics"]
    # The synthetic signal is strong: held-out separation must be high.
    assert metrics["roc_auc"] > 0.75
    assert 0.0 <= metrics["precision_at_threshold"] <= 1.0
    assert 0.0 <= metrics["recall_at_threshold"] <= 1.0
    assert 0.0 < metrics["threshold"] <= 1.0
    import json

    sidecar = json.loads((model_dir / "supervised" / "latest" / "model.json").read_text())
    assert sidecar["metrics"]["roc_auc"] == metrics["roc_auc"]
    assert sidecar["dataset_fingerprint"]
