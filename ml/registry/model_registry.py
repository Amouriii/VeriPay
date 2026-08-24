"""Model versioning + rollback API (PLAN §10 governance).

Models are versioned with training dataset snapshots and strict rollback.
"""
from __future__ import annotations


def register(model_name: str, version: str) -> None:
    """Register a new model version. Stubbed."""
    raise NotImplementedError


def rollback(model_name: str, to_version: str) -> None:
    """Roll back to a previous model version. Stubbed."""
    raise NotImplementedError
