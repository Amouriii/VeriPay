"""Tier-driven mobile verification orchestration.

Push delivery, biometric verification, and bank-core settlement remain provider
boundaries. The in-memory implementation enforces the security-critical state
transitions and token bindings used by tests and local development.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from veripay_common.enums import (
    PaymentRail,
    ProcessingPath,
    RiskTier,
    VerificationOutcome,
)
from veripay_common.risk_policy import (
    policy_for_tier,
    processing_path_for_rail,
    tier_for_score,
)
from veripay_common.security import HmacVerificationTokenSigner, VerificationTokenClaims


class VerificationSessionRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_score: int = Field(ge=0, le=100)
    risk_tier: RiskTier | None = None
    payment_rail: PaymentRail = PaymentRail.CARD
    processing_path: ProcessingPath | None = None
    ttl_seconds: int = Field(default=30, ge=10, le=30)

    @model_validator(mode="after")
    def derive_fields(self) -> VerificationSessionRequest:
        if self.risk_tier is None:
            self.risk_tier = tier_for_score(self.risk_score)
        if self.processing_path is None:
            self.processing_path = processing_path_for_rail(self.payment_rail)
        return self


class VerificationCompletionRequest(BaseModel):
    token: str = Field(min_length=1)
    outcome: VerificationOutcome
    exact_amount_minor: int | None = Field(default=None, ge=0)
    exact_currency: str | None = Field(default=None, min_length=3, max_length=3)
    biometric_assertion: str | None = None
    confirmation_swipe: bool = False
    denial_reason: str | None = None


class VerificationSession(BaseModel):
    session_id: str
    transaction_id: str
    device_id: str
    amount_minor: int
    currency: str
    risk_tier: RiskTier
    processing_path: ProcessingPath
    friction: str
    workflow: str
    timeout_seconds: int
    expires_at: datetime
    token_id: str
    token_digest: str
    outcome: VerificationOutcome = VerificationOutcome.PENDING
    temporary_lock: bool = False
    escalation_required: bool = False
    created_at: datetime

    @property
    def token_value(self) -> str:
        """Tokens are deliberately not serializable from the session model."""
        raise AttributeError("Verification token is write-only and never stored on a session")


class VerificationResult(BaseModel):
    session_id: str
    transaction_id: str
    outcome: VerificationOutcome
    risk_tier: RiskTier
    temporary_lock: bool
    escalation_required: bool
    reason_code: str
    completed_at: datetime


class PushProvider(Protocol):
    def dispatch(self, session: VerificationSession) -> None: ...


class BiometricAssertionVerifier(Protocol):
    def verify(self, assertion: str, device_id: str, transaction_id: str) -> bool: ...


class RecordingPushProvider:
    """Deterministic local adapter that records dispatched session IDs."""

    def __init__(self) -> None:
        self.session_ids: list[str] = []

    def dispatch(self, session: VerificationSession) -> None:
        self.session_ids.append(session.session_id)


class DeterministicBiometricAssertionVerifier:
    """Test adapter; production verifies a platform hardware assertion."""

    def verify(self, assertion: str, device_id: str, transaction_id: str) -> bool:
        del device_id, transaction_id
        return assertion == "valid-biometric-assertion"


class VerificationRepository(Protocol):
    def save(self, session: VerificationSession) -> VerificationSession: ...

    def get(self, session_id: str) -> VerificationSession | None: ...


@dataclass
class InMemoryVerificationRepository:
    sessions: dict[str, VerificationSession] = field(default_factory=dict)

    def save(self, session: VerificationSession) -> VerificationSession:
        self.sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> VerificationSession | None:
        return self.sessions.get(session_id)


class VerificationService:
    def __init__(
        self,
        repository: VerificationRepository | None = None,
        signer: HmacVerificationTokenSigner | None = None,
        push_provider: PushProvider | None = None,
        biometric_verifier: BiometricAssertionVerifier | None = None,
        now: Callable[[], datetime] | None = None,
        nonce_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository or InMemoryVerificationRepository()
        self.signer = signer or HmacVerificationTokenSigner("local-veripay-signing-key")
        self.push_provider = push_provider or RecordingPushProvider()
        self.biometric_verifier = biometric_verifier or DeterministicBiometricAssertionVerifier()
        self.now = now or (lambda: datetime.now(UTC))
        self.nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(18))

    def create_session(
        self, request: VerificationSessionRequest
    ) -> tuple[VerificationSession, str]:
        assert request.risk_tier is not None
        assert request.processing_path is not None
        policy = policy_for_tier(request.risk_tier)
        now = self.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        session_id = f"verify_{uuid4().hex}"
        token_id = f"token_{uuid4().hex}"
        claims = VerificationTokenClaims(
            session_id=session_id,
            transaction_id=request.transaction_id,
            device_id=request.device_id,
            nonce=self.nonce_factory(),
            amount_minor=request.amount_minor,
            currency=request.currency.upper(),
            risk_tier=request.risk_tier,
            issued_at=now,
            expires_at=now,
            token_id=token_id,
        )
        token = self.signer.issue(claims, request.ttl_seconds)
        parsed_claims = self.signer.verify(token, now=now)
        session = VerificationSession(
            session_id=session_id,
            transaction_id=request.transaction_id,
            device_id=request.device_id,
            amount_minor=request.amount_minor,
            currency=request.currency.upper(),
            risk_tier=request.risk_tier,
            processing_path=request.processing_path,
            friction=policy.friction,
            workflow=policy.workflow,
            timeout_seconds=policy.timeout_seconds,
            expires_at=parsed_claims.expires_at,
            token_id=token_id,
            token_digest=self._digest(token),
            created_at=now,
        )
        self.repository.save(session)
        if request.risk_tier != RiskTier.NO_RISK:
            self.push_provider.dispatch(session)
        return session, token

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _expired(self, session: VerificationSession) -> bool:
        current = self.now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        return session.expires_at <= current

    def _validate_workflow(
        self,
        session: VerificationSession,
        request: VerificationCompletionRequest,
    ) -> str | None:
        if request.outcome not in (VerificationOutcome.APPROVED, VerificationOutcome.DENIED):
            return None
        if request.outcome == VerificationOutcome.DENIED:
            return None
        if session.risk_tier == RiskTier.NO_RISK:
            return None
        if session.risk_tier == RiskTier.MODERATE:
            if not request.biometric_assertion:
                return "BIOMETRIC_ASSERTION_REQUIRED"
            if not self.biometric_verifier.verify(
                request.biometric_assertion,
                session.device_id,
                session.transaction_id,
            ):
                return "BIOMETRIC_ASSERTION_REJECTED"
        if session.risk_tier == RiskTier.HIGH:
            if request.exact_amount_minor != session.amount_minor:
                return "EXACT_AMOUNT_MISMATCH"
            if (request.exact_currency or "").upper() != session.currency:
                return "EXACT_CURRENCY_MISMATCH"
            if not request.biometric_assertion:
                return "BIOMETRIC_ASSERTION_REQUIRED"
            if not self.biometric_verifier.verify(
                request.biometric_assertion,
                session.device_id,
                session.transaction_id,
            ):
                return "BIOMETRIC_ASSERTION_REJECTED"
            if not request.confirmation_swipe:
                return "CONFIRMATION_SWIPE_REQUIRED"
        return None

    def complete_session(
        self,
        session_id: str,
        request: VerificationCompletionRequest,
    ) -> VerificationResult:
        session = self.repository.get(session_id)
        now = self.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        if session is None:
            raise KeyError("Verification session not found")
        if session.outcome != VerificationOutcome.PENDING:
            raise ValueError("Verification session is already completed")
        if self._digest(request.token) != session.token_digest:
            raise ValueError("Verification token binding failed")
        try:
            claims = self.signer.verify(request.token, now=now)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if (
            claims.session_id != session.session_id
            or claims.transaction_id != session.transaction_id
            or claims.device_id != session.device_id
            or claims.token_id != session.token_id
        ):
            raise ValueError("Verification token claims do not match session")
        if self._expired(session):
            session.outcome = (
                VerificationOutcome.ESCALATED
                if session.risk_tier == RiskTier.HIGH
                else VerificationOutcome.TIMED_OUT
            )
            session.temporary_lock = session.risk_tier == RiskTier.MODERATE
            session.escalation_required = session.risk_tier == RiskTier.HIGH
            self.repository.save(session)
            return VerificationResult(
                session_id=session.session_id,
                transaction_id=session.transaction_id,
                outcome=session.outcome,
                risk_tier=session.risk_tier,
                temporary_lock=session.temporary_lock,
                escalation_required=session.escalation_required,
                reason_code="VERIFICATION_TIMEOUT",
                completed_at=now,
            )
        workflow_error = self._validate_workflow(session, request)
        if workflow_error is not None:
            session.outcome = (
                VerificationOutcome.ESCALATED
                if session.risk_tier == RiskTier.HIGH
                else VerificationOutcome.DENIED
            )
            session.temporary_lock = session.risk_tier == RiskTier.MODERATE
            session.escalation_required = session.risk_tier == RiskTier.HIGH
            self.repository.save(session)
            return VerificationResult(
                session_id=session.session_id,
                transaction_id=session.transaction_id,
                outcome=session.outcome,
                risk_tier=session.risk_tier,
                temporary_lock=session.temporary_lock,
                escalation_required=session.escalation_required,
                reason_code=workflow_error,
                completed_at=now,
            )
        if request.outcome == VerificationOutcome.DENIED:
            session.outcome = (
                VerificationOutcome.ESCALATED
                if session.risk_tier == RiskTier.HIGH
                else VerificationOutcome.DENIED
            )
            reason = request.denial_reason or "USER_DENIED"
        else:
            session.outcome = VerificationOutcome.APPROVED
            reason = "VERIFICATION_APPROVED"
        session.temporary_lock = (
            session.risk_tier == RiskTier.MODERATE
            and session.outcome != VerificationOutcome.APPROVED
        )
        session.escalation_required = (
            session.risk_tier == RiskTier.HIGH and session.outcome != VerificationOutcome.APPROVED
        )
        self.repository.save(session)
        return VerificationResult(
            session_id=session.session_id,
            transaction_id=session.transaction_id,
            outcome=session.outcome,
            risk_tier=session.risk_tier,
            temporary_lock=session.temporary_lock,
            escalation_required=session.escalation_required,
            reason_code=reason,
            completed_at=now,
        )

    def expire_session(self, session_id: str) -> VerificationResult:
        session = self.repository.get(session_id)
        if session is None:
            raise KeyError("Verification session not found")
        return self.complete_session(
            session_id,
            VerificationCompletionRequest(
                token=self._token_for_expiration(session),
                outcome=VerificationOutcome.TIMED_OUT,
            ),
        )

    def _token_for_expiration(self, session: VerificationSession) -> str:
        raise ValueError(
            "Expiration requires the original token; tokens are never recoverable from storage"
        )


__all__ = [
    "BiometricAssertionVerifier",
    "DeterministicBiometricAssertionVerifier",
    "InMemoryVerificationRepository",
    "PushProvider",
    "RecordingPushProvider",
    "VerificationCompletionRequest",
    "VerificationRepository",
    "VerificationResult",
    "VerificationService",
    "VerificationSession",
    "VerificationSessionRequest",
]
