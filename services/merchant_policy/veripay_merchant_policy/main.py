"""HTTP entry point for merchant policy evaluation. Expansion §1 Dev4, §2."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_merchant_policy.config import settings
from veripay_merchant_policy.service import (
    InMemoryMerchantPolicyRepository,
    MerchantLockRule,
    MerchantPolicyRepository,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    evaluate_policy,
)


def create_app(repository: MerchantPolicyRepository | None = None) -> FastAPI:
    """Build the merchant policy API with injectable persistence."""
    app = FastAPI(title="veripay-merchant_policy", version="0.1.0")
    policy_repository = repository or InMemoryMerchantPolicyRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-merchant_policy"}

    @app.get("/api/v1/merchant/rules", response_model=list[MerchantLockRule])
    def list_rules() -> list[MerchantLockRule]:
        return policy_repository.list()

    @app.post(
        "/api/v1/merchant/rules",
        response_model=MerchantLockRule,
        status_code=status.HTTP_201_CREATED,
    )
    def create_rule(rule: MerchantLockRule) -> MerchantLockRule:
        return policy_repository.save(rule)

    @app.get("/api/v1/merchant/rules/{lock_id}", response_model=MerchantLockRule)
    def get_rule(lock_id: str) -> MerchantLockRule:
        rule = policy_repository.get(lock_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Merchant rule not found")
        return rule

    @app.put("/api/v1/merchant/rules/{lock_id}", response_model=MerchantLockRule)
    def replace_rule(lock_id: str, rule: MerchantLockRule) -> MerchantLockRule:
        if rule.lock_id != lock_id:
            raise HTTPException(status_code=400, detail="Path and body lock IDs must match")
        return policy_repository.save(rule)

    @app.delete("/api/v1/merchant/rules/{lock_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_rule(lock_id: str) -> None:
        if not policy_repository.delete(lock_id):
            raise HTTPException(status_code=404, detail="Merchant rule not found")

    @app.post("/api/v1/merchant/rules/evaluate", response_model=PolicyEvaluationResponse)
    def evaluate(request: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
        return evaluate_policy(request, policy_repository)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
