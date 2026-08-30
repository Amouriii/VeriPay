"""Service configuration (env-driven). Analyst API composite boundary."""

from __future__ import annotations

import os


class Settings:
    """Environment-driven configuration for the analyst API composite.

    Every downstream dependency is injectable by URL so the service can be
    pointed at locally running containers, deployed endpoints, or (in tests)
    deterministic fakes.
    """

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "8000"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))

    # Feature engine mode: "basic" (repo columns from raw signals) or "rich"
    # (the architecture's 16 causal-sequence features, mapped onto the model
    # vector). Config-driven so it can be toggled without code changes.
    FEATURE_MODE: str = os.getenv("FEATURE_MODE", "basic").strip().lower()

    @property
    def use_rich_features(self) -> bool:
        return self.FEATURE_MODE == "rich"

    # Downstream service endpoints (REST).
    SUPERVISED_URL: str = os.getenv("VERIPAY_SUPERVISED_URL", "http://localhost:8006")
    ANOMALY_URL: str = os.getenv("VERIPAY_ANOMALY_URL", "http://localhost:8007")
    RISK_FUSION_URL: str = os.getenv("VERIPAY_RISK_FUSION_URL", "http://localhost:8012")
    DECISION_URL: str = os.getenv("VERIPAY_DECISION_URL", "http://localhost:8013")
    INVESTIGATION_URL: str = os.getenv("VERIPAY_INVESTIGATION_URL", "http://localhost:8014")
    FEEDBACK_URL: str = os.getenv("VERIPAY_FEEDBACK_URL", "http://localhost:8016")
    MODEL_MONITOR_URL: str = os.getenv("VERIPAY_MODEL_MONITOR_URL", "http://localhost:8025")
    GRAPH_URL: str = os.getenv("VERIPAY_GRAPH_URL", "http://localhost:8008")

    # Network (graph) scoring axis — fourth fusion component (PLAN §12).
    # When the graph engine is unavailable, fusion redistributes this weight
    # across the available supervised/anomaly components, so the pipeline
    # degrades to the current two-axis behaviour.
    NETWORK_FUSION_WEIGHT: float = float(os.getenv("NETWORK_FUSION_WEIGHT", "0.2"))

    # Per-transaction adjustment tuning (documented in the architecture).
    TRUST_BOOST_FACTOR: float = float(os.getenv("TRUST_BOOST_FACTOR", "0.7"))
    HEIGHTENED_ALERT_ADD: float = float(os.getenv("HEIGHTENED_ALERT_ADD", "0.1"))
    GRADUAL_DRIFT_FACTOR: float = float(os.getenv("GRADUAL_DRIFT_FACTOR", "0.6"))
    SUDDEN_DRIFT_FACTOR: float = float(os.getenv("SUDDEN_DRIFT_FACTOR", "1.2"))

    # Feedback trust-boost window (last N feedbacks on this customer).
    TRUST_BOOST_WINDOW: int = int(os.getenv("TRUST_BOOST_WINDOW", "3"))

    # Four-quadrant refinement thresholds (architecture §6). The fused
    # 0-100 score cannot distinguish "unusual but legitimate" from
    # "normal-looking fraud" — the two raw axes can. When the engine would
    # BLOCK but the fraud probability is high while the anomaly score is low,
    # the transaction matches known fraud while looking normal → REVIEW_STEALTH.
    FRAUD_QUADRANT_THRESHOLD: float = float(os.getenv("FRAUD_QUADRANT_THRESHOLD", "0.5"))
    ANOMALY_QUADRANT_THRESHOLD: float = float(os.getenv("ANOMALY_QUADRANT_THRESHOLD", "0.5"))


settings = Settings()
