"""HTTP entry point for financial context. PLAN §17."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_financial_context.config import settings
from veripay_financial_context.service import (
    FinancialContextRequest,
    FinancialContextResponse,
    evaluate_financial_context,
)


def create_app() -> FastAPI:
    """Build the financial context API."""
    app = FastAPI(title="veripay-financial_context", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-financial_context"}

    @app.post("/api/v1/context/financial/evaluate", response_model=FinancialContextResponse)
    def evaluate(request: FinancialContextRequest) -> FinancialContextResponse:
        return evaluate_financial_context(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
