"""Anomaly pipeline tests: training, artifact persistence, held-out separation."""

from __future__ import annotations

from anomaly.train import train
from datasets.generate_synthetic import generate


def test_anomaly_train_end_to_end(tmp_path, monkeypatch) -> None:
    dataset = tmp_path / "small.csv"
    generate(n_rows=2_000, seed=7).to_csv(dataset, index=False)
    model_dir = tmp_path / "models"
    monkeypatch.setenv("VERIPAY_MODEL_REGISTRY", str(tmp_path / "registry.json"))

    result = train(dataset, model_dir, n_estimators=60, version="test-v1")

    assert result["model_name"] == "anomaly"
    assert result["version"] == "test-v1"
    assert (model_dir / "anomaly" / "latest" / "model.joblib").exists()
    assert (model_dir / "anomaly" / "latest" / "model.json").exists()
    metrics = result["metrics"]
    # Unsupervised, but the synthetic fraud is structurally unusual: the
    # anomaly score must still separate it from the bulk distribution.
    assert metrics["roc_auc"] > 0.65
    assert 0.0 <= metrics["precision_at_threshold"] <= 1.0
    assert 0.0 <= metrics["recall_at_threshold"] <= 1.0
