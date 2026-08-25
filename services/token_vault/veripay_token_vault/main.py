"""HTTP entry point for the PCI-safe token vault boundary."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_token_vault.config import settings
from veripay_token_vault.service import (
    DcvvValidationRequest,
    DcvvValidationResponse,
    InMemoryTokenRepository,
    TokenCreateRequest,
    TokenRecord,
    TokenRepository,
    consume,
    validate_dcvv,
)


def create_app(repository: TokenRepository | None = None) -> FastAPI:
    """Build the API with an injectable token repository."""
    app = FastAPI(title="veripay-token_vault", version="0.1.0")
    token_repository = repository or InMemoryTokenRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-token_vault"}

    @app.get("/api/v1/tokens", response_model=list[TokenRecord])
    def list_tokens() -> list[TokenRecord]:
        return token_repository.list()

    @app.post(
        "/api/v1/tokens",
        response_model=TokenRecord,
        status_code=status.HTTP_201_CREATED,
    )
    def create_token(request: TokenCreateRequest) -> TokenRecord:
        token = TokenRecord(**request.model_dump())
        return token_repository.save(token)

    @app.post("/api/v1/tokens/{token_id}/consume", response_model=TokenRecord)
    def consume_token(token_id: str) -> TokenRecord:
        token = token_repository.get(token_id)
        if token is None:
            raise HTTPException(status_code=404, detail="Token not found")
        try:
            updated = consume(token)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        token_repository.save(updated)
        return updated

    @app.post("/api/v1/tokens/dcvv/validate", response_model=DcvvValidationResponse)
    def validate_token_dcvv(request: DcvvValidationRequest) -> DcvvValidationResponse:
        return validate_dcvv(request, token_repository)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
