"""HTTP entry point for audit persistence. PLAN §22."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_audit_store.config import settings
from veripay_audit_store.service import (
    AuditEvent,
    AuditRepository,
    InMemoryAuditRepository,
    TransactionState,
)


def create_app(repository: AuditRepository | None = None) -> FastAPI:
    """Build the API with an injectable audit repository."""
    app = FastAPI(title="veripay-audit_store", version="0.1.0")
    audit_repository = repository or InMemoryAuditRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-audit_store"}

    @app.post(
        "/api/v1/audit/events",
        response_model=AuditEvent,
        status_code=status.HTTP_201_CREATED,
    )
    def record_event(event: AuditEvent) -> AuditEvent:
        try:
            return audit_repository.record_event(event)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/audit/transactions/{transaction_id}/events", response_model=list[AuditEvent])
    def list_events(transaction_id: str) -> list[AuditEvent]:
        return audit_repository.events_for(transaction_id)

    @app.put("/api/v1/audit/transactions/{transaction_id}/state", response_model=TransactionState)
    def save_state(transaction_id: str, state: TransactionState) -> TransactionState:
        if state.transaction_id != transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID does not match path")
        return audit_repository.save_state(state)

    @app.get("/api/v1/audit/transactions/{transaction_id}/state", response_model=TransactionState)
    def get_state(transaction_id: str) -> TransactionState:
        state = audit_repository.get_state(transaction_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Transaction state not found")
        return state

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
