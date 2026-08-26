from fastapi.testclient import TestClient
from veripay_merchant_policy.main import create_app
from veripay_merchant_policy.service import (
    InMemoryMerchantPolicyRepository,
    MerchantLockRule,
    PolicyEvaluationRequest,
    evaluate_policy,
)


def test_limits_and_mcc_restrictions_block() -> None:
    repository = InMemoryMerchantPolicyRepository()
    repository.save(
        MerchantLockRule(
            lock_id="lock-1",
            merchant_id="merchant-1",
            allowed_mccs="5411",
            max_spend_per_txn_minor=1_000,
            daily_spend_limit_minor=2_000,
            velocity_limit_5m=2,
        )
    )
    result = evaluate_policy(
        PolicyEvaluationRequest(
            transaction_id="tx-1",
            merchant_id="merchant-1",
            mcc="5999",
            amount_minor=1_500,
            daily_spend_minor=1_000,
            velocity_count_5m=3,
        ),
        repository,
    )
    assert result.allowed is False
    assert {finding.code for finding in result.findings if finding.triggered} == {
        "MCC_RESTRICTED",
        "TRANSACTION_LIMIT",
        "DAILY_LIMIT",
        "VELOCITY_LIMIT",
    }


def test_missing_policy_allows_by_default() -> None:
    result = evaluate_policy(
        PolicyEvaluationRequest(
            transaction_id="tx-2", merchant_id="unknown", mcc="5411", amount_minor=10
        ),
        InMemoryMerchantPolicyRepository(),
    )
    assert result.allowed is True
    assert result.findings[0].code == "NO_POLICY"


def test_merchant_rule_api() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/merchant/rules",
        json={"lock_id": "lock-api", "merchant_id": "merchant-api", "max_spend_per_txn_minor": 100},
    )
    assert response.status_code == 201
    evaluation = client.post(
        "/api/v1/merchant/rules/evaluate",
        json={
            "transaction_id": "tx-api",
            "merchant_id": "merchant-api",
            "mcc": "5411",
            "amount_minor": 101,
        },
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["allowed"] is False
