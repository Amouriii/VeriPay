"""Service configuration (env-driven). PLAN §20."""

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

    # LLM investigation boundary (PLAN §20). "deterministic" is the
    # zero-dependency default; "openai_compatible" targets a local vLLM
    # (OpenAI-compatible) server and degrades to the deterministic provider
    # whenever the server is unreachable or the ``openai`` package is absent.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deterministic")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "EMPTY")  # vLLM ignores; never commit a real key
    LLM_MODEL: str = os.getenv("LLM_MODEL", "veripay-explainer")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))


settings = Settings()
