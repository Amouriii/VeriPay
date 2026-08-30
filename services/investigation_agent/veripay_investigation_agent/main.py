"""FastAPI app factory + gRPC server entry. PLAN §20."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_investigation_agent.config import settings
from veripay_investigation_agent.service import (
    InvestigationRequest,
    LlmExplanation,
    evaluate,
)


def create_app() -> FastAPI:
    """Build the investigation/explanation API."""
    app = FastAPI(title="veripay-investigation_agent", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-investigation_agent"}

    @app.post("/api/v1/investigate", response_model=LlmExplanation)
    def investigate(request: InvestigationRequest) -> LlmExplanation:
        return evaluate(request)

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC)."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
