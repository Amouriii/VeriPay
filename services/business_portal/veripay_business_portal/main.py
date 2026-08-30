"""HTTP entry point for the Business Portal backend. Expansion Dev 5, §2."""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, status

from veripay_business_portal.auth import (
    AuthError,
    ConfigTokenAuthenticator,
    TokenAuthenticator,
    require_roles,
)
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

BUSINESS_ROLES = frozenset({"BUSINESS_ADMIN", "MERCHANT_ADMIN"})


def create_app(
    repository: BusinessPortalRepository | None = None,
    authenticator: TokenAuthenticator | None = None,
) -> FastAPI:
    """Build the Business Portal API with injectable service composition."""
    app = FastAPI(title="veripay-business_portal", version="0.1.0")
    business_repository = repository or InMemoryBusinessPortalRepository()
    auth = authenticator or ConfigTokenAuthenticator()

    def guard(authorization: str | None) -> None:
        """Enforce bearer auth + role membership; raises AuthError to deny."""
        try:
            require_roles(authorization, auth, BUSINESS_ROLES)
        except AuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-business_portal"}

    @app.get("/api/v1/business/access-policy", response_model=PortalAccessPolicy)
    def access_policy() -> PortalAccessPolicy:
        return PortalAccessPolicy(
            portal="BUSINESS", required_roles=["BUSINESS_ADMIN", "MERCHANT_ADMIN"]
        )

    @app.get("/api/v1/business/transactions", response_model=list[BusinessTransactionView])
    def list_transactions(
        merchant_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> list[BusinessTransactionView]:
        guard(authorization)
        return business_repository.list_transactions(merchant_id)

    @app.get(
        "/api/v1/business/transactions/{transaction_id}", response_model=BusinessTransactionView
    )
    def get_transaction(
        transaction_id: str, authorization: str | None = Header(default=None)
    ) -> BusinessTransactionView:
        guard(authorization)
        view = business_repository.get_transaction(transaction_id)
        if view is None:
            raise HTTPException(status_code=404, detail="Transaction view not found")
        return view

    @app.get("/api/v1/business/spend/{merchant_id}", response_model=SpendSummary)
    def spend_summary(
        merchant_id: str,
        period: str = "DAILY",
        authorization: str | None = Header(default=None),
    ) -> SpendSummary:
        guard(authorization)
        summary = business_repository.get_spend_summary(merchant_id, period)
        if summary is None:
            raise HTTPException(status_code=404, detail="Spend summary not found")
        return summary

    @app.get("/api/v1/business/policies", response_model=list[BusinessPolicyView])
    def list_policies(
        merchant_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> list[BusinessPolicyView]:
        guard(authorization)
        return business_repository.list_policies(merchant_id)

    @app.post(
        "/api/v1/business/policies",
        response_model=BusinessPolicyView,
        status_code=status.HTTP_201_CREATED,
    )
    def create_policy(
        policy: BusinessPolicyView,
        authorization: str | None = Header(default=None),
    ) -> BusinessPolicyView:
        guard(authorization)
        return business_repository.save_policy(policy)

    @app.get("/api/v1/business/policies/{lock_id}", response_model=BusinessPolicyView)
    def get_policy(
        lock_id: str, authorization: str | None = Header(default=None)
    ) -> BusinessPolicyView:
        guard(authorization)
        policy = business_repository.get_policy(lock_id)
        if policy is None:
            raise HTTPException(status_code=404, detail="Business policy not found")
        return policy

    @app.put("/api/v1/business/policies/{lock_id}", response_model=BusinessPolicyView)
    def replace_policy(
        lock_id: str,
        policy: BusinessPolicyView,
        authorization: str | None = Header(default=None),
    ) -> BusinessPolicyView:
        guard(authorization)
        if policy.lock_id != lock_id:
            raise HTTPException(status_code=400, detail="Path and body lock IDs must match")
        return business_repository.save_policy(policy)

    @app.delete("/api/v1/business/policies/{lock_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_policy(lock_id: str, authorization: str | None = Header(default=None)) -> None:
        guard(authorization)
        if not business_repository.delete_policy(lock_id):
            raise HTTPException(status_code=404, detail="Business policy not found")

    @app.get("/api/v1/business/disputes", response_model=list[BusinessDisputeView])
    def list_disputes(
        merchant_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> list[BusinessDisputeView]:
        guard(authorization)
        return business_repository.list_disputes(merchant_id)

    @app.get("/api/v1/business/disputes/{dispute_id}", response_model=BusinessDisputeView)
    def get_dispute(
        dispute_id: str, authorization: str | None = Header(default=None)
    ) -> BusinessDisputeView:
        guard(authorization)
        dispute = business_repository.get_dispute(dispute_id)
        if dispute is None:
            raise HTTPException(status_code=404, detail="Business dispute not found")
        return dispute

    @app.post(
        "/api/v1/business/disputes/{dispute_id}/transition",
        response_model=BusinessDisputeView,
    )
    def transition_dispute(
        dispute_id: str,
        request: BusinessDisputeTransitionRequest,
        authorization: str | None = Header(default=None),
    ) -> BusinessDisputeView:
        guard(authorization)
        try:
            return business_repository.transition_dispute(dispute_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/business/webhooks", response_model=list[WebhookStatusView])
    def list_webhooks(
        merchant_id: str | None = None,
        authorization: str | None = Header(default=None),
    ) -> list[WebhookStatusView]:
        guard(authorization)
        return business_repository.list_webhooks(merchant_id)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
