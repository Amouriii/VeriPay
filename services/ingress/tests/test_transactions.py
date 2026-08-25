from fastapi.testclient import TestClient
from veripay_ingress.main import create_app
from veripay_ingress.service import InMemoryTransactionRepository, Transaction, authorize


def test_submit_and_lookup_transaction() -> None:
    client = TestClient(create_app(InMemoryTransactionRepository()))
    payload = {
        "transaction_id": "tx_001",
        "user_id": "user_001",
        "amount_minor": 4999,
        "currency": "USD",
        "merchant_id": "merchant_001",
        "mti": "0100",
        "channel": "CARD_NOT_PRESENT",
    }

    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"
    assert response.json()["transaction_id"] == "tx_001"

    assert client.get("/api/v1/transactions").json() == [payload]
    risk = client.get("/api/v1/transactions/tx_001/risk")
    assert risk.status_code == 200
    assert risk.json()["band"] == "APPROVE"


def test_high_value_card_not_present_transaction_requires_challenge() -> None:
    transaction = Transaction(
        transaction_id="tx_high",
        user_id="user_001",
        amount_minor=100_000,
        currency="USD",
        channel="CARD_NOT_PRESENT",
    )

    response = authorize(transaction)
    assert response.decision == "CHALLENGE"
    assert response.risk_score == 45
    assert response.challenge_id is not None


def test_unknown_transaction_returns_not_found() -> None:
    client = TestClient(create_app(InMemoryTransactionRepository()))
    response = client.get("/api/v1/transactions/missing/risk")
    assert response.status_code == 404


def test_invalid_transaction_is_rejected() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/transactions",
        json={
            "transaction_id": "tx_001",
            "user_id": "user_001",
            "amount_minor": -1,
            "currency": "USD",
        },
    )
    assert response.status_code == 422
