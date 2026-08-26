"""HTTP entry point for deterministic rule evaluation. PLAN §13."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_rule_engine.config import settings
from veripay_rule_engine.service import (
    RuleEvaluationRequest,
    RuleEvaluationResponse,
    evaluate_rules,
)


def create_app() -> FastAPI:
    """Build the rule evaluation API."""
    app = FastAPI(title="veripay-rule_engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-rule_engine"}

    @app.post("/api/v1/rules/evaluate", response_model=RuleEvaluationResponse)
    def evaluate(request: RuleEvaluationRequest) -> RuleEvaluationResponse:
        return evaluate_rules(request)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
