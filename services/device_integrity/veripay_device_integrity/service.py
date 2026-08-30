"""Device attestation, challenge nonces, and GPV boundaries. PLAN §14, §15."""

from __future__ import annotations

import math
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field
from veripay_common.enums import DevicePlatform, DeviceTrustState, GpvOutcome


class AttestationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"


class DeviceChallengeRequest(BaseModel):
    device_id: str = Field(min_length=1)
    platform: DevicePlatform
    ttl_seconds: int = Field(default=90, ge=1, le=300)


class DeviceChallenge(BaseModel):
    challenge_id: str
    device_id: str
    platform: DevicePlatform
    nonce: str
    expires_at: datetime


class AttestationRequest(BaseModel):
    challenge_id: str = Field(min_length=1)
    nonce: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    platform: DevicePlatform
    attestation_token: str = Field(min_length=1)


class AttestationResult(BaseModel):
    challenge_id: str
    device_id: str
    platform: DevicePlatform
    status: AttestationStatus
    trust_state: DeviceTrustState
    reason_code: str


class GpvRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    current_latitude: float = Field(ge=-90, le=90)
    current_longitude: float = Field(ge=-180, le=180)
    previous_latitude: float | None = Field(default=None, ge=-90, le=90)
    previous_longitude: float | None = Field(default=None, ge=-180, le=180)
    elapsed_minutes: float = Field(default=0, ge=0)
    max_speed_kmh: float = Field(default=900, gt=0, le=2_000)


class GpvResult(BaseModel):
    transaction_id: str
    outcome: GpvOutcome
    available: bool
    distance_km: float | None = None
    permitted_distance_km: float | None = None
    reason_code: str


class AttestationProvider(Protocol):
    def verify(
        self, platform: DevicePlatform, token: str
    ) -> tuple[AttestationStatus, DeviceTrustState, str]: ...


class DeterministicAttestationProvider:
    """Test adapter; production must call Apple/Google attestation services."""

    def verify(
        self, platform: DevicePlatform, token: str
    ) -> tuple[AttestationStatus, DeviceTrustState, str]:
        del platform
        if token == "valid-attestation":
            return AttestationStatus.VERIFIED, DeviceTrustState.TRUSTED, "ATTESTATION_VERIFIED"
        if token == "untrusted-attestation":
            return AttestationStatus.VERIFIED, DeviceTrustState.UNTRUSTED, "ATTESTATION_UNTRUSTED"
        return (
            AttestationStatus.UNAVAILABLE,
            DeviceTrustState.UNKNOWN,
            "ATTESTATION_PROVIDER_UNAVAILABLE",
        )


@dataclass
class ChallengeRecord:
    challenge: DeviceChallenge
    consumed: bool = False


class DeviceRepository(Protocol):
    def save_challenge(self, record: ChallengeRecord) -> None: ...

    def get_challenge(self, challenge_id: str) -> ChallengeRecord | None: ...


@dataclass
class InMemoryDeviceRepository:
    challenges: dict[str, ChallengeRecord] = field(default_factory=dict)

    def save_challenge(self, record: ChallengeRecord) -> None:
        self.challenges[record.challenge.challenge_id] = record

    def get_challenge(self, challenge_id: str) -> ChallengeRecord | None:
        return self.challenges.get(challenge_id)


class DeviceIntegrityService:
    def __init__(
        self,
        repository: DeviceRepository | None = None,
        provider: AttestationProvider | None = None,
        now: Callable[[], datetime] | None = None,
        nonce_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository or InMemoryDeviceRepository()
        self.provider = provider or DeterministicAttestationProvider()
        self.now = now or (lambda: datetime.now(UTC))
        self.nonce_factory = nonce_factory or (lambda: secrets.token_hex(16))

    def issue_challenge(self, request: DeviceChallengeRequest) -> DeviceChallenge:
        challenge = DeviceChallenge(
            challenge_id=f"challenge_{uuid4().hex}",
            device_id=request.device_id,
            platform=request.platform,
            nonce=self.nonce_factory(),
            expires_at=self.now() + timedelta(seconds=request.ttl_seconds),
        )
        self.repository.save_challenge(ChallengeRecord(challenge=challenge))
        return challenge

    def verify_attestation(self, request: AttestationRequest) -> AttestationResult:
        record = self.repository.get_challenge(request.challenge_id)
        if record is None:
            return AttestationResult(
                challenge_id=request.challenge_id,
                device_id=request.device_id,
                platform=request.platform,
                status=AttestationStatus.REJECTED,
                trust_state=DeviceTrustState.UNKNOWN,
                reason_code="CHALLENGE_NOT_FOUND",
            )
        if record.consumed:
            reason = "CHALLENGE_REPLAYED"
            status = AttestationStatus.REJECTED
            trust = DeviceTrustState.UNKNOWN
        elif record.challenge.expires_at <= self.now():
            reason = "CHALLENGE_EXPIRED"
            status = AttestationStatus.REJECTED
            trust = DeviceTrustState.UNKNOWN
            record.consumed = True
        elif (
            record.challenge.device_id != request.device_id
            or record.challenge.platform != request.platform
        ):
            reason = "CHALLENGE_BINDING_MISMATCH"
            status = AttestationStatus.REJECTED
            trust = DeviceTrustState.UNKNOWN
            record.consumed = True
        elif record.challenge.nonce != request.nonce:
            reason = "CHALLENGE_NONCE_MISMATCH"
            status = AttestationStatus.REJECTED
            trust = DeviceTrustState.UNKNOWN
            record.consumed = True
        else:
            status, trust, reason = self.provider.verify(
                request.platform, request.attestation_token
            )
            record.consumed = True
        return AttestationResult(
            challenge_id=request.challenge_id,
            device_id=request.device_id,
            platform=request.platform,
            status=status,
            trust_state=trust,
            reason_code=reason,
        )


def _haversine_km(
    latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float
) -> float:
    radius_km = 6_371.0
    lat_a, lat_b = math.radians(latitude_a), math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(min(1.0, value)))


def evaluate_gpv(request: GpvRequest) -> GpvResult:
    """Compare consecutive locations without claiming a production geospatial provider."""
    if request.previous_latitude is None or request.previous_longitude is None:
        return GpvResult(
            transaction_id=request.transaction_id,
            outcome=GpvOutcome.LIKELY_MATCH,
            available=False,
            reason_code="PREVIOUS_LOCATION_UNAVAILABLE",
        )
    distance = _haversine_km(
        request.previous_latitude,
        request.previous_longitude,
        request.current_latitude,
        request.current_longitude,
    )
    permitted = request.max_speed_kmh * request.elapsed_minutes / 60
    outcome = GpvOutcome.MATCHED if distance <= permitted + 0.25 else GpvOutcome.MISMATCHED
    return GpvResult(
        transaction_id=request.transaction_id,
        outcome=outcome,
        available=True,
        distance_km=round(distance, 3),
        permitted_distance_km=round(permitted, 3),
        reason_code="GPV_MATCH" if outcome == GpvOutcome.MATCHED else "GPV_IMPOSSIBLE_TRAVEL",
    )
