"""Governed local-LLM investigation and explanation boundary."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, cast

from pydantic import BaseModel, Field
from veripay_common.privacy import DeterministicPiiRedactor, PiiRedactor


class LlmExplanation(BaseModel):
    summary: str
    regulatory_reason_codes: list[str] = Field(default_factory=list)
    model_name: str
    prompt_version: str
    generated_at: datetime
    # True when the configured provider failed and the deterministic
    # explainer produced the summary instead.
    fallback: bool = False


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
        macro = cast(dict[str, object], context["macro_context"])
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


def _provider_from_settings() -> LocalLlmProvider:
    """Resolve the configured provider (deterministic by default)."""
    from veripay_investigation_agent.config import settings
    from veripay_investigation_agent.providers import provider_from_settings

    return provider_from_settings(settings)


def evaluate(
    request: InvestigationRequest,
    *,
    redactor: PiiRedactor | None = None,
    provider: LocalLlmProvider | None = None,
    now: datetime | None = None,
) -> LlmExplanation:
    """Explain a model result without allowing the LLM to authorize a payment."""
    redactor = redactor or DeterministicPiiRedactor()
    provider = provider or _provider_from_settings()
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    cutoff = current - timedelta(days=30)
    history: list[dict[str, object]] = []
    for event in request.transaction_history:
        occurred_at = _event_time(event)
        if occurred_at is None or occurred_at >= cutoff:
            history.append(event)
    redacted_transaction = redactor.redact(request.transaction).payload
    context = {
        "transaction": redacted_transaction,
        "baseline_30d": history,
        "risk_score": request.risk_score,
        "macro_context": request.macro_context,
    }
    # The provider is advisory-only and interchangeable. If the configured
    # provider fails (server unreachable, bad output, missing dependency),
    # degrade to the deterministic explainer instead of erroring.
    try:
        summary = provider.explain(context)
        model_name = provider.model_name
        fallback = False
    except Exception:
        deterministic = DeterministicLocalLlmProvider()
        summary = deterministic.explain(context)
        model_name = deterministic.model_name
        fallback = True
    return LlmExplanation(
        summary=summary,
        regulatory_reason_codes=_reason_codes(
            request.risk_score, len(history), request.macro_context
        ),
        model_name=model_name,
        prompt_version=request.prompt_version,
        generated_at=current,
        fallback=fallback,
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
    "_provider_from_settings",
]
