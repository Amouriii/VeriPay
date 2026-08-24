"""FastAPI app factory + gRPC server entry. PLAN §22."""
from __future__ import annotations

from fastapi import FastAPI

from app.config import settings


def create_app() -> FastAPI:
    """Build the FastAPI application. Stubbed."""
    app = FastAPI(title="veripay-audit_store", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-audit_store"}

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC). Stubbed."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
