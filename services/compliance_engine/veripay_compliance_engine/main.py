"""HTTP entry point for compliance evaluation. Expansion §1 Dev4, §2."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_compliance_engine.config import settings
from veripay_compliance_engine.service import (
    ComplianceRequest,
    ComplianceResponse,
    evaluate_compliance,
)


def create_app() -> FastAPI:
    """Build the compliance API."""
    app = FastAPI(title="veripay-compliance_engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-compliance_engine"}

    @app.post("/api/v1/compliance/evaluate", response_model=ComplianceResponse)
    def evaluate(request: ComplianceRequest) -> ComplianceResponse:
        return evaluate_compliance(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
