"""Auth enforcement tests for the FI Ops portal boundary (Expansion §1 item 6)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from veripay_fi_ops_portal.auth import (
    AuthError,
    ConfigTokenAuthenticator,
    _parse_token_map,
    extract_bearer_token,
    require_roles,
)
from veripay_fi_ops_portal.main import create_app


def _payload(cc_num: int = 1, txid: str = "tx_1") -> dict[str, Any]:
    return {
        "transaction": {
            "transaction_id": txid,
            "cc_num": cc_num,
            "amount": 100.0,
            "merchant": "m_amazon",
            "category": "ecommerce",
            "timestamp": "2026-08-10T10:00:00Z",
        }
    }


def _client() -> TestClient:
    authenticator = ConfigTokenAuthenticator(
        {
            "ops-token": frozenset({"FI_OPS", "ADMIN"}),
            "readonly-token": frozenset({"FI_OPS"}),
            "wrong-role-token": frozenset({"BUSINESS_ADMIN"}),
            "no-role-token": frozenset(),
        }
    )
    return TestClient(create_app(authenticator=authenticator))


def test_health_is_unauthenticated() -> None:
    assert _client().get("/health").status_code == 200


def test_access_policy_is_unauthenticated() -> None:
    response = _client().get("/api/v1/fi-ops/access-policy")
    assert response.status_code == 200
    assert response.json()["required_roles"] == ["FI_OPS", "ADMIN"]


def test_missing_token_is_unauthorized() -> None:
    response = _client().get("/api/v1/fi-ops/transactions")
    assert response.status_code == 401


def test_non_bearer_scheme_is_unauthorized() -> None:
    response = _client().get("/api/v1/fi-ops/transactions", headers={"Authorization": "Basic abc"})
    assert response.status_code == 401


def test_unknown_token_is_unauthorized() -> None:
    response = _client().get(
        "/api/v1/fi-ops/transactions", headers={"Authorization": "Bearer nope"}
    )
    assert response.status_code == 401


def test_token_without_required_role_is_forbidden() -> None:
    response = _client().get(
        "/api/v1/fi-ops/transactions", headers={"Authorization": "Bearer wrong-role-token"}
    )
    assert response.status_code == 403


def test_empty_role_set_fails_closed() -> None:
    response = _client().get(
        "/api/v1/fi-ops/transactions", headers={"Authorization": "Bearer no-role-token"}
    )
    assert response.status_code == 403


def test_valid_token_reads_transactions() -> None:
    response = _client().get(
        "/api/v1/fi-ops/transactions", headers={"Authorization": "Bearer readonly-token"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_admin_token_can_transition_disputes() -> None:
    client = _client()
    # Seed a dispute through the in-memory repository (no create endpoint —
    # production delegates dispute creation to the dispute engine service).
    from datetime import UTC, datetime

    from veripay_common.enums import DisputeReason, DisputeStatus
    from veripay_fi_ops_portal.service import InMemoryFiOpsRepository, OpsDisputeView

    repository = InMemoryFiOpsRepository()
    repository.save_dispute(
        OpsDisputeView(
            dispute_id="d-1",
            transaction_id="tx-1",
            amount_minor=1000,
            currency="USD",
            status=DisputeStatus.OPENED,
            reason=DisputeReason.FRAUD,
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    app = create_app(
        repository=repository,
        authenticator=ConfigTokenAuthenticator(
            {
                "ops-token": frozenset({"FI_OPS", "ADMIN"}),
                "readonly-token": frozenset({"FI_OPS"}),
                "wrong-role-token": frozenset({"BUSINESS_ADMIN"}),
                "no-role-token": frozenset(),
            }
        ),
    )
    client = TestClient(app)
    transitioned = client.post(
        "/api/v1/fi-ops/disputes/d-1/transition",
        json={"status": "ACCEPTED", "actor": "ops"},
        headers={"Authorization": "Bearer ops-token"},
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "ACCEPTED"


def test_forbidden_token_cannot_transition_disputes() -> None:
    response = _client().post(
        "/api/v1/fi-ops/disputes/d-1/transition",
        json={"status": "ACCEPTED", "actor": "ops"},
        headers={"Authorization": "Bearer wrong-role-token"},
    )
    assert response.status_code == 403


def test_regulatory_report_requires_auth() -> None:
    response = _client().get("/api/v1/fi-ops/reports/regulatory")
    assert response.status_code == 401


def test_parse_token_map() -> None:
    parsed = _parse_token_map("tok1:FI_OPS|ADMIN, tok2:FI_OPS ,bad,bad:")
    assert parsed == {
        "tok1": frozenset({"FI_OPS", "ADMIN"}),
        "tok2": frozenset({"FI_OPS"}),
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
        require_roles("Bearer t", authenticator, {"FI_OPS"})
    assert excinfo.value.status_code == 403
