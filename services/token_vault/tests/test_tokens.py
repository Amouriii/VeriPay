from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from veripay_token_vault.main import create_app
from veripay_token_vault.service import InMemoryTokenRepository, TokenRecord, consume


def token_payload() -> dict[str, object]:
    return {
        "token_id": "vcn_001",
        "merchant_id": "merchant_001",
        "user_id": "user_001",
        "token_type": "SINGLE_USE",
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "max_uses": 1,
    }


def test_token_lifecycle_and_dcvv_validation() -> None:
    client = TestClient(create_app(InMemoryTokenRepository()))

    created = client.post("/api/v1/tokens", json=token_payload())
    assert created.status_code == 201
    assert "pan" not in created.json()
    assert "dcvv" not in created.json()

    valid = client.post(
        "/api/v1/tokens/dcvv/validate",
        json={"token_id": "vcn_001", "provided_dcvv": "123", "expected_dcvv": "123"},
    )
    assert valid.json()["status"] == "MATCH"

    consumed = client.post("/api/v1/tokens/vcn_001/consume")
    assert consumed.status_code == 200
    assert consumed.json()["status"] == "EXHAUSTED"

    rejected = client.post("/api/v1/tokens/vcn_001/consume")
    assert rejected.status_code == 409


def test_mismatched_dcvv_is_reported() -> None:
    client = TestClient(create_app(InMemoryTokenRepository()))
    client.post("/api/v1/tokens", json=token_payload())

    response = client.post(
        "/api/v1/tokens/dcvv/validate",
        json={"token_id": "vcn_001", "provided_dcvv": "123", "expected_dcvv": "999"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "MISMATCH"


def test_expired_token_cannot_be_consumed() -> None:
    token = TokenRecord(
        token_id="expired",
        merchant_id="merchant_001",
        user_id="user_001",
        token_type="SINGLE_USE",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    try:
        consume(token)
    except ValueError as exc:
        assert str(exc) == "Token is not usable"
    else:
        raise AssertionError("expired token was consumed")
