"""Provider boundary tests: vLLM provider, redaction, selection, fallback."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from veripay_investigation_agent import providers
from veripay_investigation_agent.providers import OpenAiCompatibleLlmProvider
from veripay_investigation_agent.service import (
    DeterministicLocalLlmProvider,
    InvestigationRequest,
    evaluate,
)

_LLM_SETTINGS = SimpleNamespace(
    LLM_PROVIDER="openai_compatible",
    LLM_BASE_URL="http://localhost:8000/v1",
    LLM_API_KEY="EMPTY",
    LLM_MODEL="veripay-explainer",
    LLM_TIMEOUT_SECONDS=30.0,
)


class _FakeClient:
    """Chainable fake for ``client.chat.completions.create(...)``."""

    def __init__(self, content: str | None = "summary", *, captured: list | None = None) -> None:
        self._content = content
        self._captured = captured if captured is not None else []

    @property
    def chat(self) -> _FakeClient:
        return self

    @property
    def completions(self) -> _FakeClient:
        return self

    def create(self, **kwargs) -> SimpleNamespace:
        self._captured.append(kwargs)
        message = SimpleNamespace(content=self._content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


def _vllm_provider(client: _FakeClient) -> OpenAiCompatibleLlmProvider:
    return OpenAiCompatibleLlmProvider(
        base_url="http://localhost:8000/v1",
        api_key="EMPTY",
        model="veripay-explainer",
        client=client,
    )


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        transaction_id="tx_1",
        transaction={"amount_minor": 4999, "merchant_id": "m_amazon"},
        risk_score=42,
        macro_context={"country": "US"},
    )


def test_provider_from_settings_defaults_to_deterministic() -> None:
    settings = SimpleNamespace(**{**_LLM_SETTINGS.__dict__, "LLM_PROVIDER": "deterministic"})
    provider = providers.provider_from_settings(settings)
    assert isinstance(provider, DeterministicLocalLlmProvider)


def test_provider_from_settings_falls_back_when_openai_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        providers.importlib.util, "find_spec", lambda name: None if name == "openai" else object()
    )
    provider = providers.provider_from_settings(_LLM_SETTINGS)
    assert isinstance(provider, DeterministicLocalLlmProvider)


def test_provider_from_settings_returns_vllm_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        providers.importlib.util, "find_spec", lambda name: object() if name == "openai" else None
    )
    provider = providers.provider_from_settings(_LLM_SETTINGS)
    assert isinstance(provider, OpenAiCompatibleLlmProvider)
    assert provider.model_name == "vllm:veripay-explainer"


def test_explain_redacts_sensitive_fields() -> None:
    captured: list = []
    provider = _vllm_provider(_FakeClient("summary", captured=captured))
    context = {
        "risk_score": 42,
        "transaction": {
            "amount_minor": 4999,
            "merchant_id": "m_amazon",
            "payment_instrument": "4111111111111111",
        },
        "baseline_30d": [
            {"occurred_at": "2026-08-01T10:00:00Z", "payment_instrument": "4222222222222222"}
        ],
        "macro_context": {"country": "US"},
    }
    provider.explain(context)
    user_message = captured[0]["messages"][1]["content"]
    # Raw card numbers never cross the boundary; tokens and safe fields do.
    assert "4111111111111111" not in user_message
    assert "4222222222222222" not in user_message
    assert "tok_" in user_message
    assert "m_amazon" in user_message
    assert "Risk score: 42/100" in user_message


def test_explain_returns_content() -> None:
    provider = _vllm_provider(_FakeClient("Suspicious velocity and new device."))
    result = provider.explain(
        {"risk_score": 42, "transaction": {}, "baseline_30d": [], "macro_context": {}}
    )
    assert result == "Suspicious velocity and new device."


def test_explain_empty_content_raises() -> None:
    provider = _vllm_provider(_FakeClient(None))
    with pytest.raises(ValueError, match="empty explanation"):
        provider.explain(
            {"risk_score": 42, "transaction": {}, "baseline_30d": [], "macro_context": {}}
        )


def test_evaluate_uses_configured_provider(monkeypatch) -> None:
    fake = SimpleNamespace(model_name="vllm:test", explain=lambda context: "vllm summary")
    monkeypatch.setattr("veripay_investigation_agent.service._provider_from_settings", lambda: fake)
    result = evaluate(_request())
    assert result.summary == "vllm summary"
    assert result.model_name == "vllm:test"
    assert result.fallback is False


def test_evaluate_falls_back_when_provider_fails() -> None:
    class _FailingProvider:
        model_name = "vllm:broken"

        def explain(self, context) -> str:  # type: ignore[no-untyped-def]
            raise RuntimeError("server unreachable")

    result = evaluate(_request(), provider=_FailingProvider())
    assert result.fallback is True
    assert result.model_name == DeterministicLocalLlmProvider().model_name
    assert "Risk score 42/100" in result.summary
    # Deterministic reason codes are preserved on the fallback path.
    assert "RISK_SCORE_MODERATE" in result.regulatory_reason_codes
