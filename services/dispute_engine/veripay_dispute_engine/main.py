"""HTTP entry point for dispute lifecycle management. Expansion Dev 5, §3."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from veripay_dispute_engine.config import settings
from veripay_dispute_engine.service import (
    DisputeCase,
    DisputeReason,
    DisputeReport,
    DisputeService,
    DisputeStatus,
    DisputeTransitionRequest,
    EvidenceSubmission,
)


def create_app(service: DisputeService | None = None) -> FastAPI:
    """Build the dispute API with injectable repository and sync boundaries."""
    app = FastAPI(title="veripay-dispute_engine", version="0.1.0")
    dispute_service = service or DisputeService()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-dispute_engine"}

    @app.get("/api/v1/disputes/report", response_model=DisputeReport)
    def report(
        status_filter: DisputeStatus | None = None,
        reason: DisputeReason | None = None,
    ) -> DisputeReport:
        return dispute_service.report(status_filter, reason)

    @app.get("/api/v1/disputes", response_model=list[DisputeCase])
    def list_disputes(
        status_filter: DisputeStatus | None = None,
        reason: DisputeReason | None = None,
    ) -> list[DisputeCase]:
        cases = dispute_service.repository.list_cases()
        if status_filter is not None:
            cases = [case for case in cases if case.status == status_filter]
        if reason is not None:
            cases = [case for case in cases if case.reason == reason]
        return cases

    @app.post(
        "/api/v1/disputes",
        response_model=DisputeCase,
        status_code=status.HTTP_201_CREATED,
    )
    def create_dispute(case: DisputeCase) -> DisputeCase:
        try:
            return dispute_service.create(case)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/disputes/{dispute_id}", response_model=DisputeCase)
    def get_dispute(dispute_id: str) -> DisputeCase:
        case = dispute_service.repository.get(dispute_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Dispute not found")
        return case

    @app.post("/api/v1/disputes/{dispute_id}/transition", response_model=DisputeCase)
    def transition(dispute_id: str, request: DisputeTransitionRequest) -> DisputeCase:
        try:
            return dispute_service.transition(dispute_id, request)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/disputes/{dispute_id}/evidence", response_model=EvidenceSubmission)
    def add_evidence(dispute_id: str, evidence: EvidenceSubmission) -> EvidenceSubmission:
        try:
            return dispute_service.add_evidence(dispute_id, evidence)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/api/v1/disputes/{dispute_id}/evidence",
        response_model=list[EvidenceSubmission],
    )
    def list_evidence(dispute_id: str) -> list[EvidenceSubmission]:
        if dispute_service.repository.get(dispute_id) is None:
            raise HTTPException(status_code=404, detail="Dispute not found")
        return dispute_service.repository.evidence_for(dispute_id)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
