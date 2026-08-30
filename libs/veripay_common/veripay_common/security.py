"""Provider-neutral cryptographic boundaries used by payment verification.

The HMAC token signer and envelope cipher are deterministic local adapters. They
keep tests self-contained while making production key-management replacement
explicit. Secrets are never included in serialized models or logs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from pydantic import BaseModel, Field

from veripay_common.constants import (
    VERIFICATION_TOKEN_MAX_TTL_SEC,
    VERIFICATION_TOKEN_MIN_TTL_SEC,
)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class VerificationTokenClaims(BaseModel):
    """Bound claims carried by a one-use authorization verification token."""

    session_id: str = Field(min_length=1)
    transaction_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    nonce: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_tier: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime
    token_id: str = Field(min_length=1)


class VerificationTokenSigner(Protocol):
    """Signing and verification boundary backed by an HSM/KMS in production."""

    def issue(self, claims: VerificationTokenClaims, ttl_seconds: int) -> str: ...

    def verify(self, token: str, now: datetime | None = None) -> VerificationTokenClaims: ...


class HmacVerificationTokenSigner:
    """Compact HMAC-SHA256 signer for local/test deployments."""

    def __init__(self, secret: bytes | str) -> None:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if len(secret) < 16:
            raise ValueError("Verification signing secret must contain at least 16 bytes")
        self._secret = secret

    def _sign(self, body: bytes) -> str:
        return _b64encode(hmac.new(self._secret, body, hashlib.sha256).digest())

    def issue(self, claims: VerificationTokenClaims, ttl_seconds: int) -> str:
        if not VERIFICATION_TOKEN_MIN_TTL_SEC <= ttl_seconds <= VERIFICATION_TOKEN_MAX_TTL_SEC:
            raise ValueError("Verification token TTL must be between 10 and 30 seconds")
        issued_at = (
            claims.issued_at if claims.issued_at.tzinfo else claims.issued_at.replace(tzinfo=UTC)
        )
        expires_at = issued_at.replace() + timedelta(seconds=ttl_seconds)
        body_claims = claims.model_copy(update={"issued_at": issued_at, "expires_at": expires_at})
        body = json.dumps(
            body_claims.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return f"vpt1.{_b64encode(body)}.{self._sign(body)}"

    def verify(self, token: str, now: datetime | None = None) -> VerificationTokenClaims:
        try:
            version, encoded_body, signature = token.split(".", 2)
            if version != "vpt1":
                raise ValueError("Unsupported verification token version")
            body = _b64decode(encoded_body)
            expected = self._sign(body)
            if not hmac.compare_digest(expected, signature):
                raise ValueError("Verification token signature is invalid")
            claims = VerificationTokenClaims.model_validate(json.loads(body))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Verification token is invalid") from exc
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        if claims.expires_at <= current:
            raise ValueError("Verification token is expired")
        return claims


class EncryptedEnvelope(BaseModel):
    """Opaque authenticated envelope used for telemetry and evidence references."""

    key_id: str = Field(min_length=1)
    nonce: str = Field(min_length=1)
    ciphertext: str = Field(min_length=1)
    authentication_tag: str = Field(min_length=1)


class EnvelopeEncryptor(Protocol):
    def encrypt(self, payload: bytes) -> EncryptedEnvelope: ...

    def decrypt(self, envelope: EncryptedEnvelope) -> bytes: ...


class HmacEnvelopeEncryptor:
    """Small authenticated envelope adapter for local development.

    Production must use an approved AEAD implementation and managed key. This
    adapter uses an HMAC-derived stream only to keep local tests dependency-free.
    """

    def __init__(self, secret: bytes | str, *, key_id: str = "local-test-key") -> None:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if len(secret) < 16:
            raise ValueError("Envelope encryption secret must contain at least 16 bytes")
        self._secret = secret
        self.key_id = key_id

    def _stream(self, nonce: bytes, size: int) -> bytes:
        output = bytearray()
        counter = 0
        while len(output) < size:
            output.extend(
                hmac.new(
                    self._secret,
                    nonce + counter.to_bytes(4, "big"),
                    hashlib.sha256,
                ).digest()
            )
            counter += 1
        return bytes(output[:size])

    def encrypt(self, payload: bytes) -> EncryptedEnvelope:
        nonce = secrets.token_bytes(16)
        stream = self._stream(nonce, len(payload))
        ciphertext = bytes(left ^ right for left, right in zip(payload, stream, strict=True))
        tag = hmac.new(self._secret, nonce + ciphertext, hashlib.sha256).digest()
        return EncryptedEnvelope(
            key_id=self.key_id,
            nonce=_b64encode(nonce),
            ciphertext=_b64encode(ciphertext),
            authentication_tag=_b64encode(tag),
        )

    def decrypt(self, envelope: EncryptedEnvelope) -> bytes:
        if envelope.key_id != self.key_id:
            raise ValueError("Unknown envelope key")
        nonce = _b64decode(envelope.nonce)
        ciphertext = _b64decode(envelope.ciphertext)
        expected = hmac.new(self._secret, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(envelope.authentication_tag)):
            raise ValueError("Envelope authentication failed")
        stream = self._stream(nonce, len(ciphertext))
        return bytes(left ^ right for left, right in zip(ciphertext, stream, strict=True))


__all__ = [
    "EncryptedEnvelope",
    "EnvelopeEncryptor",
    "HmacEnvelopeEncryptor",
    "HmacVerificationTokenSigner",
    "VerificationTokenClaims",
    "VerificationTokenSigner",
]
