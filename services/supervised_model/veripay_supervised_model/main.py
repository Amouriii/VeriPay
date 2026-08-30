"""FastAPI app factory + gRPC server entry. PLAN §10,§20."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_supervised_model.config import settings
from veripay_supervised_model.service import ScoreRequest, ScoreResponse, evaluate


def create_app() -> FastAPI:
    """Build the scoring API."""
    app = FastAPI(title="veripay-supervised_model", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-supervised_model"}

    @app.post("/api/v1/score", response_model=ScoreResponse)
    def score(request: ScoreRequest) -> ScoreResponse:
        return evaluate(request)

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC)."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
