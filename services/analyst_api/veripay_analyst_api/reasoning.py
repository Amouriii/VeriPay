"""Response-engine mapping and evidence validation (architecture section 9).

The deterministic risk-level / verification-action mapping converts the
decision engine's cost-minimized action and tier into the analyst vocabulary
(BLOCK / REVIEW_STEALTH / REVIEW_UNUSUAL / PASS with HIGH/MODERATE/LOW risk and
a human-readable verification action).

The case-report evidence crosscheck is the anti-hallucination step: every
number the explanation mentions must exist in the original scoring payload,
mirroring the architecture's "parse and validate" node.
"""

from __future__ import annotations

import re
from typing import Any

from veripay_common.enums import DecisionAction, RiskTier

from veripay_analyst_api.models import Decision, RiskLevel

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def map_decision(action: DecisionAction, tier: RiskTier) -> Decision:
    """Map the cost-aware engine action to the analyst decision vocabulary."""
    if action == DecisionAction.ALLOW:
        return Decision.PASS
    if action in (DecisionAction.MONITOR, DecisionAction.CHALLENGE):
        # Low/moderate friction and a soft check → unusual-but-not-certainly-fraud.
        return Decision.REVIEW_UNUSUAL
    if action == DecisionAction.REVIEW:
        return Decision.REVIEW_STEALTH
    if action in (DecisionAction.DECLINE, DecisionAction.REVERSE):
        return Decision.BLOCK
    return Decision.PASS


def map_risk_level(tier: RiskTier) -> RiskLevel:
    if tier == RiskTier.HIGH:
        return RiskLevel.HIGH
    if tier == RiskTier.MODERATE:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def verification_action_text(decision: Decision, tier: RiskTier) -> str:
    """Deterministic, no-LLM verification action for the given decision."""
    if decision == Decision.PASS:
        return "No action."
    if decision == Decision.REVIEW_UNUSUAL:
        if tier == RiskTier.MODERATE:
            return (
                "Hold payment for 5 minutes; push notification 'Was this you?'; "
                "release if confirmed; escalate if no response."
            )
        return "Soft check: confirm amount/date/vendor, then release."
    if decision == Decision.REVIEW_STEALTH:
        return "Hold payment; require biometric; notify analyst."
    # BLOCK
    return "Hold payment; require biometric (fingerprint/face); notify analyst immediately."


def extract_numbers(text: str) -> list[str]:
    """Return every numeric token found in ``text``, in order."""
    return _NUMBER_RE.findall(text or "")


def allowed_number_strings(payload: dict[str, Any]) -> set[str]:
    """Canonical numeric strings a trustworthy explanation may cite."""
    allowed: set[str] = set()
    for value in payload.values():
        if isinstance(value, bool):
            continue
        numbers = _NUMBER_RE.findall(str(value))
        for number in numbers:
            allowed.add(number)
    return allowed


def crosscheck_numbers(
    text: str,
    payload: dict[str, Any],
    *,
    whole_number_floor: int = 200,
) -> tuple[bool, bool]:
    """Return ``(crosschecked, hallucination_flagged)`` for generated text.

    ``crosschecked`` is False when the payload carries no numbers to compare
    against. A numeric token is checked unless it is an incidental whole-number
    count below ``whole_number_floor`` (e.g. "120 transactions"). Probabilities
    and other fractional values are always checked, since a fabricated figure
    like 0.91 vs a true 0.52 is exactly the hallucination this step exists to
    catch.
    """
    allowed = allowed_number_strings(payload)
    if not allowed:
        return False, False
    false_found: list[str] = []
    for token in extract_numbers(text):
        try:
            scale = abs(float(token))
        except ValueError:
            continue
        has_fraction = "." in token
        if not has_fraction and scale < whole_number_floor:
            continue  # ignore incidental whole-number counts
        if not _matches_allowed(token, allowed):
            false_found.append(token)
    return True, bool(false_found)


def _matches_allowed(token: str, allowed: set[str]) -> bool:
    if token in allowed:
        return True
    try:
        value = float(token)
    except ValueError:
        return False
    for candidate in allowed:
        try:
            # Relative tolerance only; a 5% deviation is a rounding-level match.
            if abs(float(candidate) - value) <= abs(value) * 0.05:
                return True
        except ValueError:
            continue
    return False


__all__ = [
    "allowed_number_strings",
    "crosscheck_numbers",
    "extract_numbers",
    "map_decision",
    "map_risk_level",
    "verification_action_text",
]
