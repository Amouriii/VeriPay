"""FastAPI app factory + gRPC server entry. Expansion §1 Dev5, §2"""

from __future__ import annotations

from fastapi import FastAPI

from veripay_business_portal.config import settings


def create_app() -> FastAPI:
    """Build the FastAPI application. Stubbed."""
    app = FastAPI(title="veripay-business_portal", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-business_portal"}

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC). Stubbed."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
