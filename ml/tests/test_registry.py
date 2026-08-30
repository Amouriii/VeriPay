"""Model registry tests: register, rollback, latest-version semantics."""

from __future__ import annotations

import pytest

from registry import model_registry as registry


@pytest.fixture()
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("VERIPAY_MODEL_REGISTRY", str(tmp_path / "registry.json"))
    return registry


def test_register_creates_latest(isolated_registry) -> None:
    isolated_registry.register(
        "supervised",
        "v1",
        artifact_path="ml/models/supervised/latest/model.joblib",
        metrics={"roc_auc": 0.91},
    )
    record = isolated_registry.latest("supervised")
    assert record is not None
    assert record["version"] == "v1"
    assert record["metrics"]["roc_auc"] == 0.91


def test_register_overwrites_latest_with_new_version(isolated_registry) -> None:
    isolated_registry.register("supervised", "v1")
    isolated_registry.register("supervised", "v2")
    assert isolated_registry.latest("supervised")["version"] == "v2"
    assert set(isolated_registry.all_versions("supervised")) == {"v1", "v2"}


def test_rollback_rewinds_latest(isolated_registry) -> None:
    isolated_registry.register("supervised", "v1")
    isolated_registry.register("supervised", "v2")
    rollbacked = isolated_registry.rollback("supervised", "v1")
    assert rollbacked["version"] == "v1"
    assert isolated_registry.latest("supervised")["version"] == "v1"
    # Versions are never deleted.
    assert set(isolated_registry.all_versions("supervised")) == {"v1", "v2"}


def test_rollback_unknown_version_raises(isolated_registry) -> None:
    isolated_registry.register("supervised", "v1")
    with pytest.raises(KeyError):
        isolated_registry.rollback("supervised", "v9")


def test_rollback_unknown_model_raises(isolated_registry) -> None:
    with pytest.raises(KeyError):
        isolated_registry.rollback("nope", "v1")


def test_latest_unknown_model_is_none(isolated_registry) -> None:
    assert isolated_registry.latest("ghost") is None
