"""FastAPI entry point for the analyst API composite service.

Exposes the analyst-facing surface from the architecture: ``/score``,
``/explain``, ``/customer/{cc_num}/profile``, ``/feedback``,
``/feedback/stats``, ``/retrain`` and ``/health``.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from veripay_analyst_api.clients import HttpPipelineClient, PipelineClient
from veripay_analyst_api.config import settings
from veripay_analyst_api.models import (
    AlertItem,
    AnalystScoreRequest,
    CustomerProfileResponse,
    ExplainResponse,
    FeedbackInput,
    FeedbackResult,
    FeedbackStats,
    HealthResponse,
    RetrainResponse,
    ScoreRequest,
    ScoreResponse,
)
from veripay_analyst_api.profiles import ProfileStore
from veripay_analyst_api.service import AnalystOrchestrator, create_orchestrator


def create_app(
    client: PipelineClient | None = None,
    store: ProfileStore | None = None,
    orchestrator: AnalystOrchestrator | None = None,
) -> FastAPI:
    """Build the analyst API with injectable boundaries for tests."""
    app = FastAPI(title="veripay-analyst_api", version="0.1.0")
    active = orchestrator or create_orchestrator(
        client=client or HttpPipelineClient(settings),
        store=store,
        settings=settings,
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return active.health()

    @app.get("/alerts", response_model=list[AlertItem])
    def alerts() -> list[AlertItem]:
        return active.alerts()

    @app.post("/score", response_model=ScoreResponse)
    def score(request: AnalystScoreRequest) -> ScoreResponse:
        try:
            if request.transaction is not None:
                return active.score(ScoreRequest(transaction=request.transaction))
            return active.lookup_score(request.transaction_id, request.cc_num)
        except LookupError:
            raise HTTPException(status_code=404, detail="Unknown scored transaction") from None
        except Exception as exc:  # noqa: BLE001 - surface as a clean 502
            raise HTTPException(
                status_code=502, detail=f"Scoring downstream unavailable: {exc}"
            ) from exc

    @app.post("/explain", response_model=ExplainResponse)
    def explain(request: AnalystScoreRequest) -> ExplainResponse:
        try:
            if request.transaction is not None:
                return active.explain(ScoreRequest(transaction=request.transaction))
            return active.lookup_explain(request.transaction_id, request.cc_num)
        except LookupError:
            raise HTTPException(status_code=404, detail="Unknown scored transaction") from None
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail=f"Explanation downstream unavailable: {exc}"
            ) from exc

    @app.get("/customer/{cc_num}/profile", response_model=CustomerProfileResponse)
    def customer_profile(cc_num: int) -> CustomerProfileResponse:
        return active.profile(cc_num)

    @app.get("/customer/{cc_num}/network")
    def customer_network(cc_num: int) -> dict:
        """Network (graph) context for a customer (PLAN §12).

        Lets an investigator browse a customer's ego graph + fraud-ring
        community directly from the profile page, without an open alert.
        """
        return active.network(cc_num)

    @app.post("/feedback", response_model=FeedbackResult)
    def feedback(input_: FeedbackInput) -> FeedbackResult:
        return active.submit_feedback(input_)

    @app.get("/feedback/stats", response_model=FeedbackStats)
    def feedback_stats() -> FeedbackStats:
        return active.feedback_stats()

    @app.post("/retrain", response_model=RetrainResponse)
    def retrain(version: str | None = None) -> RetrainResponse:
        try:
            return active.retrain(version)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail=f"Retrain upstream unavailable: {exc}"
            ) from exc

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
