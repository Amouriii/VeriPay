from datetime import UTC, datetime

from fastapi.testclient import TestClient
from veripay_dispute_engine.main import create_app
from veripay_dispute_engine.service import (
    DisputeCase,
    DisputeReason,
    DisputeService,
    DisputeStatus,
    DisputeTransitionRequest,
    EvidenceSubmission,
    InMemoryDisputeRepository,
)


def _case(dispute_id: str = "dispute-1") -> DisputeCase:
    return DisputeCase(
        dispute_id=dispute_id,
        idempotency_key=f"key-{dispute_id}",
        transaction_id="tx-1",
        merchant_id="merchant-1",
        amount_minor=1_000,
        currency="usd",
        status=DisputeStatus.OPENED,
        reason=DisputeReason.FRAUD,
        opened_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_create_is_idempotent_and_normalizes_currency() -> None:
    repository = InMemoryDisputeRepository()
    service = DisputeService(repository=repository)
    first = service.create(_case())
    duplicate = service.create(_case())
    assert first == duplicate
    assert first.currency == "USD"
    assert len(repository.list()) == 1


def test_lifecycle_accepts_valid_transition_and_rejects_invalid_transition() -> None:
    service = DisputeService(repository=InMemoryDisputeRepository())
    service.create(_case())
    represented = service.transition(
        "dispute-1", DisputeTransitionRequest(status=DisputeStatus.REPRESENTED, actor="merchant-1")
    )
    assert represented.status == DisputeStatus.REPRESENTED
    try:
        service.transition(
            "dispute-1", DisputeTransitionRequest(status=DisputeStatus.OPENED, actor="analyst-1")
        )
    except ValueError as exc:
        assert "Invalid transition" in str(exc)
    else:
        raise AssertionError("Expected invalid transition to fail")


def test_evidence_and_report() -> None:
    service = DisputeService(repository=InMemoryDisputeRepository())
    service.create(_case())
    service.add_evidence(
        "dispute-1",
        EvidenceSubmission(
            evidence_id="evidence-1",
            dispute_id="dispute-1",
            evidence_type="TRANSACTION_LOG",
            provider_reference="vault-ref-1",
            submitted_by="analyst-1",
        ),
    )
    report = service.report()
    assert report.case_count == 1
    assert report.amount_minor == 1_000
    assert report.counts_by_reason[DisputeReason.FRAUD] == 1


def test_dispute_api() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/disputes",
        json={
            "dispute_id": "dispute-api",
            "idempotency_key": "key-api",
            "transaction_id": "tx-api",
            "amount_minor": 500,
            "currency": "USD",
            "status": "OPENED",
            "reason": "CONSUMER",
        },
    )
    assert response.status_code == 201
    transition = client.post(
        "/api/v1/disputes/dispute-api/transition",
        json={"status": "REPRESENTED", "actor": "merchant-api"},
    )
    assert transition.status_code == 200
    assert transition.json()["status"] == "REPRESENTED"
    report = client.get("/api/v1/disputes/report")
    assert report.status_code == 200
    assert report.json()["case_count"] == 1
