"""PII minimization boundary for data leaving the payment edge.

The deterministic adapter is suitable for tests and local development. A
production deployment should replace it with a vault-backed tokenization
provider while preserving the same protocol and sanitized output contract.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import Any, Protocol

from pydantic import BaseModel, Field

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:pan|primary.?account|card.?number|cvv|d?cvv|name|address|national.?id|"
    r"social.?security|ssn|ip|device.?id|payment.?instrument|credential|secret|token)",
    re.IGNORECASE,
)


class RedactionResult(BaseModel):
    """Sanitized payload and non-sensitive metadata about the transformation."""

    payload: dict[str, Any]
    redacted_fields: list[str] = Field(default_factory=list)
    tokenization_version: str = "deterministic-v1"


class PiiRedactor(Protocol):
    """Provider boundary for edge-to-model PII minimization."""

    def redact(self, payload: Mapping[str, Any]) -> RedactionResult: ...


class DeterministicPiiRedactor:
    """Replace configured sensitive values with stable one-way surrogate tokens."""

    def __init__(self, *, namespace: str = "veripay") -> None:
        self.namespace = namespace

    def _tokenize(self, value: Any) -> str:
        digest = hashlib.sha256(f"{self.namespace}:{value}".encode()).hexdigest()[:20]
        return f"tok_{digest}"

    def _walk(self, value: Any, path: str, redacted: list[str]) -> Any:
        if isinstance(value, Mapping):
            result: dict[str, Any] = {}
            for key, child in value.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}" if path else key_text
                if _SENSITIVE_KEY_PATTERN.search(key_text):
                    result[key_text] = self._tokenize(child)
                    redacted.append(child_path)
                else:
                    result[key_text] = self._walk(child, child_path, redacted)
            return result
        if isinstance(value, (list, tuple)):
            return [
                self._walk(child, f"{path}[{index}]", redacted) for index, child in enumerate(value)
            ]
        return value

    def redact(self, payload: Mapping[str, Any]) -> RedactionResult:
        redacted_fields: list[str] = []
        sanitized = self._walk(payload, "", redacted_fields)
        return RedactionResult(payload=sanitized, redacted_fields=redacted_fields)


__all__ = ["DeterministicPiiRedactor", "PiiRedactor", "RedactionResult"]
