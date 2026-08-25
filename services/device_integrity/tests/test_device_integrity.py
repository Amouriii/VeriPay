from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from veripay_common.enums import DevicePlatform, DeviceTrustState, GpvOutcome
from veripay_device_integrity.main import create_app
from veripay_device_integrity.service import (
    AttestationRequest,
    AttestationStatus,
    DeviceChallengeRequest,
    DeviceIntegrityService,
    GpvRequest,
    evaluate_gpv,
)


def test_challenge_is_single_use() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = DeviceIntegrityService(now=lambda: now, nonce_factory=lambda: "nonce")
    challenge = service.issue_challenge(
        DeviceChallengeRequest(device_id="device-1", platform=DevicePlatform.IOS)
    )
    request = AttestationRequest(
        challenge_id=challenge.challenge_id,
        nonce=challenge.nonce,
        device_id="device-1",
        platform=DevicePlatform.IOS,
        attestation_token="valid-attestation",
    )
    first = service.verify_attestation(request)
    second = service.verify_attestation(request)
    assert first.status == AttestationStatus.VERIFIED
    assert second.reason_code == "CHALLENGE_REPLAYED"


def test_expired_challenge_is_rejected() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = DeviceIntegrityService(now=lambda: now)
    challenge = service.issue_challenge(
        DeviceChallengeRequest(device_id="device-1", platform=DevicePlatform.ANDROID, ttl_seconds=1)
    )
    service.now = lambda: now + timedelta(seconds=2)
    result = service.verify_attestation(
        AttestationRequest(
            challenge_id=challenge.challenge_id,
            nonce=challenge.nonce,
            device_id="device-1",
            platform=DevicePlatform.ANDROID,
            attestation_token="valid-attestation",
        )
    )
    assert result.reason_code == "CHALLENGE_EXPIRED"
    assert result.trust_state == DeviceTrustState.UNKNOWN


def test_gpv_detects_impossible_travel() -> None:
    result = evaluate_gpv(
        GpvRequest(
            transaction_id="tx-1",
            previous_latitude=40.7128,
            previous_longitude=-74.0060,
            current_latitude=51.5074,
            current_longitude=-0.1278,
            elapsed_minutes=10,
        )
    )
    assert result.outcome == GpvOutcome.MISMATCHED
    assert result.available is True


def test_device_endpoints() -> None:
    client = TestClient(create_app())
    challenge_response = client.post(
        "/api/v1/device/challenges",
        json={"device_id": "device-api", "platform": "ios"},
    )
    assert challenge_response.status_code == 200
    challenge_id = challenge_response.json()["challenge_id"]
    attestation_response = client.post(
        "/api/v1/device/attestation",
        json={
            "challenge_id": challenge_id,
            "nonce": challenge_response.json()["nonce"],
            "device_id": "device-api",
            "platform": "ios",
            "attestation_token": "valid-attestation",
        },
    )
    assert attestation_response.status_code == 200
    assert attestation_response.json()["status"] == "VERIFIED"
