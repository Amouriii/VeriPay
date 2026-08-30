"""Auth enforcement tests for the Business portal boundary (Expansion §1 item 6)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from veripay_business_portal.auth import (
    AuthError,
    ConfigTokenAuthenticator,
    _parse_token_map,
    extract_bearer_token,
    require_roles,
)
from veripay_business_portal.main import create_app


def _payload() -> dict[str, Any]:
    return {
        "lock_id": "lock-1",
        "merchant_id": "m-1",
        "allowed_mccs": "5411",
        "max_spend_per_txn_minor": 10_000,
        "daily_spend_limit_minor": 100_000,
        "enforce_merchant_lock": True,
    }


def _client() -> TestClient:
    authenticator = ConfigTokenAuthenticator(
        {
            "admin-token": frozenset({"BUSINESS_ADMIN", "MERCHANT_ADMIN"}),
            "merchant-token": frozenset({"MERCHANT_ADMIN"}),
            "wrong-role-token": frozenset({"FI_OPS"}),
            "no-role-token": frozenset(),
        }
    )
    return TestClient(create_app(authenticator=authenticator))


def test_health_is_unauthenticated() -> None:
    assert _client().get("/health").status_code == 200


def test_access_policy_is_unauthenticated() -> None:
    response = _client().get("/api/v1/business/access-policy")
    assert response.status_code == 200
    assert response.json()["required_roles"] == ["BUSINESS_ADMIN", "MERCHANT_ADMIN"]


def test_missing_token_is_unauthorized() -> None:
    response = _client().get("/api/v1/business/transactions")
    assert response.status_code == 401


def test_non_bearer_scheme_is_unauthorized() -> None:
    response = _client().get(
        "/api/v1/business/transactions", headers={"Authorization": "Basic abc"}
    )
    assert response.status_code == 401


def test_unknown_token_is_unauthorized() -> None:
    response = _client().get(
        "/api/v1/business/transactions", headers={"Authorization": "Bearer nope"}
    )
    assert response.status_code == 401


def test_token_without_required_role_is_forbidden() -> None:
    response = _client().get(
        "/api/v1/business/transactions", headers={"Authorization": "Bearer wrong-role-token"}
    )
    assert response.status_code == 403


def test_empty_role_set_fails_closed() -> None:
    response = _client().get(
        "/api/v1/business/transactions", headers={"Authorization": "Bearer no-role-token"}
    )
    assert response.status_code == 403


def test_valid_token_reads_transactions() -> None:
    response = _client().get(
        "/api/v1/business/transactions", headers={"Authorization": "Bearer merchant-token"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_valid_token_can_create_policy() -> None:
    response = _client().post(
        "/api/v1/business/policies",
        json=_payload(),
        headers={"Authorization": "Bearer merchant-token"},
    )
    assert response.status_code == 201
    assert response.json()["lock_id"] == "lock-1"


def test_wrong_role_token_cannot_create_policy() -> None:
    response = _client().post(
        "/api/v1/business/policies",
        json=_payload(),
        headers={"Authorization": "Bearer wrong-role-token"},
    )
    assert response.status_code == 403


def test_valid_token_can_delete_policy() -> None:
    client = _client()
    created = client.post(
        "/api/v1/business/policies",
        json=_payload(),
        headers={"Authorization": "Bearer admin-token"},
    )
    assert created.status_code == 201
    deleted = client.delete(
        "/api/v1/business/policies/lock-1",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert deleted.status_code == 204


def test_webhooks_require_auth() -> None:
    response = _client().get("/api/v1/business/webhooks")
    assert response.status_code == 401


def test_parse_token_map() -> None:
    parsed = _parse_token_map("tok1:BUSINESS_ADMIN|MERCHANT_ADMIN, tok2:MERCHANT_ADMIN ,bad,bad:")
    assert parsed == {
        "tok1": frozenset({"BUSINESS_ADMIN", "MERCHANT_ADMIN"}),
        "tok2": frozenset({"MERCHANT_ADMIN"}),
    }


def test_extract_bearer_token_rejects_non_bearer() -> None:
    with pytest.raises(AuthError) as excinfo:
        extract_bearer_token("Basic abc")
    assert excinfo.value.status_code == 401
    with pytest.raises(AuthError):
        extract_bearer_token(None)
    with pytest.raises(AuthError):
        extract_bearer_token("Bearer   ")


def test_require_roles_fail_closed() -> None:
    authenticator = ConfigTokenAuthenticator({"t": frozenset()})
    with pytest.raises(AuthError) as excinfo:
        require_roles("Bearer t", authenticator, {"BUSINESS_ADMIN"})
    assert excinfo.value.status_code == 403
