"""AI-value regression test: model vs rules-only baseline on the same split.

Trains the real supervised pipeline on the committed dataset, re-derives the
exact held-out test split ``train`` used (via ``split_indices``), scores with
the freshly trained artifact, and compares against the deterministic
rules-only baseline on the same rows. This pins the claim quantified in
``docs/evaluation.md``: the model flags a small fraction of transactions that
the rules would flag, at better precision.
"""

from __future__ import annotations

import joblib
from sklearn.metrics import precision_score

from supervised.baseline import evaluate_rules_only
from supervised.train import (
    DEFAULT_DATASET,
    load_dataset,
    prepare_features,
    split_indices,
    train,
)


def test_supervised_model_beats_rules_baseline_on_same_split(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VERIPAY_MODEL_REGISTRY", str(tmp_path / "registry.json"))
    model_dir = tmp_path / "models"

    # Real pipeline: committed dataset, default hyperparameters and seeds.
    result = train(DEFAULT_DATASET, model_dir)
    metrics = result["metrics"]
    assert metrics["roc_auc"] > 0.75  # sanity: the trained model separates fraud

    # Re-derive the identical held-out split the pipeline evaluated on.
    frame = load_dataset(DEFAULT_DATASET)
    x, y = prepare_features(frame)
    _, _, idx_test = split_indices(y)
    x_test = x[idx_test]
    y_test = y[idx_test]
    test_frame = frame.iloc[idx_test]

    model = joblib.load(model_dir / "supervised" / "latest" / "model.joblib")
    proba = model.predict_proba(x_test)[:, 1]
    model_predictions = (proba >= metrics["threshold"]).astype(int)

    model_flag_rate = float(model_predictions.mean())
    model_precision = float(precision_score(y_test, model_predictions, zero_division=0))
    baseline = evaluate_rules_only(test_frame, y_test)

    # The AI-value claim: the model flags less than half of what the rules
    # flag (real margin is ~14x) and does so at strictly better precision.
    assert 0.0 <= model_flag_rate <= 1.0
    assert model_flag_rate < baseline["flag_rate"] / 2
    assert model_precision > baseline["precision"]

    # Guard against a degenerate baseline (must actually flag a large share).
    assert baseline["flag_rate"] > 0.2
