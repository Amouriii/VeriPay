from fastapi.testclient import TestClient
from veripay_common.enums import DecisionAction, RiskBand
from veripay_decision_engine.main import create_app
from veripay_decision_engine.service import DecisionReason, DecisionRequest, decide


def test_low_approve_score_allows() -> None:
    result = decide(
        DecisionRequest(transaction_id="tx-low", risk_score=10, risk_band=RiskBand.APPROVE)
    )
    assert result.action == DecisionAction.ALLOW
    assert result.reason_code == DecisionReason.COST_MINIMIZED


def test_verify_score_challenges_with_default_costs() -> None:
    result = decide(
        DecisionRequest(transaction_id="tx-verify", risk_score=55, risk_band=RiskBand.VERIFY)
    )
    assert result.action == DecisionAction.CHALLENGE
    assert len(result.candidates) == 3


def test_hard_controls_override_cost_model() -> None:
    reversal = decide(
        DecisionRequest(
            transaction_id="tx-reversal",
            risk_score=1,
            risk_band=RiskBand.APPROVE,
            is_reversal=True,
        )
    )
    blocked = decide(
        DecisionRequest(
            transaction_id="tx-compliance",
            risk_score=1,
            risk_band=RiskBand.APPROVE,
            compliance_blocked=True,
        )
    )
    assert reversal.action == DecisionAction.REVERSE
    assert blocked.action == DecisionAction.DECLINE


def test_missing_evidence_is_sent_to_review() -> None:
    result = decide(
        DecisionRequest(
            transaction_id="tx-missing",
            risk_score=5,
            risk_band=RiskBand.APPROVE,
            evidence_available=False,
        )
    )
    assert result.action == DecisionAction.REVIEW
    assert result.reason_code == DecisionReason.EVIDENCE_UNAVAILABLE


def test_decision_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/decision/evaluate",
        json={"transaction_id": "tx-api", "risk_score": 90, "risk_band": "BLOCK"},
    )
    assert response.status_code == 200
    assert response.json()["action"] == "DECLINE"
