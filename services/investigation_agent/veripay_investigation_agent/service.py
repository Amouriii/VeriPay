"""Governed local-LLM investigation and explanation boundary."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

from pydantic import BaseModel, Field
from veripay_common.privacy import DeterministicPiiRedactor, PiiRedactor


class LlmExplanation(BaseModel):
    summary: str
    regulatory_reason_codes: list[str] = Field(default_factory=list)
    model_name: str
    prompt_version: str
    generated_at: datetime


class InvestigationRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    transaction: dict[str, object]
    transaction_history: list[dict[str, object]] = Field(default_factory=list)
    risk_score: int = Field(ge=0, le=100)
    macro_context: dict[str, object] = Field(default_factory=dict)
    prompt_version: str = "fraud-explanation-v1"


class LocalLlmProvider(Protocol):
    model_name: str

    def explain(self, context: dict[str, object]) -> str: ...


class DeterministicLocalLlmProvider:
    model_name = "local-governed-explainer"

    def explain(self, context: dict[str, object]) -> str:
        score = context["risk_score"]
        baseline = context["baseline_30d"]
        macro = context["macro_context"]
        return (
            f"Risk score {score}/100; 30-day baseline contains {baseline} "
            f"transactions; macro context fields: {len(macro)}."
        )


def _reason_codes(score: int, baseline_count: int, macro_context: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if score > 50:
        reasons.append("RISK_SCORE_HIGH")
    elif score > 25:
        reasons.append("RISK_SCORE_MODERATE")
    elif score > 5:
        reasons.append("RISK_SCORE_LOW")
    if baseline_count == 0:
        reasons.append("BASELINE_UNAVAILABLE")
    if macro_context:
        reasons.append("MACRO_CONTEXT_CONSIDERED")
    return reasons or ["NO_ADVERSE_FACTOR"]


def evaluate(
    request: InvestigationRequest,
    *,
    redactor: PiiRedactor | None = None,
    provider: LocalLlmProvider | None = None,
    now: datetime | None = None,
) -> LlmExplanation:
    """Explain a model result without allowing the LLM to authorize a payment."""
    redactor = redactor or DeterministicPiiRedactor()
    provider = provider or DeterministicLocalLlmProvider()
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    cutoff = current - timedelta(days=30)
    history = [
        event
        for event in request.transaction_history
        if _event_time(event) is None or _event_time(event) >= cutoff
    ]
    redacted_transaction = redactor.redact(request.transaction).payload
    context = {
        "transaction": redacted_transaction,
        "baseline_30d": history,
        "risk_score": request.risk_score,
        "macro_context": request.macro_context,
    }
    return LlmExplanation(
        summary=provider.explain(context),
        regulatory_reason_codes=_reason_codes(
            request.risk_score, len(history), request.macro_context
        ),
        model_name=provider.model_name,
        prompt_version=request.prompt_version,
        generated_at=current,
    )


def _event_time(event: dict[str, object]) -> datetime | None:
    value = event.get("occurred_at") or event.get("timestamp")
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


__all__ = [
    "DeterministicLocalLlmProvider",
    "InvestigationRequest",
    "LlmExplanation",
    "LocalLlmProvider",
    "evaluate",
]
