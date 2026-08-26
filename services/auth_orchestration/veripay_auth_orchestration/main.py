"""HTTP entry point for tier-driven mobile verification orchestration."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_auth_orchestration.config import settings
from veripay_auth_orchestration.service import (
    InMemoryVerificationRepository,
    VerificationCompletionRequest,
    VerificationRepository,
    VerificationResult,
    VerificationService,
    VerificationSessionRequest,
)


def create_app(
    repository: VerificationRepository | None = None,
    verification_service: VerificationService | None = None,
) -> FastAPI:
    """Build the verification API with injectable state and providers."""
    app = FastAPI(title="veripay-auth_orchestration", version="0.1.0")
    service = verification_service or VerificationService(
        repository=repository or InMemoryVerificationRepository()
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-auth_orchestration"}

    @app.post(
        "/api/v1/verification/sessions",
        response_model=dict[str, object],
        status_code=status.HTTP_201_CREATED,
    )
    def create_session(request: VerificationSessionRequest) -> dict[str, object]:
        session, token = service.create_session(request)
        # Return the one-use token only at issuance; never persist it.
        return {**session.model_dump(), "verification_token": token}

    @app.post(
        "/api/v1/verification/sessions/{session_id}/complete",
        response_model=VerificationResult,
    )
    def complete_session(
        session_id: str, request: VerificationCompletionRequest
    ) -> VerificationResult:
        try:
            return service.complete_session(session_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
