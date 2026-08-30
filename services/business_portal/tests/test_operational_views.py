from fastapi.testclient import TestClient
from veripay_business_portal.auth import ConfigTokenAuthenticator
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
    authenticator = ConfigTokenAuthenticator({"t": frozenset({"BUSINESS_ADMIN", "MERCHANT_ADMIN"})})
    client = TestClient(create_app(repository, authenticator=authenticator))
    auth = {"Authorization": "Bearer t"}
    create = client.post(
        "/api/v1/business/policies",
        json={
            "lock_id": "lock-business",
            "merchant_id": "merchant-business",
            "allowed_mccs": "5411,5812",
        },
        headers=auth,
    )
    assert create.status_code == 201
    assert (
        client.get("/api/v1/business/policies/lock-business", headers=auth).json()["allowed_mccs"]
        == "5411,5812"
    )
    assert (
        client.get("/api/v1/business/disputes?merchant_id=merchant-business", headers=auth).json()[
            0
        ]["dispute_id"]
        == "dispute-business"
    )
    transition = client.post(
        "/api/v1/business/disputes/dispute-business/transition",
        json={"status": "ACCEPTED", "actor": "merchant-admin"},
        headers=auth,
    )
    assert transition.status_code == 200
    assert transition.json()["status"] == "ACCEPTED"
    assert client.delete("/api/v1/business/policies/lock-business", headers=auth).status_code == 204
