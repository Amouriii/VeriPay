from fastapi.testclient import TestClient
from veripay_rule_engine.main import create_app
from veripay_rule_engine.service import RuleCode, RuleEvaluationRequest, evaluate_rules


def test_dcvv_and_velocity_rules_trigger() -> None:
    result = evaluate_rules(
        RuleEvaluationRequest(dcvv_match=False, velocity_count_5m=6, velocity_limit_5m=5)
    )
    assert result.triggered is True
    assert {finding.code for finding in result.findings if finding.triggered} == {
        RuleCode.DCVV_MISMATCH,
        RuleCode.BURNER_VELOCITY,
    }


def test_rule_endpoint_returns_non_triggered_findings() -> None:
    client = TestClient(create_app())
    response = client.post("/api/v1/rules/evaluate", json={})
    assert response.status_code == 200
    assert response.json()["triggered"] is False
    assert len(response.json()["findings"]) == 5
