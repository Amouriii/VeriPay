"""Service configuration (env-driven). PLAN §19.

Decision cost parameters (``CostModel`` defaults) are governed configuration:
business owners calibrate them here via environment variables rather than
editing code. All values are in minor currency units unless noted.
"""

from __future__ import annotations

import os


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    """Environment-driven configuration. PLAN §19."""

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8000"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))

    # Downstream service endpoints (gRPC). Filled in as services are wired.
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_DSN: str = os.getenv(
        "POSTGRES_DSN", "postgresql://veripay:veripay@localhost:5432/veripay"
    )

    # ---- Governed cost model (CostModel defaults) ----
    # Expected-loss inputs; values are minor currency units. Business owners
    # calibrate these via environment variables, not code changes.
    COST_FRAUD_LOSS_MINOR: float = _env_float("COST_FRAUD_LOSS_MINOR", 10_000)
    COST_FALSE_DECLINE_LOSS_MINOR: float = _env_float("COST_FALSE_DECLINE_LOSS_MINOR", 2_500)
    COST_MONITOR_COST_MINOR: float = _env_float("COST_MONITOR_COST_MINOR", 400)
    COST_CHALLENGE_COST_MINOR: float = _env_float("COST_CHALLENGE_COST_MINOR", 60)
    COST_REVIEW_COST_MINOR: float = _env_float("COST_REVIEW_COST_MINOR", 150)
    COST_REVERSAL_COST_MINOR: float = _env_float("COST_REVERSAL_COST_MINOR", 100)
    COST_MONITOR_RESIDUAL_FRAUD_RATE: float = _env_float("COST_MONITOR_RESIDUAL_FRAUD_RATE", 0.85)
    COST_CHALLENGE_RESIDUAL_FRAUD_RATE: float = _env_float(
        "COST_CHALLENGE_RESIDUAL_FRAUD_RATE", 0.20
    )
    COST_REVIEW_RESIDUAL_FRAUD_RATE: float = _env_float("COST_REVIEW_RESIDUAL_FRAUD_RATE", 0.35)
    COST_REVERSAL_RESIDUAL_FRAUD_RATE: float = _env_float("COST_REVERSAL_RESIDUAL_FRAUD_RATE", 0.05)

    def cost_model(self):
        """Build a CostModel from governed env configuration."""
        from veripay_decision_engine.service import CostModel

        return CostModel(
            fraud_loss_minor=self.COST_FRAUD_LOSS_MINOR,
            false_decline_loss_minor=self.COST_FALSE_DECLINE_LOSS_MINOR,
            monitor_cost_minor=self.COST_MONITOR_COST_MINOR,
            challenge_cost_minor=self.COST_CHALLENGE_COST_MINOR,
            review_cost_minor=self.COST_REVIEW_COST_MINOR,
            reversal_cost_minor=self.COST_REVERSAL_COST_MINOR,
            monitor_residual_fraud_rate=self.COST_MONITOR_RESIDUAL_FRAUD_RATE,
            challenge_residual_fraud_rate=self.COST_CHALLENGE_RESIDUAL_FRAUD_RATE,
            review_residual_fraud_rate=self.COST_REVIEW_RESIDUAL_FRAUD_RATE,
            reversal_residual_fraud_rate=self.COST_REVERSAL_RESIDUAL_FRAUD_RATE,
        )


settings = Settings()
