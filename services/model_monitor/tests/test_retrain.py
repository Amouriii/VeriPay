"""Retraining tests: label merge, dataset augmentation, promotion gate, orchestration."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from veripay_model_monitor.service import (
    MonitorLabel,
    Observation,
    RetrainResult,
    build_augmented_dataset,
    collect_labeled,
    observation_to_row,
    promote_if_better,
    retrain_and_promote,
)

BASE_CSV = (
    "transaction_id,amount_minor,amount_log,mcc,mcc_risk,hour_of_day,weekend,"
    "velocity_5m,device_trust,network_trust,impossible_travel,new_device,"
    "distance_km,is_fraud\n"
    "tx_base_1,4999,8.5,5712,0.25,14,0,1,1,1,0,0,3.0,0\n"
    "tx_base_2,120000,11.7,6011,0.85,2,1,9,0,0,1,1,900.0,1\n"
)


def _observation(tx: str, label: MonitorLabel | None = None) -> Observation:
    return Observation(
        transaction_id=tx,
        features={
            "amount_log": 9.2,
            "mcc_risk": 0.55,
            "velocity_5m": 3.0,
            "device_trust": 1.0,
            "network_trust": 1.0,
            "impossible_travel": 0.0,
            "new_device": 0.0,
            "hour_of_day": 12.0,
            "weekend": 0.0,
            "distance_km": 5.0,
        },
        score=40.0,
        label=label,
    )


def _champion_registry(path: Path, roc_auc: float = 0.93) -> None:
    path.write_text(
        json.dumps(
            {
                "models": {
                    "supervised": {
                        "latest": "champion",
                        "versions": {
                            "champion": {
                                "version": "champion",
                                "metrics": {"roc_auc": roc_auc, "pr_auc": 0.5},
                            }
                        },
                    }
                }
            }
        )
    )


class _FakeRetrainer:
    """Writes a scratch artifact tree and returns the given metrics."""

    def __init__(self, metrics: dict[str, float]) -> None:
        self.metrics = metrics
        self.calls: list[tuple[Path, str]] = []
        self.dataset_contents: dict[str, str] = {}

    def retrain(self, dataset_path, version, model_name, scratch_dir) -> RetrainResult:
        self.calls.append((Path(dataset_path), version))
        try:
            self.dataset_contents[version] = Path(dataset_path).read_text()
        except FileNotFoundError:
            self.dataset_contents[version] = ""
        latest = Path(scratch_dir) / "models" / model_name / "latest"
        latest.mkdir(parents=True)
        (latest / "model.joblib").write_bytes(b"artifact")
        (latest / "reference_profile.json").write_text('{"features": {}}')
        (latest / "model.json").write_text(
            json.dumps(
                {
                    "model_name": model_name,
                    "version": version,
                    "metrics": self.metrics,
                    "reference_profile": str(latest / "reference_profile.json"),
                }
            )
        )
        return RetrainResult(
            version=version,
            metrics=self.metrics,
            scratch_dir=str(Path(scratch_dir) / "models"),
            dataset_path=str(dataset_path),
        )


def test_observation_to_row_inverse_transforms() -> None:
    observation = Observation(
        transaction_id="tx_fb_1",
        features={
            "amount_log": 9.2,
            "mcc_risk": 0.55,
            "velocity_5m": 3.0,
            "device_trust": 1.0,
            "network_trust": 1.0,
            "impossible_travel": 0.0,
            "new_device": 0.0,
            "hour_of_day": 12.0,
            "weekend": 0.0,
            "distance_km": 5.0,
        },
        score=40.0,
    )
    row = observation_to_row(observation, flag=1)
    assert row["transaction_id"] == "tx_fb_1"
    assert row["is_fraud"] == 1
    assert row["amount_minor"] == round(__import__("math").expm1(9.2))
    assert row["mcc"] in {4814, 5812}  # nearest to mcc_risk 0.55
    assert row["device_trust"] == 1


def test_build_augmented_dataset(tmp_path) -> None:
    base = tmp_path / "base.csv"
    base.write_text(BASE_CSV)
    output = tmp_path / "augmented.csv"
    rows = [observation_to_row(_observation("tx_fb_1", MonitorLabel.CONFIRMED_FRAUD), 1)]
    added = build_augmented_dataset(base, rows, output)
    assert added == 1
    with output.open(newline="") as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == 3
    assert records[-1]["transaction_id"] == "tx_fb_1"
    assert records[-1]["is_fraud"] == "1"


def test_collect_labeled_prefers_feedback_labels() -> None:
    observations = [
        _observation("tx_a", MonitorLabel.CONFIRMED_FRAUD),
        _observation("tx_b", MonitorLabel.LEGITIMATE),
        _observation("tx_c"),  # no local label, feedback supplies it
        _observation("tx_d"),  # no label anywhere -> excluded
    ]
    feedback = {"tx_c": "CONFIRMED_FRAUD"}
    labeled = collect_labeled(observations, feedback)
    flags = {observation.transaction_id: flag for observation, flag in labeled}
    assert len(labeled) == 3
    assert flags["tx_a"] == 1
    assert flags["tx_b"] == 0
    assert flags["tx_c"] == 1


def test_promote_gate_rejects_worse_model(tmp_path) -> None:
    registry = tmp_path / "registry.json"
    _champion_registry(registry, roc_auc=0.93)
    latest_dir = tmp_path / "models" / "supervised" / "latest"
    retrainer = _FakeRetrainer({"roc_auc": 0.80, "pr_auc": 0.4})
    result = retrainer.retrain(
        tmp_path / "d.csv", "retrain-bad", "supervised", tmp_path / "scratch"
    )

    outcome = promote_if_better(
        result, model_name="supervised", latest_dir=latest_dir, registry_path=registry
    )
    assert outcome.gate_passed is False
    assert not latest_dir.exists()  # nothing promoted
    payload = json.loads(registry.read_text())
    assert payload["models"]["supervised"]["latest"] == "champion"


def test_promote_gate_promotes_better_model(tmp_path) -> None:
    registry = tmp_path / "registry.json"
    _champion_registry(registry, roc_auc=0.90)
    latest_dir = tmp_path / "models" / "supervised" / "latest"
    retrainer = _FakeRetrainer({"roc_auc": 0.95, "pr_auc": 0.6})
    result = retrainer.retrain(
        tmp_path / "d.csv", "retrain-good", "supervised", tmp_path / "scratch"
    )

    outcome = promote_if_better(
        result, model_name="supervised", latest_dir=latest_dir, registry_path=registry
    )
    assert outcome.gate_passed is True
    assert (latest_dir / "model.joblib").exists()
    payload = json.loads(registry.read_text())
    assert payload["models"]["supervised"]["latest"] == "retrain-good"


def test_retrain_and_promote_end_to_end(tmp_path) -> None:
    base = tmp_path / "base.csv"
    base.write_text(BASE_CSV)
    registry = tmp_path / "registry.json"
    _champion_registry(registry, roc_auc=0.90)
    model_dir = tmp_path / "models"
    observations = [_observation(f"tx_fb_{i}", MonitorLabel.CONFIRMED_FRAUD) for i in range(12)]
    retrainer = _FakeRetrainer({"roc_auc": 0.95, "pr_auc": 0.6})

    result = retrain_and_promote(
        observations=observations,
        feedback_labels={},
        retrainer=retrainer,
        base_dataset=base,
        model_name="supervised",
        model_dir=model_dir,
        registry_path=registry,
        min_labels=10,
        version="retrain-e2e",
    )
    assert result["triggered"] is True
    assert result["gate_passed"] is True
    assert result["version"] == "retrain-e2e"
    assert result["labeled_count"] == 12
    # The retrainer received the augmented dataset (base + feedback rows).
    content = retrainer.dataset_contents["retrain-e2e"]
    records = list(csv.DictReader(content.splitlines()))
    assert len(records) == 14  # 2 base + 12 feedback
    assert json.loads(registry.read_text())["models"]["supervised"]["latest"] == "retrain-e2e"


def test_retrain_requires_minimum_labels(tmp_path) -> None:
    base = tmp_path / "base.csv"
    base.write_text(BASE_CSV)
    registry = tmp_path / "registry.json"
    _champion_registry(registry)
    result = retrain_and_promote(
        observations=[_observation("tx_fb_1", MonitorLabel.CONFIRMED_FRAUD)],
        feedback_labels={},
        retrainer=_FakeRetrainer({"roc_auc": 0.9}),
        base_dataset=base,
        model_name="supervised",
        model_dir=tmp_path / "models",
        registry_path=registry,
        min_labels=10,
    )
    assert result["triggered"] is False
    assert "minimum 10" in result["reason"]
