"""Service configuration (env-driven). PLAN §12."""

from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Environment-driven configuration. Stubbed; replace with pydantic-settings."""

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8008"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))

    # Downstream service endpoints (gRPC). Filled in as services are wired.
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    POSTGRES_DSN: str = os.getenv(
        "POSTGRES_DSN", "postgresql://veripay:veripay@localhost:5432/veripay"
    )

    # Network risk window: only consider transactions within this many days
    # of the customer's most recent activity when computing graph features.
    NETWORK_WINDOW_DAYS: int = int(os.getenv("NETWORK_WINDOW_DAYS", "30"))

    # Backfill the graph store at startup from the labeled dataset so every
    # customer's full merchant history is present, not just transactions that
    # flowed through the analyst API. Empty/unset disables backfill. The path
    # points at the same CSV used to train the supervised/anomaly models.
    GRAPH_SEED_CSV: str = os.getenv(
        "VERIPAY_GRAPH_SEED_CSV",
        str(
            Path(__file__).resolve().parents[3]
            / "datasets"
            / "synthetic"
            / "transactions_labeled.csv"
        ),
    )


settings = Settings()
