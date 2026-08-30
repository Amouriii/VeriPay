"""FastAPI app factory + gRPC server entry. PLAN §12.

Implements the network-analysis fourth scoring axis described in
``docs/network-analysis.md``. The service accumulates observed transactions
into an in-memory customer ↔ merchant graph and, for each scored transaction,
returns a network risk score, analyst-readable findings, and an ego-graph
payload for the analyst console.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.extract import ObservedTransaction, network_context
from veripay_graph_engine.config import settings
from veripay_graph_engine.store import get_store

# --- wire models -----------------------------------------------------------


class GraphObserveRequest(BaseModel):
    """A transaction observed into the graph."""

    transaction_id: str = Field(min_length=1)
    cc_num: int = Field(ge=1)
    merchant: str = Field(min_length=1)
    amount: float = Field(ge=0)
    timestamp: datetime
    location: list[float] | None = None  # [lat, lon]
    flagged: bool = False  # set when the customer is confirmed-fraud


class GraphObserveResponse(BaseModel):
    status: str
    transaction_id: str
    recorded: bool = True


class GraphScoreRequest(GraphObserveRequest):
    """A transaction to score (also observed into the graph)."""


class GraphScoreResponse(BaseModel):
    transaction_id: str
    cc_num: int
    network_risk_score: float = Field(ge=0, le=1)
    available: bool
    findings: list[str] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)
    ego: dict[str, Any] = Field(default_factory=dict)


# --- helpers ---------------------------------------------------------------


def _observe(payload: GraphObserveRequest) -> None:
    loc: tuple[float, float] | None = None
    if payload.location and len(payload.location) == 2:
        loc = (float(payload.location[0]), float(payload.location[1]))
    get_store().observe(
        ObservedTransaction(
            transaction_id=payload.transaction_id,
            cc_num=payload.cc_num,
            merchant=payload.merchant,
            amount=payload.amount,
            timestamp=payload.timestamp,
            location=loc,
            flagged=payload.flagged,
        )
    )


# --- app -------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(title="veripay-graph_engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, Any]:
        store = get_store()
        return {
            "status": "ok",
            "service": "veripay-graph_engine",
            "customers": len(store.customers()),
            "model_name": "graph",
            "model_version": "v1",
            "model_available": True,
            "fallback": False,
        }

    @app.post("/api/v1/graph/observe", response_model=GraphObserveResponse)
    def observe(request: GraphObserveRequest) -> GraphObserveResponse:
        _observe(request)
        return GraphObserveResponse(
            status="recorded", transaction_id=request.transaction_id
        )

    @app.post("/api/v1/graph/score", response_model=GraphScoreResponse)
    def score(request: GraphScoreRequest) -> GraphScoreResponse:
        _observe(request)
        ctx = network_context(
            get_store(), request.cc_num, window_days=settings.NETWORK_WINDOW_DAYS
        )
        return GraphScoreResponse(
            transaction_id=request.transaction_id,
            cc_num=request.cc_num,
            network_risk_score=ctx["network_risk_score"],
            available=ctx["available"],
            findings=ctx["findings"],
            features=ctx["features"],
            ego=ctx["ego"],
        )

    @app.get("/api/v1/graph/ego/{cc_num}")
    def ego(cc_num: int) -> dict[str, Any]:
        if cc_num <= 0:
            raise HTTPException(status_code=422, detail="cc_num must be positive")
        return network_context(
            get_store(), cc_num, window_days=settings.NETWORK_WINDOW_DAYS
        )

    @app.get("/api/v1/graph/community/{cc_num}")
    def community(cc_num: int) -> dict[str, Any]:
        """Full Louvain-style community + aggregate cluster stats (PLAN §12).

        Unlike the ego endpoint (1-hop peers), this renders the entire
        connected component of the shared-merchant projection the customer
        belongs to — the fraud-ring overview an investigator needs.
        """
        if cc_num <= 0:
            raise HTTPException(status_code=422, detail="cc_num must be positive")
        store = get_store()
        return store.community(cc_num, window_days=settings.NETWORK_WINDOW_DAYS)

    return app


app = create_app()


def main() -> None:
    """Run the service (HTTP + gRPC)."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
