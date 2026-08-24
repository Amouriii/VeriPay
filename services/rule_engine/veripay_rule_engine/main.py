"""FastAPI app factory + gRPC server entry. PLAN §13."""
from __future__ import annotations

from fastapi import FastAPI

from veripay_rule_engine.config import settings


def create_app() -> FastAPI:
    """Build the FastAPI application. Stubbed."""
    app = FastAPI(title="veripay-rule_engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-rule_engine"}

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC). Stubbed."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
