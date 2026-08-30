"""Rules-only baseline for AI-value evaluation (PLAN §10, §13).

Deterministic hard-rule flagging mirrors the rule engine's most common
triggers (velocity, untrusted device/network, impossible travel, high-risk
MCC) with no learned component. Comparing the supervised model against this
baseline on the *same* held-out split quantifies what the AI adds — see
``docs/evaluation.md`` and ``ml/tests/test_baseline.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score

# Thresholds mirror the deterministic rule engine defaults in
# ``services/rule_engine`` (velocity limit, zero-trust, MCC risk band).
VELOCITY_LIMIT_5M = 5
HIGH_RISK_MCC = 0.7


def rules_only_predictions(frame: pd.DataFrame) -> np.ndarray:
    """Flag rows where any hard rule fires (0/1 array, one entry per row)."""
    flag = (
        (frame["velocity_5m"] > VELOCITY_LIMIT_5M)
        | (frame["device_trust"] == 0)
        | (frame["network_trust"] == 0)
        | (frame["impossible_travel"] == 1)
        | (frame["mcc_risk"] >= HIGH_RISK_MCC)
    )
    return flag.astype(int).to_numpy()


def evaluate_rules_only(frame: pd.DataFrame, labels: np.ndarray) -> dict[str, float]:
    """Evaluate the rules-only baseline on a labeled frame."""
    predictions = rules_only_predictions(frame)
    return {
        "flag_rate": float(predictions.mean()),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
    }


__all__ = ["evaluate_rules_only", "rules_only_predictions"]
