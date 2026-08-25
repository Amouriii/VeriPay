from fastapi.testclient import TestClient
from veripay_business_portal.main import create_app
from veripay_business_portal.service import BusinessDisputeView, InMemoryBusinessPortalRepository
from veripay_common.enums import DisputeReason, DisputeStatus


def test_business_policy_crud_and_dispute_transition() -> None:
    repository = InMemoryBusinessPortalRepository()
    repository.save_dispute(
        BusinessDisputeView(
            dispute_id="dispute-business",
            transaction_id="tx-business",
            merchant_id="merchant-business",
            amount_minor=200,
            currency="USD",
            status=DisputeStatus.OPENED,
            reason=DisputeReason.CONSUMER,
        )
    )
    client = TestClient(create_app(repository))
    create = client.post(
        "/api/v1/business/policies",
        json={
            "lock_id": "lock-business",
            "merchant_id": "merchant-business",
            "allowed_mccs": "5411,5812",
        },
    )
    assert create.status_code == 201
    assert (
        client.get("/api/v1/business/policies/lock-business").json()["allowed_mccs"] == "5411,5812"
    )
    assert (
        client.get("/api/v1/business/disputes?merchant_id=merchant-business").json()[0][
            "dispute_id"
        ]
        == "dispute-business"
    )
    transition = client.post(
        "/api/v1/business/disputes/dispute-business/transition",
        json={"status": "ACCEPTED", "actor": "merchant-admin"},
    )
    assert transition.status_code == 200
    assert transition.json()["status"] == "ACCEPTED"
    assert client.delete("/api/v1/business/policies/lock-business").status_code == 204
