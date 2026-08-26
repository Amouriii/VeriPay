"""HTTP entry point for device integrity and GPV. PLAN §14, §15."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_device_integrity.config import settings
from veripay_device_integrity.service import (
    AttestationRequest,
    AttestationResult,
    DeviceChallenge,
    DeviceChallengeRequest,
    DeviceIntegrityService,
    GpvRequest,
    GpvResult,
    evaluate_gpv,
)


def create_app(service: DeviceIntegrityService | None = None) -> FastAPI:
    """Build the device integrity API with injectable provider state."""
    app = FastAPI(title="veripay-device_integrity", version="0.1.0")
    integrity_service = service or DeviceIntegrityService()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-device_integrity"}

    @app.post("/api/v1/device/challenges", response_model=DeviceChallenge)
    def issue_challenge(request: DeviceChallengeRequest) -> DeviceChallenge:
        return integrity_service.issue_challenge(request)

    @app.post("/api/v1/device/attestation", response_model=AttestationResult)
    def verify_attestation(request: AttestationRequest) -> AttestationResult:
        return integrity_service.verify_attestation(request)

    @app.post("/api/v1/device/gpv", response_model=GpvResult)
    def evaluate_location(request: GpvRequest) -> GpvResult:
        return evaluate_gpv(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
