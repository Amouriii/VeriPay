"""HTTP entry point for risk fusion. PLAN §18."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_risk_fusion.config import settings
from veripay_risk_fusion.service import FusionRequest, FusionResponse, fuse_risk


def create_app() -> FastAPI:
    """Build the risk fusion API."""
    app = FastAPI(title="veripay-risk_fusion", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-risk_fusion"}

    @app.post("/api/v1/risk/fuse", response_model=FusionResponse)
    def fuse(request: FusionRequest) -> FusionResponse:
        return fuse_risk(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
