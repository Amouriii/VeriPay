"""Deterministic policy rules used by the fraud pipeline."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RuleCode(StrEnum):
    DCVV_MISMATCH = "DCVV_MISMATCH"
    MERCHANT_LOCK = "MERCHANT_LOCK"
    BURNER_VELOCITY = "BURNER_VELOCITY"
    IMPOSSIBLE_TRAVEL = "IMPOSSIBLE_TRAVEL"
    SIGNAL_CONTRADICTION = "SIGNAL_CONTRADICTION"


class RuleEvaluationRequest(BaseModel):
    dcvv_match: bool | None = None
    merchant_allowed: bool | None = None
    velocity_count_5m: int = Field(default=0, ge=0)
    velocity_limit_5m: int = Field(default=5, ge=1)
    impossible_travel: bool = False
    device_trusted: bool | None = None
    network_trusted: bool | None = None


class RuleFinding(BaseModel):
    code: RuleCode
    triggered: bool
    severity: int = Field(ge=0, le=100)
    reason: str


class RuleEvaluationResponse(BaseModel):
    triggered: bool
    findings: list[RuleFinding]


def evaluate_rules(request: RuleEvaluationRequest) -> RuleEvaluationResponse:
    """Evaluate hard rules without calling ML or external systems."""
    findings = [
        RuleFinding(
            code=RuleCode.DCVV_MISMATCH,
            triggered=request.dcvv_match is False,
            severity=100 if request.dcvv_match is False else 0,
            reason="Dynamic CVV did not match" if request.dcvv_match is False else "Not triggered",
        ),
        RuleFinding(
            code=RuleCode.MERCHANT_LOCK,
            triggered=request.merchant_allowed is False,
            severity=90 if request.merchant_allowed is False else 0,
            reason=(
                "Merchant policy rejected transaction"
                if request.merchant_allowed is False
                else "Not triggered"
            ),
        ),
        RuleFinding(
            code=RuleCode.BURNER_VELOCITY,
            triggered=request.velocity_count_5m > request.velocity_limit_5m,
            severity=80 if request.velocity_count_5m > request.velocity_limit_5m else 0,
            reason="Five-minute velocity limit exceeded"
            if request.velocity_count_5m > request.velocity_limit_5m
            else "Not triggered",
        ),
        RuleFinding(
            code=RuleCode.IMPOSSIBLE_TRAVEL,
            triggered=request.impossible_travel,
            severity=85 if request.impossible_travel else 0,
            reason="Transaction location implies impossible travel"
            if request.impossible_travel
            else "Not triggered",
        ),
        RuleFinding(
            code=RuleCode.SIGNAL_CONTRADICTION,
            triggered=request.device_trusted is False and request.network_trusted is True,
            severity=(
                60 if request.device_trusted is False and request.network_trusted is True else 0
            ),
            reason="Device and network trust signals contradict"
            if request.device_trusted is False and request.network_trusted is True
            else "Not triggered",
        ),
    ]
    return RuleEvaluationResponse(
        triggered=any(finding.triggered for finding in findings),
        findings=findings,
    )
