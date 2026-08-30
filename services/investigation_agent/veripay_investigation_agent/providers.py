"""LLM provider boundary for the investigation agent. PLAN §20.

Two interchangeable providers sit behind ``LocalLlmProvider``:

- ``DeterministicLocalLlmProvider`` — zero-dependency, reproducible summaries
  (the default and the failure fallback).
- ``OpenAiCompatibleLlmProvider`` — talks to a local vLLM (or any
  OpenAI-compatible) server. Prompts are built **only from redacted context**
  (defense in depth on top of the redaction applied in ``evaluate``), output
  is parsed defensively, and the LLM never authorizes a payment — it only
  summarizes evidence.
"""

from __future__ import annotations

import importlib.util
import json
from typing import Any

from veripay_common.privacy import DeterministicPiiRedactor

from veripay_investigation_agent.service import (
    DeterministicLocalLlmProvider,
    LocalLlmProvider,
)

_SYSTEM_PROMPT = (
    "You are the VeriPay fraud investigation copilot. You explain risk "
    "decisions to fraud analysts using only the evidence provided to you. You "
    "NEVER authorize, block, or alter a payment decision. Write 2-4 concise "
    "sentences and end with a 'Key signals' bullet list."
)

_MAX_BASELINE_EVENTS = 20
_MAX_TOKENS = 256


class OpenAiCompatibleLlmProvider:
    """vLLM (OpenAI-compatible) provider behind the governed boundary.

    ``client`` is injectable for tests; when omitted, an ``openai.OpenAI``
    client is built lazily from ``base_url``/``api_key``/``timeout_seconds``.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client
        self.model_name = f"vllm:{model}"

    def _client_instance(self) -> Any:
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout_seconds,
            )
        return self._client

    def explain(self, context: dict[str, object]) -> str:
        """Summarize the redacted context; raise ``ValueError`` on bad output."""
        completion = self._client_instance().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _render_prompt(context)},
            ],
            temperature=0.0,
            max_tokens=_MAX_TOKENS,
        )
        try:
            content = completion.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError("LLM response missing text content") from exc
        if not content or not str(content).strip():
            raise ValueError("LLM returned an empty explanation")
        return str(content).strip()


def _render_prompt(context: dict[str, object]) -> str:
    """Render a prompt from redacted context (defense in depth).

    ``evaluate`` already redacts the transaction; the provider re-redacts the
    whole context so baseline history and macro context are also sanitized
    before anything crosses the LLM boundary.
    """
    redacted = DeterministicPiiRedactor().redact(context).payload
    transaction = redacted.get("transaction", {})
    baseline = redacted.get("baseline_30d", [])
    if not isinstance(baseline, list):
        baseline = []
    macro = redacted.get("macro_context", {})
    score = redacted.get("risk_score", "?")
    return "\n".join(
        [
            f"Risk score: {score}/100",
            f"30-day baseline: {len(baseline)} event(s)",
            f"Transaction (redacted): {json.dumps(transaction, default=str)}",
            f"Recent events (redacted): {json.dumps(baseline[:_MAX_BASELINE_EVENTS], default=str)}",
            f"Macro context (redacted): {json.dumps(macro, default=str)}",
        ]
    )


def provider_from_settings(settings: Any) -> LocalLlmProvider:
    """Select the provider from service settings.

    vLLM is used only when configured *and* the ``openai`` package is
    installed; any other combination returns the deterministic provider.
    """
    if (
        settings.LLM_PROVIDER == "openai_compatible"
        and importlib.util.find_spec("openai") is not None
    ):
        return OpenAiCompatibleLlmProvider(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        )
    return DeterministicLocalLlmProvider()


__all__ = ["OpenAiCompatibleLlmProvider", "provider_from_settings"]
