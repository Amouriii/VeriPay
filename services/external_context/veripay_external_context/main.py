"""HTTP entry point for external context. PLAN §17."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_external_context.config import settings
from veripay_external_context.service import (
    ExternalContextRequest,
    ExternalContextResponse,
    evaluate_external_context,
)


def create_app() -> FastAPI:
    """Build the external context API."""
    app = FastAPI(title="veripay-external_context", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-external_context"}

    @app.post("/api/v1/context/external/evaluate", response_model=ExternalContextResponse)
    def evaluate(request: ExternalContextRequest) -> ExternalContextResponse:
        return evaluate_external_context(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
