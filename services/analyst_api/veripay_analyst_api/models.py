"""Wire models for the analyst API composite service.

The response shapes mirror the analyst console contract (``web/src/types`` and
the ``system-architecture.md`` decision vocabulary) so the dashboard can be
pointed at this backend without re-mapping fields.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator
from veripay_common.enums import DecisionAction, RiskBand, RiskTier

# Bundle returned by the graph engine and forwarded to the dashboard.
NetworkContext = dict[str, Any]


class Decision(StrEnum):
    BLOCK = "BLOCK"
    REVIEW_STEALTH = "REVIEW_STEALTH"
    REVIEW_UNUSUAL = "REVIEW_UNUSUAL"
    PASS = "PASS"


class RiskLevel(StrEnum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class TransactionInput(BaseModel):
    transaction_id: str = Field(min_length=1)
    cc_num: int = Field(ge=1)
    customer_id: str | None = None
    # Amount in major currency units (e.g. dollars).
    amount: float = Field(ge=0)
    merchant: str = Field(min_length=1)
    category: str = ""
    timestamp: datetime
    location: GeoPoint | None = None
    merchant_location: GeoPoint | None = None
    # Optional raw signals used to derive the model feature set when a caller
    # does not submit pre-computed features.
    mcc_risk: float = Field(default=0.5, ge=0, le=1)
    device_trust: float = Field(default=-1.0, ge=-1, le=1)
    network_trust: float = Field(default=-1.0, ge=-1, le=1)
    new_device: float = Field(default=0.0, ge=0, le=1)
    impossible_travel: float = Field(default=0.0, ge=0, le=1)
    # Optional pre-computed model features (bypass the causal feature builder).
    model_features: dict[str, float] | None = None


class ScoreRequest(BaseModel):
    transaction: TransactionInput


class FeatureRow(BaseModel):
    name: str
    value: str
    customer_baseline: str = "—"
    unit: str = ""


class ContributorShare(BaseModel):
    feature: str
    contribution_pct: float = Field(ge=0, le=100)


class XgbContribution(BaseModel):
    feature: str
    shap_value: float


class RecentTransaction(BaseModel):
    time: str
    amount: float
    merchant: str
    category: str
    location: str


class Adjustment(BaseModel):
    kind: str  # "feedback" | "drift"
    effect: str  # trust_boost | heightened_alert | gradual_drift | sudden_drift
    description: str
    anomaly_factor: float = 1.0
    fraud_add: float = 0.0


class ScoreResponse(BaseModel):
    transaction_id: str
    cc_num: int
    decision: Decision
    risk_level: RiskLevel
    verification_action: str
    action: DecisionAction
    risk_band: RiskBand
    risk_tier: RiskTier
    fused_risk_score: int = Field(ge=0, le=100)
    fraud_probability: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    raw_fraud_probability: float = Field(ge=0, le=1)
    raw_anomaly_score: float = Field(ge=0, le=1)
    model_available: bool
    model_versions: dict[str, str] = Field(default_factory=dict)
    model_fallbacks: list[str] = Field(default_factory=list)
    feature_mode: str = "basic"  # basic | rich
    adjustments: list[Adjustment] = Field(default_factory=list)
    features: list[FeatureRow] = Field(default_factory=list)
    features16: list[FeatureRow] = Field(default_factory=list)
    anomaly_top_contributors: list[ContributorShare] = Field(default_factory=list)
    xgboost_feature_contributions: list[XgbContribution] = Field(default_factory=list)
    recent_transactions: list[RecentTransaction] = Field(default_factory=list)
    # Network (graph) scoring axis — the fourth component (PLAN §12). Optional
    # with defaults so the field is backwards-compatible with older payloads.
    network_risk_score: float = Field(ge=0, le=1, default=0.0)
    network_available: bool = False
    network_findings: list[str] = Field(default_factory=list)
    network_ego: dict[str, Any] | None = None
    network_community: dict[str, Any] | None = None


class CaseReport(BaseModel):
    verdict: str
    evidence: list[str] = Field(default_factory=list)
    pattern_match: str
    recommended_action: str
    crosschecked: bool = False
    hallucination_flagged: bool = False


class ExplainResponse(BaseModel):
    transaction_id: str
    cc_num: int
    risk_level: RiskLevel
    verification_action: str
    case_report: CaseReport
    score: ScoreResponse


class Baseline(BaseModel):
    median_amount: str
    typical_hours: str
    home_location: str
    distinct_merchants: int
    daily_txn_count: int


class DriftInfo(BaseModel):
    kind: str  # "gradual" | "sudden"
    severity: str  # "yellow" | "red"
    message: str


class TrustStatus(BaseModel):
    level: str  # "normal" | "boosted" | "alert"
    message: str


class CustomerProfileResponse(BaseModel):
    cc_num: int
    long_term_baseline: Baseline
    recent_behavior: Baseline
    drift_detected: DriftInfo | None = None
    trust_status: TrustStatus


class AlertItem(BaseModel):
    transaction_id: str
    cc_num: int
    customer_name: str
    amount: float
    currency: str = "USD"
    merchant: str
    time: str
    decision: Decision
    risk_level: RiskLevel
    fraud_probability: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)


class AnalystScoreRequest(BaseModel):
    """The analyst console sends either a new transaction to score, or a
    lookup of an already-scored result (by transaction_id or cc_num)."""

    transaction: TransactionInput | None = None
    transaction_id: str | None = None
    cc_num: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_target(self) -> AnalystScoreRequest:
        if self.transaction is None and not self.transaction_id and self.cc_num is None:
            raise ValueError("Provide a transaction, transaction_id, or cc_num")
        return self


class FeedbackInput(BaseModel):
    transaction_id: str = Field(min_length=1)
    cc_num: int = Field(ge=1)
    analyst_decision: str = Field(
        min_length=1
    )  # confirmed_fraud | false_alarm | customer_confirmed_legitimate
    analyst_id: str = "analyst"
    notes: str = ""
    decision: Decision = Decision.PASS


class FeedbackResult(BaseModel):
    status: str
    transaction_id: str
    recorded: bool = True
    note: str = ""


class FeedbackByDecisionRow(BaseModel):
    decision: Decision
    total_reviewed: int
    confirmed_fraud: int
    false_alarm: int
    fraud_rate: float = Field(ge=0, le=1)


class FeedbackStats(BaseModel):
    total_feedback: int
    confirmed_fraud: int
    false_alarm: int
    customer_confirmed_legitimate: int
    false_positive_rate: float = Field(ge=0, le=1)
    feedback_by_decision: list[FeedbackByDecisionRow] = Field(default_factory=list)


class RetrainResponse(BaseModel):
    status: str
    message: str
    new_version: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    models_loaded: list[str] = Field(default_factory=list)
    model_versions: dict[str, str] = Field(default_factory=dict)
    upstream: dict[str, str] = Field(default_factory=dict)


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "Adjustment",
    "AlertItem",
    "AnalystScoreRequest",
    "Baseline",
    "CaseReport",
    "ContributorShare",
    "CustomerProfileResponse",
    "Decision",
    "DriftInfo",
    "ExplainResponse",
    "FeedbackByDecisionRow",
    "FeedbackInput",
    "FeedbackResult",
    "FeedbackStats",
    "FeatureRow",
    "GeoPoint",
    "HealthResponse",
    "RecentTransaction",
    "RetrainResponse",
    "RiskLevel",
    "ScoreRequest",
    "ScoreResponse",
    "TransactionInput",
    "TrustStatus",
    "XgbContribution",
    "_utcnow",
    "NetworkContext",
]
