"""Service configuration (env-driven). PLAN §10, §21."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-driven configuration."""

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8000"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))

    # Model under monitoring (must match a registry model_name).
    MODEL_NAME: str = os.getenv("MODEL_NAME", "supervised")
    MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(_REPO_ROOT / "ml" / "models")))
    REGISTRY_PATH: Path = Path(
        os.getenv("MODEL_REGISTRY", str(_REPO_ROOT / "ml" / "models" / "registry.json"))
    )
    BASE_DATASET: Path = Path(
        os.getenv(
            "BASE_DATASET",
            str(_REPO_ROOT / "datasets" / "synthetic" / "transactions_labeled.csv"),
        )
    )
    REPO_ROOT: Path = Path(os.getenv("REPO_ROOT", str(_REPO_ROOT)))

    # Drift thresholds and retraining policy.
    PSI_THRESHOLD: float = float(os.getenv("PSI_THRESHOLD", "0.25"))
    MIN_DRIFT_WINDOW: int = int(os.getenv("MIN_DRIFT_WINDOW", "30"))
    MIN_LABELED_OBSERVATIONS: int = int(os.getenv("MIN_LABELED_OBSERVATIONS", "10"))
    PROMOTION_TOLERANCE: float = float(os.getenv("PROMOTION_TOLERANCE", "0.01"))
    OBSERVATION_WINDOW: int = int(os.getenv("OBSERVATION_WINDOW", "1000"))

    # Feedback-loop wiring (labels joined onto observations by transaction id).
    FEEDBACK_LOOP_URL: str = os.getenv("FEEDBACK_LOOP_URL", "http://localhost:8016")

    # Retraining: the Python interpreter used for the training subprocess.
    PYTHON: str = os.getenv("PYTHON", sys.executable)


settings = Settings()
