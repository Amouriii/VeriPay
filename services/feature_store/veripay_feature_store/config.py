"""Service configuration (env-driven). PLAN §8,§9."""
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
    POSTGRES_DSN: str = os.getenv("POSTGRES_DSN", "postgresql://veripay:veripay@localhost:5432/veripay")


settings = Settings()
