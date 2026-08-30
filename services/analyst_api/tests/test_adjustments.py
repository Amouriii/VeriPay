from veripay_analyst_api import adjustments


def test_no_feedback_no_adjustment() -> None:
    outcome = adjustments.feedback_adjustment([])
    assert outcome.anomaly_factor == 1.0
    assert outcome.fraud_add == 0.0
    assert outcome.effect == "no_adjustment"


def test_trust_boost_when_last_three_benign() -> None:
    outcome = adjustments.feedback_adjustment(
        ["false_alarm", "false_alarm", "customer_confirmed_legitimate"]
    )
    assert outcome.anomaly_factor == 0.7
    assert outcome.fraud_add == 0.0
    assert outcome.effect == "trust_boost"


def test_trust_boost_requires_three_in_window() -> None:
    outcome = adjustments.feedback_adjustment(["false_alarm", "false_alarm"])
    assert outcome.anomaly_factor == 1.0


def test_heightened_alert_on_confirmed_fraud() -> None:
    outcome = adjustments.feedback_adjustment([])
    outcome = adjustments.feedback_adjustment(["confirmed_fraud"])
    assert outcome.fraud_add == 0.1
    assert outcome.effect == "heightened_alert"


def test_confirmed_fraud_beats_trust_boost_factor() -> None:
    # A single recent confirmed-fraud verdict must not trigger the trust boost
    # even if the tail is benign.
    outcome = adjustments.feedback_adjustment(["confirmed_fraud", "false_alarm", "false_alarm"])
    assert outcome.fraud_add == 0.1
    assert outcome.anomaly_factor == 1.0


def test_gradual_drift_confirmed_lowers_anomaly() -> None:
    outcome = adjustments.drift_adjustment("gradual", confirmed_by_feedback=True)
    assert outcome.anomaly_factor == 0.6
    assert outcome.effect == "gradual_drift"


def test_gradual_drift_without_feedback_is_noop() -> None:
    outcome = adjustments.drift_adjustment("gradual", confirmed_by_feedback=False)
    assert outcome.anomaly_factor == 1.0
    assert outcome.effect == "no_adjustment"


def test_sudden_drift_raises_anomaly() -> None:
    outcome = adjustments.drift_adjustment("sudden", confirmed_by_feedback=False)
    assert outcome.anomaly_factor == 1.2
    assert outcome.effect == "sudden_drift"


def test_chain_multiplies_factors_and_sums_add() -> None:
    combined = adjustments.chain(
        adjustments.feedback_adjustment(["confirmed_fraud"]),
        adjustments.drift_adjustment("sudden", confirmed_by_feedback=False),
    )
    assert combined.anomaly_factor == 1.2
    assert combined.fraud_add == 0.1
    assert len(combined.items) == 2
