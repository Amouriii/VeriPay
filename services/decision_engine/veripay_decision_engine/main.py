"""HTTP entry point for the cost-aware decision engine. PLAN §19."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_decision_engine.config import settings
from veripay_decision_engine.service import DecisionRequest, DecisionResponse, decide


def create_app() -> FastAPI:
    """Build the decision evaluation API."""
    app = FastAPI(title="veripay-decision_engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-decision_engine"}

    @app.post("/api/v1/decision/evaluate", response_model=DecisionResponse)
    def evaluate(request: DecisionRequest) -> DecisionResponse:
        return decide(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
