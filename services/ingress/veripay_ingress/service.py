"""Transaction ingress domain logic with blueprint rail-aware authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Protocol
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from veripay_common.enums import (
    Channel,
    DecisionAction,
    ExplanationMode,
    Mti,
    PaymentRail,
    ProcessingPath,
    RiskBand,
    RiskTier,
)
from veripay_common.risk_policy import (
    band_for_tier,
    policy_for_tier,
    processing_path_for_rail,
    tier_for_score,
)


class Transaction(BaseModel):
    """Canonical transaction payload accepted by the ingress API.

    The rail fields are optional for compatibility with clients using the
    original contract. New adapters should always send ``payment_rail``.
    """

    model_config = ConfigDict(use_enum_values=True)

    transaction_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant_id: str | None = None
    mti: Mti = Mti.AUTHORIZATION_REQUEST
    channel: Channel = Channel.CARD_NOT_PRESENT
    payment_rail: PaymentRail | None = None
    processing_path: ProcessingPath | None = None


class ComponentScore(BaseModel):
    component: str
    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    available: bool = True
    reason_code: str | None = None


class RiskScore(BaseModel):
    transaction_id: str
    unified_score: int = Field(ge=0, le=100)
    band: RiskBand
    tier: RiskTier
    components: list[ComponentScore] = Field(default_factory=list)


class AuthorizationResponse(BaseModel):
    transaction_id: str
    decision: DecisionAction
    risk_score: int = Field(ge=0, le=100)
    reason_code: str
    challenge_id: str | None = None
    risk_tier: RiskTier | None = None
    friction: str | None = None
    workflow: str | None = None
    verification_timeout_seconds: int = Field(default=0, ge=0)
    processing_path: ProcessingPath | None = None
    explanation_mode: ExplanationMode | None = None
    explanation_job_id: str | None = None
    escalation_required: bool = False


class TransactionRepository(Protocol):
    def save(self, transaction: Transaction) -> Transaction: ...

    def list(self) -> list[Transaction]: ...

    def get(self, transaction_id: str) -> Transaction | None: ...


@dataclass
class InMemoryTransactionRepository:
    """Temporary adapter used until the populated database adapter is wired."""

    transactions: dict[str, Transaction] = field(default_factory=dict)

    def save(self, transaction: Transaction) -> Transaction:
        self.transactions[transaction.transaction_id] = transaction
        return transaction

    def list(self) -> list[Transaction]:
        return list(self.transactions.values())

    def get(self, transaction_id: str) -> Transaction | None:
        return self.transactions.get(transaction_id)


def _feature_payload(transaction: Transaction) -> dict[str, float]:
    """Build a conservative feature vector from the ingress contract."""
    return {
        "amount_log": min(20.0, transaction.amount_minor / 100.0),
        "mcc_risk": 0.5,
        "velocity_5m": 0.0,
        "device_trust": -1.0,
        "network_trust": -1.0,
        "impossible_travel": 0.0,
        "new_device": 0.0,
        "hour_of_day": 12.0,
        "weekend": 0.0,
        "distance_km": 0.0,
    }


def _post_json(url: str, path: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        f"{url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("downstream response must be an object")
    return value


def _ml_first_risk(transaction: Transaction, *, settings: Any) -> RiskScore | None:
    """Try learned scores first; return None to preserve the legacy scheme."""
    if not (settings.SUPERVISED_URL and settings.ANOMALY_URL and settings.RISK_FUSION_URL):
        return None
    features = _feature_payload(transaction)
    try:
        supervised = _post_json(
            settings.SUPERVISED_URL,
            "/api/v1/score",
            {"transaction_id": transaction.transaction_id, "features": features},
            settings.ML_TIMEOUT_SECONDS,
        )
        anomaly = _post_json(
            settings.ANOMALY_URL,
            "/api/v1/score",
            {"transaction_id": transaction.transaction_id, "features": features},
            settings.ML_TIMEOUT_SECONDS,
        )
        components = [
            {
                "component": "supervised",
                "score": round(float(supervised.get("fraud_probability", 0.0)) * 100),
                "weight": 0.5,
                "available": bool(supervised.get("model_available", False)),
                "reason_code": str(supervised.get("model_name", "unknown")),
            },
            {
                "component": "anomaly",
                "score": round(float(anomaly.get("anomaly_score", 0.0)) * 100),
                "weight": 0.5,
                "available": bool(anomaly.get("model_available", False)),
                "reason_code": str(anomaly.get("model_name", "unknown")),
            },
        ]
        fused = _post_json(
            settings.RISK_FUSION_URL,
            "/api/v1/risk/fuse",
            {"transaction_id": transaction.transaction_id, "components": components},
            settings.ML_TIMEOUT_SECONDS,
        )
        score = int(fused["unified_score"])
        tier = tier_for_score(score)
        return RiskScore(
            transaction_id=transaction.transaction_id,
            unified_score=score,
            band=band_for_tier(tier),
            tier=tier,
            components=[ComponentScore(**component) for component in components],
        )
    except Exception:  # noqa: BLE001 - ML is an optional first layer
        return None


def calculate_risk(transaction: Transaction, *, settings: Any | None = None) -> RiskScore:
    """Use ML/fusion first, falling back to the deterministic baseline."""
    if settings is not None:
        learned = _ml_first_risk(transaction, settings=settings)
        if learned is not None:
            return learned
    """Return the deterministic legacy risk score."""
    score = 0
    reason: str | None = None
    if transaction.amount_minor >= 100_000:
        score += 35
        reason = "HIGH_VALUE"
    if transaction.channel == Channel.CARD_NOT_PRESENT:
        score += 10
        reason = reason or "CARD_NOT_PRESENT"
    score = min(score, 100)
    tier = tier_for_score(score)
    component = ComponentScore(
        component="ingress_baseline",
        score=score,
        weight=1.0,
        reason_code=reason,
    )
    return RiskScore(
        transaction_id=transaction.transaction_id,
        unified_score=score,
        band=band_for_tier(tier),
        tier=tier,
        components=[component],
    )


def _legacy_authorize(transaction: Transaction, risk: RiskScore) -> AuthorizationResponse:
    """Keep the original response semantics for pre-rail clients."""
    if risk.band == RiskBand.BLOCK:
        decision = DecisionAction.DECLINE
        challenge_id = None
        reason_code = "RISK_THRESHOLD"
    elif risk.band == RiskBand.VERIFY:
        decision = DecisionAction.CHALLENGE
        challenge_id = f"challenge_{uuid4().hex}"
        reason_code = "RISK_THRESHOLD"
    else:
        decision = DecisionAction.ALLOW
        challenge_id = None
        reason_code = "BASELINE_APPROVED"
    policy = policy_for_tier(risk.tier)
    return AuthorizationResponse(
        transaction_id=transaction.transaction_id,
        decision=decision,
        risk_score=risk.unified_score,
        reason_code=reason_code,
        challenge_id=challenge_id,
        risk_tier=risk.tier,
        friction=policy.friction,
        workflow=policy.workflow,
        verification_timeout_seconds=policy.timeout_seconds,
        processing_path=ProcessingPath.FAST,
        explanation_mode=ExplanationMode.ASYNC,
    )


def authorize(transaction: Transaction, *, settings: Any | None = None) -> AuthorizationResponse:
    """Authorize with ML-first risk and the existing authorization matrix."""
    risk = calculate_risk(transaction, settings=settings)
    if transaction.payment_rail is None:
        return _legacy_authorize(transaction, risk)
    path = transaction.processing_path or processing_path_for_rail(transaction.payment_rail)
    policy = policy_for_tier(risk.tier)
    if risk.tier == RiskTier.NO_RISK:
        decision = DecisionAction.ALLOW
        reason_code = "BASELINE_APPROVED"
        challenge_id = None
    elif risk.tier in (RiskTier.LOW, RiskTier.MODERATE):
        decision = DecisionAction.CHALLENGE
        reason_code = "RISK_TIER_VERIFICATION_REQUIRED"
        challenge_id = f"challenge_{uuid4().hex}"
    else:
        decision = DecisionAction.REVIEW
        reason_code = "HIGH_RISK_ANALYST_REVIEW_REQUIRED"
        challenge_id = f"challenge_{uuid4().hex}"
    explanation_job_id = f"explain_{uuid4().hex}" if path == ProcessingPath.FAST else None
    return AuthorizationResponse(
        transaction_id=transaction.transaction_id,
        decision=decision,
        risk_score=risk.unified_score,
        reason_code=reason_code,
        challenge_id=challenge_id,
        risk_tier=risk.tier,
        friction=policy.friction,
        workflow=policy.workflow,
        verification_timeout_seconds=policy.timeout_seconds,
        processing_path=path,
        explanation_mode=(
            ExplanationMode.ASYNC if path == ProcessingPath.FAST else ExplanationMode.IN_BAND
        ),
        explanation_job_id=explanation_job_id,
        escalation_required=risk.tier == RiskTier.HIGH,
    )
