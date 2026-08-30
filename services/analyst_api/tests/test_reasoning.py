from veripay_analyst_api.models import Decision, RiskLevel
from veripay_analyst_api.reasoning import crosscheck_numbers, map_decision, map_risk_level
from veripay_common.enums import DecisionAction, RiskTier


def test_decision_mapping() -> None:
    assert map_decision(DecisionAction.ALLOW, RiskTier.NO_RISK) == Decision.PASS
    assert map_decision(DecisionAction.CHALLENGE, RiskTier.MODERATE) == Decision.REVIEW_UNUSUAL
    assert map_decision(DecisionAction.MONITOR, RiskTier.LOW) == Decision.REVIEW_UNUSUAL
    assert map_decision(DecisionAction.REVIEW, RiskTier.HIGH) == Decision.REVIEW_STEALTH
    assert map_decision(DecisionAction.DECLINE, RiskTier.HIGH) == Decision.BLOCK


def test_risk_level_mapping() -> None:
    assert map_risk_level(RiskTier.HIGH) == RiskLevel.HIGH
    assert map_risk_level(RiskTier.MODERATE) == RiskLevel.MODERATE
    assert map_risk_level(RiskTier.LOW) == RiskLevel.LOW


def test_crosscheck_allows_cited_numbers() -> None:
    payload = {"fraud_probability": 0.52, "risk_score": 47}
    crosschecked, flagged = crosscheck_numbers("Risk score 47; fraud probability 0.52.", payload)
    assert crosschecked is True
    assert flagged is False


def test_crosscheck_flags_hallucinated_number() -> None:
    payload = {"fraud_probability": 0.52, "risk_score": 47}
    crosschecked, flagged = crosscheck_numbers("Fraud probability 0.91.", payload)
    assert crosschecked is True
    assert flagged is True


def test_crosscheck_ignores_incidental_whole_numbers() -> None:
    payload = {"risk_score": 47}
    crosschecked, flagged = crosscheck_numbers("120 transactions.", payload)
    assert crosschecked is True
    # 120 is an incidental whole-number count below the floor: ignored.
    assert flagged is False


def test_crosscheck_flags_large_unmatched_number() -> None:
    payload = {"risk_score": 47}
    crosschecked, flagged = crosscheck_numbers("Estimated loss 5000.", payload)
    assert crosschecked is True
    assert flagged is True  # 5000 is above the floor and absent from the payload


def test_crosscheck_not_applicable_without_payload_numbers() -> None:
    crosschecked, flagged = crosscheck_numbers("Risk score high.", {"verdict": "high"})
    assert crosschecked is False
    assert flagged is False
