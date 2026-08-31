"""Service configuration (env-driven). PLAN §5,§6.1."""

from __future__ import annotations

import os


class Settings:
    """Environment-driven configuration. Stubbed; replace with pydantic-settings."""

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8000"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))

    # Downstream service endpoints (gRPC). Filled in as services are wired.
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_DSN: str = os.getenv(
        "POSTGRES_DSN", "postgresql://veripay:veripay@localhost:5432/veripay"
    )

    # Optional ML-first downstream endpoints. Empty values keep the legacy
    # ingress path active when the services are not deployed.
    SUPERVISED_URL: str = os.getenv("VERIPAY_SUPERVISED_URL", "")
    ANOMALY_URL: str = os.getenv("VERIPAY_ANOMALY_URL", "")
    RISK_FUSION_URL: str = os.getenv("VERIPAY_RISK_FUSION_URL", "")
    DECISION_URL: str = os.getenv("VERIPAY_DECISION_URL", "")
    ML_TIMEOUT_SECONDS: float = float(os.getenv("ML_TIMEOUT_SECONDS", "1.5"))

    # System log encryption. Logs are encrypted before emission when a key is
    # configured; the key is a 32-byte URL-safe base64 Fernet key.
    SYSTEM_LOG_KEY: str = os.getenv("SYSTEM_LOG_KEY", "")
    SYSTEM_LOG_SALT: str = os.getenv("SYSTEM_LOG_SALT", "veripay-ingress")


settings = Settings()
