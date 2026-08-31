"""HTTP entry point for transaction ingestion. PLAN §5,§6.1."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_ingress.config import settings
from veripay_ingress.service import (
    AuthorizationResponse,
    InMemoryTransactionRepository,
    RiskScore,
    Transaction,
    TransactionRepository,
    authorize,
    calculate_risk,
)


def create_app(repository: TransactionRepository | None = None) -> FastAPI:
    """Build the API with an injectable persistence boundary."""
    app = FastAPI(title="veripay-ingress", version="0.1.0")
    transaction_repository = repository or InMemoryTransactionRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-ingress"}

    @app.get(
        "/api/v1/transactions",
        response_model=list[Transaction],
        response_model_exclude_none=True,
    )
    def list_transactions() -> list[Transaction]:
        return transaction_repository.list()

    @app.post(
        "/api/v1/transactions",
        response_model=AuthorizationResponse,
        status_code=status.HTTP_200_OK,
    )
    def submit_transaction(transaction: Transaction) -> AuthorizationResponse:
        transaction_repository.save(transaction)
        return authorize(transaction, settings=settings)

    @app.get("/api/v1/transactions/{transaction_id}/risk", response_model=RiskScore)
    def transaction_risk(transaction_id: str) -> RiskScore:
        transaction = transaction_repository.get(transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return calculate_risk(transaction, settings=settings)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
