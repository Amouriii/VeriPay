from datetime import UTC, datetime

from fastapi.testclient import TestClient
from veripay_feedback_loop.main import create_app
from veripay_feedback_loop.service import (
    FeedbackSubmission,
    InMemoryFeedbackRepository,
    ReviewLabel,
    export_feedback,
)


def _submission(key: str, label: ReviewLabel = ReviewLabel.CONFIRMED_FRAUD) -> FeedbackSubmission:
    return FeedbackSubmission(
        idempotency_key=key,
        transaction_id="tx-1",
        analyst_id="analyst-1",
        label=label,
        reason_codes=["VELOCITY"],
        decision_action="DECLINE",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_duplicate_submission_is_idempotent_and_append_only() -> None:
    repository = InMemoryFeedbackRepository()
    first = repository.append(_submission("key-1"))
    duplicate = repository.append(_submission("key-1", ReviewLabel.LEGITIMATE))
    assert duplicate == first
    assert len(repository.list()) == 1
    assert repository.list()[0].label == ReviewLabel.CONFIRMED_FRAUD


def test_feedback_export_filters_by_label() -> None:
    repository = InMemoryFeedbackRepository()
    repository.append(_submission("key-fraud"))
    repository.append(_submission("key-legit", ReviewLabel.LEGITIMATE))
    records = export_feedback(repository, label=ReviewLabel.LEGITIMATE)
    assert len(records) == 1
    assert records[0].transaction_id == "tx-1"


def test_feedback_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/feedback",
        json={
            "idempotency_key": "key-api",
            "transaction_id": "tx-api",
            "analyst_id": "analyst-api",
            "label": "LEGITIMATE",
            "decision_action": "ALLOW",
        },
    )
    assert response.status_code == 200
    assert response.json()["label"] == "LEGITIMATE"
