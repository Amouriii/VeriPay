"""HTTP entry point for the analyst feedback loop. PLAN §21."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_feedback_loop.config import settings
from veripay_feedback_loop.service import (
    FeedbackRecord,
    FeedbackRepository,
    FeedbackSubmission,
    InMemoryFeedbackRepository,
    ReviewLabel,
    export_feedback,
)


def create_app(repository: FeedbackRepository | None = None) -> FastAPI:
    """Build the append-only feedback API."""
    app = FastAPI(title="veripay-feedback_loop", version="0.1.0")
    feedback_repository = repository or InMemoryFeedbackRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-feedback_loop"}

    @app.post("/api/v1/feedback", response_model=FeedbackRecord)
    def submit(submission: FeedbackSubmission) -> FeedbackRecord:
        return feedback_repository.append(submission)

    @app.get("/api/v1/feedback", response_model=list[FeedbackRecord])
    def list_feedback(
        transaction_id: str | None = None, label: ReviewLabel | None = None
    ) -> list[FeedbackRecord]:
        return export_feedback(feedback_repository, transaction_id, label)

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
