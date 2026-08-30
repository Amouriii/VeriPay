"""Tests for veripay_common.security — verification tokens + envelope cipher."""

from datetime import UTC, datetime, timedelta

import pytest
from veripay_common.constants import (
    VERIFICATION_TOKEN_MAX_TTL_SEC,
    VERIFICATION_TOKEN_MIN_TTL_SEC,
)
from veripay_common.security import (
    EncryptedEnvelope,
    HmacEnvelopeEncryptor,
    HmacVerificationTokenSigner,
    VerificationTokenClaims,
)


def _claims(issued_at: datetime | None = None) -> VerificationTokenClaims:
    issued = issued_at or datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC)
    return VerificationTokenClaims(
        session_id="sess-1",
        transaction_id="tx-1",
        device_id="dev-1",
        nonce="nonce-1",
        amount_minor=12345,
        currency="EUR",
        risk_tier="MODERATE",
        issued_at=issued,
        expires_at=issued,
        token_id="tok-1",
    )


# --- HmacVerificationTokenSigner ------------------------------------------


def test_issue_and_verify_roundtrip() -> None:
    signer = HmacVerificationTokenSigner("secret-key-16-bytes!")
    token = signer.issue(_claims(), 30)
    assert token.startswith("vpt1.")
    verified = signer.verify(token, now=datetime(2026, 8, 30, 12, 0, 5, tzinfo=UTC))
    assert verified.session_id == "sess-1"
    assert verified.amount_minor == 12345
    assert verified.expires_at == datetime(2026, 8, 30, 12, 0, 30, tzinfo=UTC)


def test_tampered_token_rejected() -> None:
    signer = HmacVerificationTokenSigner("secret-key-16-bytes!")
    token = signer.issue(_claims(), 30)
    body, sig = token.rsplit(".", 1)
    tampered = body[:-2] + ("AA" if not body.endswith("AA") else "BB") + "." + sig
    with pytest.raises(ValueError):
        signer.verify(tampered, now=datetime(2026, 8, 30, 12, 0, 5, tzinfo=UTC))


def test_wrong_secret_rejected() -> None:
    signer_a = HmacVerificationTokenSigner("secret-key-16-bytes!")
    signer_b = HmacVerificationTokenSigner("other-key-16-bytes!!")
    token = signer_a.issue(_claims(), 30)
    with pytest.raises(ValueError):
        signer_b.verify(token, now=datetime(2026, 8, 30, 12, 0, 5, tzinfo=UTC))


def test_expired_token_rejected() -> None:
    signer = HmacVerificationTokenSigner("secret-key-16-bytes!")
    token = signer.issue(_claims(), 10)
    with pytest.raises(ValueError, match="expired"):
        signer.verify(token, now=datetime(2026, 8, 30, 12, 0, 11, tzinfo=UTC))


def test_ttl_bounds_enforced() -> None:
    signer = HmacVerificationTokenSigner("secret-key-16-bytes!")
    with pytest.raises(ValueError):
        signer.issue(_claims(), VERIFICATION_TOKEN_MIN_TTL_SEC - 1)
    with pytest.raises(ValueError):
        signer.issue(_claims(), VERIFICATION_TOKEN_MAX_TTL_SEC + 1)


def test_short_secret_rejected() -> None:
    with pytest.raises(ValueError, match="16 bytes"):
        HmacVerificationTokenSigner("short")
    with pytest.raises(ValueError, match="16 bytes"):
        HmacEnvelopeEncryptor("short")


def test_naive_timestamp_normalized_to_utc() -> None:
    signer = HmacVerificationTokenSigner("secret-key-16-bytes!")
    naive = datetime(2026, 8, 30, 12, 0, 0)  # no tzinfo
    token = signer.issue(_claims(naive), 30)
    verified = signer.verify(token, now=naive.replace(tzinfo=UTC) + timedelta(seconds=1))
    # pydantic normalizes to UTC; compare offsets, not tzinfo identity
    assert verified.expires_at.utcoffset() == timedelta(0)
    assert verified.expires_at == datetime(2026, 8, 30, 12, 0, 30, tzinfo=UTC)


# --- HmacEnvelopeEncryptor -------------------------------------------------


def test_envelope_roundtrip() -> None:
    enc = HmacEnvelopeEncryptor("envelope-secret-16b")
    payload = b"transaction evidence payload \x00\x01\xff"
    envelope = enc.encrypt(payload)
    assert isinstance(envelope, EncryptedEnvelope)
    assert envelope.ciphertext != ""
    assert enc.decrypt(envelope) == payload


def test_envelope_ciphertext_differs_per_nonce() -> None:
    enc = HmacEnvelopeEncryptor("envelope-secret-16b")
    a = enc.encrypt(b"same payload")
    b = enc.encrypt(b"same payload")
    assert a.ciphertext != b.ciphertext  # random nonce -> fresh keystream
    assert enc.decrypt(a) == b"same payload"
    assert enc.decrypt(b) == b"same payload"


def test_envelope_tamper_detected() -> None:
    enc = HmacEnvelopeEncryptor("envelope-secret-16b")
    envelope = enc.encrypt(b"sensitive")
    # Flip the first ciphertext character (base64url alphabet: A<->B)
    first = envelope.ciphertext[0]
    flipped_char = "B" if first == "A" else "A"
    tampered = EncryptedEnvelope(
        key_id=envelope.key_id,
        nonce=envelope.nonce,
        ciphertext=flipped_char + envelope.ciphertext[1:],
        authentication_tag=envelope.authentication_tag,
    )
    with pytest.raises(ValueError):
        enc.decrypt(tampered)


def test_envelope_wrong_key_id_rejected() -> None:
    enc = HmacEnvelopeEncryptor("envelope-secret-16b", key_id="key-1")
    envelope = enc.encrypt(b"data")
    other = HmacEnvelopeEncryptor("envelope-secret-16b", key_id="key-2")
    with pytest.raises(ValueError, match="key"):
        other.decrypt(envelope)


def test_envelope_wrong_secret_rejected() -> None:
    enc = HmacEnvelopeEncryptor("envelope-secret-16b")
    envelope = enc.encrypt(b"data")
    other = HmacEnvelopeEncryptor("different-secret-16b")
    with pytest.raises(ValueError):
        other.decrypt(envelope)
