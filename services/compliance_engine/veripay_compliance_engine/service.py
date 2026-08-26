"""Compliance controls for PCI, PSD3/SCA, and network trust. Expansion §1 Dev4, §2."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field
from veripay_common.enums import ComplianceStandard, DeviceTrustState, ScaExemption


class ComplianceOutcome(StrEnum):
    PASS = "PASS"
    CHALLENGE = "CHALLENGE"
    REJECT = "REJECT"
    UNAVAILABLE = "UNAVAILABLE"


class ComplianceRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    tokenized: bool = True
    sca_exemption: ScaExemption = ScaExemption.NONE
    authenticated: bool = False
    network_trusted: bool | None = True
    device_trust_state: DeviceTrustState = DeviceTrustState.UNKNOWN
    device_signal_required: bool = False
    low_value_threshold_minor: int = Field(default=3_000, ge=0)
    fail_closed_on_unavailable: bool = True


class ComplianceFinding(BaseModel):
    standard: ComplianceStandard
    outcome: ComplianceOutcome
    triggered: bool
    reason_code: str
    reason: str


class ComplianceResponse(BaseModel):
    transaction_id: str
    outcome: ComplianceOutcome
    blocking: bool
    findings: list[ComplianceFinding]


def evaluate_compliance(request: ComplianceRequest) -> ComplianceResponse:
    findings: list[ComplianceFinding] = []
    findings.append(
        ComplianceFinding(
            standard=ComplianceStandard.PCI_DSS_4_0,
            outcome=ComplianceOutcome.PASS if request.tokenized else ComplianceOutcome.REJECT,
            triggered=not request.tokenized,
            reason_code="TOKENIZATION_REQUIRED" if not request.tokenized else "TOKENIZED_INPUT",
            reason=(
                "Payment references must be tokenized before entering this service"
                if not request.tokenized
                else "Payment data is represented by a token reference"
            ),
        )
    )

    sca_required = request.amount_minor > request.low_value_threshold_minor
    sca_exempt = request.sca_exemption != ScaExemption.NONE
    if request.authenticated or (
        sca_exempt and request.amount_minor <= request.low_value_threshold_minor * 3
    ):
        sca_outcome = ComplianceOutcome.PASS
        sca_reason = "Strong customer authentication or an eligible exemption is present"
        sca_code = "SCA_SATISFIED"
        sca_triggered = False
    elif sca_required:
        sca_outcome = ComplianceOutcome.CHALLENGE
        sca_reason = "Strong customer authentication is required"
        sca_code = "SCA_REQUIRED"
        sca_triggered = True
    else:
        sca_outcome = ComplianceOutcome.PASS
        sca_reason = "Transaction is below the low-value SCA threshold"
        sca_code = "SCA_LOW_VALUE"
        sca_triggered = False
    findings.append(
        ComplianceFinding(
            standard=ComplianceStandard.PSD3_SCA,
            outcome=sca_outcome,
            triggered=sca_triggered,
            reason_code=sca_code,
            reason=sca_reason,
        )
    )

    if request.network_trusted is False:
        network_outcome = ComplianceOutcome.REJECT
        network_code = "NETWORK_UNTRUSTED"
        network_reason = "Network trust verification failed"
        network_triggered = True
    elif request.network_trusted is None:
        network_outcome = ComplianceOutcome.UNAVAILABLE
        network_code = "NETWORK_TRUST_UNAVAILABLE"
        network_reason = "Network trust evidence is unavailable"
        network_triggered = True
    else:
        network_outcome = ComplianceOutcome.PASS
        network_code = "NETWORK_TRUSTED"
        network_reason = "Network trust verification passed"
        network_triggered = False
    findings.append(
        ComplianceFinding(
            standard=ComplianceStandard.NETWORK_ZERO_TRUST,
            outcome=network_outcome,
            triggered=network_triggered,
            reason_code=network_code,
            reason=network_reason,
        )
    )

    if request.device_signal_required and request.device_trust_state == DeviceTrustState.UNTRUSTED:
        findings.append(
            ComplianceFinding(
                standard=ComplianceStandard.NETWORK_ZERO_TRUST,
                outcome=ComplianceOutcome.CHALLENGE,
                triggered=True,
                reason_code="DEVICE_TRUST_REQUIRED",
                reason="A trusted device is required for this transaction",
            )
        )
    elif request.device_signal_required and request.device_trust_state == DeviceTrustState.UNKNOWN:
        findings.append(
            ComplianceFinding(
                standard=ComplianceStandard.NETWORK_ZERO_TRUST,
                outcome=ComplianceOutcome.UNAVAILABLE,
                triggered=True,
                reason_code="DEVICE_TRUST_UNAVAILABLE",
                reason="Device trust evidence is unavailable",
            )
        )

    outcomes = [finding.outcome for finding in findings]
    if ComplianceOutcome.REJECT in outcomes:
        overall = ComplianceOutcome.REJECT
        blocking = True
    elif ComplianceOutcome.UNAVAILABLE in outcomes:
        overall = ComplianceOutcome.UNAVAILABLE
        blocking = request.fail_closed_on_unavailable
    elif ComplianceOutcome.CHALLENGE in outcomes:
        overall = ComplianceOutcome.CHALLENGE
        blocking = True
    else:
        overall = ComplianceOutcome.PASS
        blocking = False
    return ComplianceResponse(
        transaction_id=request.transaction_id,
        outcome=overall,
        blocking=blocking,
        findings=findings,
    )
