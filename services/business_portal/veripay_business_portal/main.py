"""HTTP entry point for the Business Portal backend. Expansion Dev 5, §2."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_business_portal.config import settings
from veripay_business_portal.service import (
    BusinessDisputeTransitionRequest,
    BusinessDisputeView,
    BusinessPolicyView,
    BusinessPortalRepository,
    BusinessTransactionView,
    InMemoryBusinessPortalRepository,
    PortalAccessPolicy,
    SpendSummary,
    WebhookStatusView,
)


def create_app(repository: BusinessPortalRepository | None = None) -> FastAPI:
    """Build the Business Portal API with injectable service composition."""
    app = FastAPI(title="veripay-business_portal", version="0.1.0")
    business_repository = repository or InMemoryBusinessPortalRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-business_portal"}

    @app.get("/api/v1/business/access-policy", response_model=PortalAccessPolicy)
    def access_policy() -> PortalAccessPolicy:
        return PortalAccessPolicy(
            portal="BUSINESS", required_roles=["BUSINESS_ADMIN", "MERCHANT_ADMIN"]
        )

    @app.get("/api/v1/business/transactions", response_model=list[BusinessTransactionView])
    def list_transactions(merchant_id: str | None = None) -> list[BusinessTransactionView]:
        return business_repository.list_transactions(merchant_id)

    @app.get(
        "/api/v1/business/transactions/{transaction_id}", response_model=BusinessTransactionView
    )
    def get_transaction(transaction_id: str) -> BusinessTransactionView:
        view = business_repository.get_transaction(transaction_id)
        if view is None:
            raise HTTPException(status_code=404, detail="Transaction view not found")
        return view

    @app.get("/api/v1/business/spend/{merchant_id}", response_model=SpendSummary)
    def spend_summary(merchant_id: str, period: str = "DAILY") -> SpendSummary:
        summary = business_repository.get_spend_summary(merchant_id, period)
        if summary is None:
            raise HTTPException(status_code=404, detail="Spend summary not found")
        return summary

    @app.get("/api/v1/business/policies", response_model=list[BusinessPolicyView])
    def list_policies(merchant_id: str | None = None) -> list[BusinessPolicyView]:
        return business_repository.list_policies(merchant_id)

    @app.post(
        "/api/v1/business/policies",
        response_model=BusinessPolicyView,
        status_code=status.HTTP_201_CREATED,
    )
    def create_policy(policy: BusinessPolicyView) -> BusinessPolicyView:
        return business_repository.save_policy(policy)

    @app.get("/api/v1/business/policies/{lock_id}", response_model=BusinessPolicyView)
    def get_policy(lock_id: str) -> BusinessPolicyView:
        policy = business_repository.get_policy(lock_id)
        if policy is None:
            raise HTTPException(status_code=404, detail="Business policy not found")
        return policy

    @app.put("/api/v1/business/policies/{lock_id}", response_model=BusinessPolicyView)
    def replace_policy(lock_id: str, policy: BusinessPolicyView) -> BusinessPolicyView:
        if policy.lock_id != lock_id:
            raise HTTPException(status_code=400, detail="Path and body lock IDs must match")
        return business_repository.save_policy(policy)

    @app.delete("/api/v1/business/policies/{lock_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_policy(lock_id: str) -> None:
        if not business_repository.delete_policy(lock_id):
            raise HTTPException(status_code=404, detail="Business policy not found")

    @app.get("/api/v1/business/disputes", response_model=list[BusinessDisputeView])
    def list_disputes(merchant_id: str | None = None) -> list[BusinessDisputeView]:
        return business_repository.list_disputes(merchant_id)

    @app.get("/api/v1/business/disputes/{dispute_id}", response_model=BusinessDisputeView)
    def get_dispute(dispute_id: str) -> BusinessDisputeView:
        dispute = business_repository.get_dispute(dispute_id)
        if dispute is None:
            raise HTTPException(status_code=404, detail="Business dispute not found")
        return dispute

    @app.post(
        "/api/v1/business/disputes/{dispute_id}/transition",
        response_model=BusinessDisputeView,
    )
    def transition_dispute(
        dispute_id: str, request: BusinessDisputeTransitionRequest
    ) -> BusinessDisputeView:
        try:
            return business_repository.transition_dispute(dispute_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/business/webhooks", response_model=list[WebhookStatusView])
    def list_webhooks(merchant_id: str | None = None) -> list[WebhookStatusView]:
        return business_repository.list_webhooks(merchant_id)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
