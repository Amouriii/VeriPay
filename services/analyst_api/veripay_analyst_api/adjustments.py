"""Live, per-transaction score adjustments (architecture section 7).

Two deterministic adjustments are chained before a decision is finalized:

* **Feedback** — if the last ``TRUST_BOOST_WINDOW`` analyst verdicts on this
  customer were all benign (false alarm / customer confirmed legitimate), the
  anomaly score is multiplied by ``TRUST_BOOST_FACTOR`` (0.7) so the system
  stops re-flagging verified-normal behavior. If any recent verdict confirmed
  fraud, ``HEIGHTENED_ALERT_ADD`` (0.1) is added to the fraud probability
  because the account is under active attack.

* **Drift** — a *gradual* lifestyle/relocation drift, when also confirmed by
  benign feedback, multiplies the anomaly score by ``GRADUAL_DRIFT_FACTOR``
  (0.6): it is the new normal. A *sudden* location jump (hundreds of km in
  minutes) multiplies the anomaly score by ``SUDDEN_DRIFT_FACTOR`` (1.2):
  stay more suspicious.

Both chains. Raw and adjusted scores are both returned so an analyst can see
exactly what happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Values copied from the models so callers see the effective tuning constants;
# the live source of truth is ``config.settings``.
TRUST_BOOST_FACTOR = 0.7
HEIGHTENED_ALERT_ADD = 0.1
GRADUAL_DRIFT_FACTOR = 0.6
SUDDEN_DRIFT_FACTOR = 1.2

_BENIGN_LABELS = frozenset(
    {"false_alarm", "false_positive", "customer_confirmed_legitimate", "legitimate"}
)
_CONFIRMED_LABELS = frozenset({"confirmed_fraud", "confirmed_fraud?"})


@dataclass
class FeedbackOutcome:
    anomaly_factor: float = 1.0
    fraud_add: float = 0.0
    effect: str | None = None
    description: str = ""


@dataclass
class DriftOutcome:
    anomaly_factor: float = 1.0
    effect: str | None = None
    description: str = ""


@dataclass
class Adjustment:
    """Combined result of the feedback + drift chain for one transaction."""

    anomaly_factor: float = 1.0
    fraud_add: float = 0.0
    items: list[object] = field(default_factory=list)


def is_benign(label: str) -> bool:
    """True when a normalized analyst verdict says the transaction was genuine."""
    return label.strip().lower() in _BENIGN_LABELS


def is_confirmed_fraud(label: str) -> bool:
    """True when a normalized analyst verdict confirmed fraud."""
    return label.strip().lower() in _CONFIRMED_LABELS


def to_review_label(label: str) -> str:
    """Map an analyst verdict to the shared ReviewLabel-style vocabulary.

    ``feedback_loop`` (ReviewLabel) and ``model_monitor`` (MonitorLabel) use the
    same upper-case values, so a single canonical mapping lets the analyst API
    forward a verdict to both boundaries unchanged.
    """
    normalized = label.strip().lower()
    if normalized in ("confirmed_fraud", "confirmed_fraud?"):
        return "CONFIRMED_FRAUD"
    if normalized in ("false_alarm", "false_positive"):
        return "FALSE_POSITIVE"
    if normalized in ("legitimate", "customer_confirmed_legitimate"):
        return "LEGITIMATE"
    return "NEEDS_REVIEW"


def feedback_adjustment(
    labels: list[str],
    *,
    window: int = 3,
    trust_factor: float = TRUST_BOOST_FACTOR,
    add: float = HEIGHTENED_ALERT_ADD,
) -> FeedbackOutcome:
    """Apply the feedback trust-boost / heightened-alert rules.

    ``labels`` should be that customer's verdicts ordered oldest → newest.
    """
    outcome = FeedbackOutcome()
    any_confirmed = any(is_confirmed_fraud(label) for label in labels)
    if any_confirmed:
        outcome.fraud_add = add
        outcome.effect = "heightened_alert"
        outcome.description = (
            f"Recent analyst feedback confirmed fraud on this customer; "
            f"fraud probability +{add:.2f}."
        )

    recent = labels[-window:] if labels else []
    if len(recent) >= window and all(is_benign(label) for label in recent):
        outcome.anomaly_factor = trust_factor
        outcome.effect = "trust_boost" if outcome.effect is None else outcome.effect
        description = (
            f"Last {window} analyst verdicts for this customer were benign; "
            f"anomaly score ×{trust_factor}."
        )
        if outcome.description:
            outcome.description = f"{outcome.description} {description}"
        else:
            outcome.description = description
    if outcome.effect is None:
        outcome.effect = "no_adjustment"
        outcome.description = "No recent feedback; no adjustment."
    return outcome


def drift_adjustment(
    drift_kind: str | None,
    *,
    confirmed_by_feedback: bool,
    gradual_factor: float = GRADUAL_DRIFT_FACTOR,
    sudden_factor: float = SUDDEN_DRIFT_FACTOR,
) -> DriftOutcome:
    """Apply the drift adjustment to the anomaly score.

    ``drift_kind`` is ``"gradual"`` (lifestyle/relocation change) or
    ``"sudden"`` (impossible location jump). ``None`` means no drift.
    """
    outcome = DriftOutcome()
    if drift_kind == "gradual" and confirmed_by_feedback:
        outcome.anomaly_factor = gradual_factor
        outcome.effect = "gradual_drift"
        outcome.description = (
            f"Customer relocated / changed lifestyle (gradual drift) and it was "
            f"confirmed by feedback; anomaly score ×{gradual_factor}."
        )
    elif drift_kind == "sudden":
        outcome.anomaly_factor = sudden_factor
        outcome.effect = "sudden_drift"
        outcome.description = (
            f"Sudden drift: location jumped hundreds of kilometres in minutes; "
            f"anomaly score ×{sudden_factor}."
        )
    else:
        outcome.effect = "no_adjustment"
        outcome.description = "No drift; no adjustment."
    return outcome


def chain(
    feedback: FeedbackOutcome,
    drift: DriftOutcome,
) -> Adjustment:
    """Combine both adjustments into a single chainable result."""
    return Adjustment(
        anomaly_factor=feedback.anomaly_factor * drift.anomaly_factor,
        fraud_add=feedback.fraud_add,
        items=[feedback, drift],
    )


__all__ = [
    "Adjustment",
    "DriftOutcome",
    "FeedbackOutcome",
    "GRADUAL_DRIFT_FACTOR",
    "HEIGHTENED_ALERT_ADD",
    "SUDDEN_DRIFT_FACTOR",
    "TRUST_BOOST_FACTOR",
    "chain",
    "drift_adjustment",
    "feedback_adjustment",
    "is_benign",
    "is_confirmed_fraud",
    "to_review_label",
]
