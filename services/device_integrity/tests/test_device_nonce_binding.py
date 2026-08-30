from datetime import UTC, datetime

from veripay_common.enums import DevicePlatform, DeviceTrustState
from veripay_device_integrity.service import (
    AttestationRequest,
    AttestationStatus,
    DeviceChallengeRequest,
    DeviceIntegrityService,
)


def test_nonce_binding_mismatch_is_rejected_and_consumed() -> None:
    service = DeviceIntegrityService(
        now=lambda: datetime(2026, 1, 1, tzinfo=UTC), nonce_factory=lambda: "issued-nonce"
    )
    challenge = service.issue_challenge(
        DeviceChallengeRequest(device_id="device-1", platform=DevicePlatform.IOS)
    )
    request = AttestationRequest(
        challenge_id=challenge.challenge_id,
        nonce="wrong-nonce",
        device_id="device-1",
        platform=DevicePlatform.IOS,
        attestation_token="valid-attestation",
    )
    result = service.verify_attestation(request)
    replay = service.verify_attestation(request.model_copy(update={"nonce": challenge.nonce}))
    assert result.status == AttestationStatus.REJECTED
    assert result.trust_state == DeviceTrustState.UNKNOWN
    assert result.reason_code == "CHALLENGE_NONCE_MISMATCH"
    assert replay.reason_code == "CHALLENGE_REPLAYED"
