"""HTTP entry point for the FI Ops portal backend. Expansion Dev 5, §2."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from veripay_fi_ops_portal.config import settings
from veripay_fi_ops_portal.service import (
    FiOpsRepository,
    InMemoryFiOpsRepository,
    OpsAuditEventView,
    OpsDisputeTransitionRequest,
    OpsDisputeView,
    OpsTransactionStateView,
    OpsTransactionView,
    PortalAccessPolicy,
    RegulatoryReport,
    build_regulatory_report,
)


def create_app(repository: FiOpsRepository | None = None) -> FastAPI:
    """Build the FI Ops API with injectable service composition."""
    app = FastAPI(title="veripay-fi_ops_portal", version="0.1.0")
    ops_repository = repository or InMemoryFiOpsRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-fi_ops_portal"}

    @app.get("/api/v1/fi-ops/access-policy", response_model=PortalAccessPolicy)
    def access_policy() -> PortalAccessPolicy:
        return PortalAccessPolicy(portal="FI_OPS", required_roles=["FI_OPS", "ADMIN"])

    @app.get("/api/v1/fi-ops/transactions", response_model=list[OpsTransactionView])
    def list_transactions() -> list[OpsTransactionView]:
        return ops_repository.list_transactions()

    @app.get("/api/v1/fi-ops/transactions/{transaction_id}", response_model=OpsTransactionView)
    def get_transaction(transaction_id: str) -> OpsTransactionView:
        view = ops_repository.get_transaction(transaction_id)
        if view is None:
            raise HTTPException(status_code=404, detail="Transaction view not found")
        return view

    @app.get(
        "/api/v1/fi-ops/transactions/{transaction_id}/audit",
        response_model=list[OpsAuditEventView],
    )
    def list_audit_events(transaction_id: str) -> list[OpsAuditEventView]:
        if ops_repository.get_transaction(transaction_id) is None:
            raise HTTPException(status_code=404, detail="Transaction view not found")
        return ops_repository.audit_events_for(transaction_id)

    @app.get(
        "/api/v1/fi-ops/transactions/{transaction_id}/state",
        response_model=OpsTransactionStateView,
    )
    def get_transaction_state(transaction_id: str) -> OpsTransactionStateView:
        state = ops_repository.get_transaction_state(transaction_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Transaction state not found")
        return state

    @app.get("/api/v1/fi-ops/disputes", response_model=list[OpsDisputeView])
    def list_disputes() -> list[OpsDisputeView]:
        return ops_repository.list_disputes()

    @app.post(
        "/api/v1/fi-ops/disputes/{dispute_id}/transition",
        response_model=OpsDisputeView,
    )
    def transition_dispute(dispute_id: str, request: OpsDisputeTransitionRequest) -> OpsDisputeView:
        try:
            return ops_repository.transition_dispute(dispute_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/fi-ops/reports/regulatory", response_model=RegulatoryReport)
    def regulatory_report() -> RegulatoryReport:
        return build_regulatory_report(ops_repository)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
