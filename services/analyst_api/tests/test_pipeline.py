from datetime import UTC, datetime, timedelta

from veripay_analyst_api.clients import PipelineClient
from veripay_analyst_api.config import Settings, settings
from veripay_analyst_api.features16 import FEATURES16
from veripay_analyst_api.models import (
    Decision,
    FeedbackInput,
    GeoPoint,
    RiskLevel,
    ScoreRequest,
    TransactionInput,
)
from veripay_analyst_api.profiles import ProfileStore, StoredFeedback, StoredTransaction
from veripay_analyst_api.service import AnalystOrchestrator

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _input(cc_num: int = 7, amount: float = 100.0, **overrides: object) -> TransactionInput:
    fields: dict[str, object] = {
        "transaction_id": f"tx_{cc_num}",
        "cc_num": cc_num,
        "amount": amount,
        "merchant": "m_amazon",
        "category": "ecommerce",
        "timestamp": _BASE,
    }
    fields.update(overrides)
    return TransactionInput(**fields)


def _orch(client: PipelineClient, store: ProfileStore | None = None) -> AnalystOrchestrator:
    return AnalystOrchestrator(client=client, store=store or ProfileStore(), settings=settings)


def test_score_passes_low_risk(fake_client: PipelineClient) -> None:
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input(cc_num=1)))
    assert resp.decision == Decision.PASS
    assert resp.risk_level == RiskLevel.LOW
    assert resp.verification_action.startswith("No action")
    assert resp.transaction_id == "tx_1"
    assert fake_client.supervised_calls == 1  # type: ignore[attr-defined]
    assert fake_client.anomaly_calls == 1  # type: ignore[attr-defined]


def test_trust_boost_lowers_anomaly(fake_client: PipelineClient) -> None:
    fake_client.anomaly = 0.9  # type: ignore[attr-defined]
    store = ProfileStore()
    for _ in range(3):
        store.record_feedback(
            StoredFeedback(
                transaction_id="past",
                cc_num=7,
                analyst_decision="false_alarm",
                decision=Decision.REVIEW_UNUSUAL,
                notes="",
                timestamp=_BASE,
            )
        )
    resp = _orch(fake_client, store).score(ScoreRequest(transaction=_input(cc_num=7)))
    assert resp.raw_anomaly_score == 0.9
    assert resp.anomaly_score == round(0.9 * 0.7, 4)
    assert any(a.kind == "feedback" and a.effect == "trust_boost" for a in resp.adjustments)


def test_heightened_alert_raises_fraud(fake_client: PipelineClient) -> None:
    fake_client.fraud = 0.5  # type: ignore[attr-defined]
    store = ProfileStore()
    store.record_feedback(
        StoredFeedback(
            transaction_id="past",
            cc_num=7,
            analyst_decision="confirmed_fraud",
            decision=Decision.BLOCK,
            notes="",
            timestamp=_BASE,
        )
    )
    resp = _orch(fake_client, store).score(ScoreRequest(transaction=_input(cc_num=7)))
    assert resp.fraud_probability == round(0.5 + 0.1, 4)
    assert any(a.kind == "feedback" and a.effect == "heightened_alert" for a in resp.adjustments)


def test_block_mapping_when_decline(fake_client: PipelineClient) -> None:
    fake_client.action = "DECLINE"  # type: ignore[attr-defined]
    fake_client.anomaly = 0.95  # type: ignore[attr-defined]
    fake_client.fraud = 0.95  # type: ignore[attr-defined]
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input(cc_num=2, amount=5000.0)))
    assert resp.decision == Decision.BLOCK
    assert resp.risk_level == RiskLevel.HIGH


def test_stealth_quadrant_yields_review_stealth(fake_client: PipelineClient) -> None:
    """Engine would BLOCK, but high fraud prob + low anomaly is the stealth
    quadrant (architecture §6): matches known fraud while looking normal →
    REVIEW_STEALTH instead of an automatic freeze."""
    fake_client.action = "DECLINE"  # type: ignore[attr-defined]
    fake_client.fraud = 0.9  # type: ignore[attr-defined]
    fake_client.anomaly = 0.4  # type: ignore[attr-defined]
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input(cc_num=17, amount=900.0)))
    assert resp.decision == Decision.REVIEW_STEALTH
    assert resp.risk_level == RiskLevel.HIGH
    assert "biometric" in resp.verification_action.lower()


def test_both_high_stays_block(fake_client: PipelineClient) -> None:
    """Both axes high → BLOCK; the quadrant refinement must not downgrade it."""
    fake_client.action = "DECLINE"  # type: ignore[attr-defined]
    fake_client.fraud = 0.9  # type: ignore[attr-defined]
    fake_client.anomaly = 0.95  # type: ignore[attr-defined]
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input(cc_num=18, amount=900.0)))
    assert resp.decision == Decision.BLOCK


def test_feedback_and_stats(fake_client: PipelineClient) -> None:
    orch = _orch(fake_client)
    orch.submit_feedback(
        FeedbackInput(
            transaction_id="tx_9",
            cc_num=9,
            analyst_decision="confirmed_fraud",
            decision=Decision.BLOCK,
        )
    )
    stats = orch.feedback_stats()
    assert stats.total_feedback == 1
    assert stats.confirmed_fraud == 1
    assert any(
        row.decision == Decision.BLOCK and row.confirmed_fraud == 1
        for row in stats.feedback_by_decision
    )


def test_feedback_forwards_label_to_boundaries(fake_client: PipelineClient) -> None:
    orch = _orch(fake_client)
    result = orch.submit_feedback(
        FeedbackInput(
            transaction_id="tx_11",
            cc_num=11,
            analyst_decision="confirmed_fraud",
            decision=Decision.BLOCK,
        )
    )
    assert result.recorded is True
    assert result.note == "feedback_loop:ok; model_monitor:ok"
    assert fake_client.feedback_appends == 1  # type: ignore[attr-defined]
    assert fake_client.monitor_labels == ["CONFIRMED_FRAUD"]  # type: ignore[attr-defined]


def test_feedback_forward_failure_is_not_fatal(fake_client: PipelineClient) -> None:
    def boom(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise RuntimeError("feedback_loop down")

    fake_client.append_feedback = boom  # type: ignore[attr-defined,method-assign]
    orch = _orch(fake_client)
    result = orch.submit_feedback(
        FeedbackInput(
            transaction_id="tx_12",
            cc_num=12,
            analyst_decision="false_alarm",
            decision=Decision.REVIEW_UNUSUAL,
        )
    )
    assert result.recorded is True
    assert result.note == "feedback_loop:unavailable; model_monitor:ok"


def test_profile_reports_baseline(fake_client: PipelineClient) -> None:
    store = ProfileStore()
    for i in range(5):
        store.add_transaction(
            StoredTransaction(
                transaction_id=f"t{i}",
                cc_num=5,
                amount=10.0 + i,
                merchant="m_" + str(i),
                category="retail",
                timestamp=_BASE - timedelta(days=i),
                location=GeoPoint(lat=40.0, lon=-74.0),
                merchant_location=GeoPoint(lat=40.0, lon=-74.1),
                decision=Decision.PASS,
            )
        )
    profile = _orch(fake_client, store).profile(5)
    assert profile.cc_num == 5
    assert profile.long_term_baseline.distinct_merchants == 5
    assert profile.drift_detected is None or profile.drift_detected.kind in ("gradual", "sudden")


def test_sudden_drift_detected(fake_client: PipelineClient) -> None:
    store = ProfileStore()
    base = _BASE - timedelta(days=7)
    # Six prior local transactions (a settled baseline).
    for i in range(6):
        store.add_transaction(
            StoredTransaction(
                transaction_id=f"d{i}",
                cc_num=3,
                amount=30.0,
                merchant="m_home",
                category="retail",
                timestamp=base + timedelta(days=i),
                location=GeoPoint(lat=40.0, lon=-74.0),
                merchant_location=GeoPoint(lat=40.0, lon=-74.1),
                decision=Decision.PASS,
            )
        )
    # Then a London transaction seconds later → impossible travel / sudden drift.
    store.add_transaction(
        StoredTransaction(
            transaction_id="near1",
            cc_num=3,
            amount=50.0,
            merchant="m_home",
            category="ecommerce",
            timestamp=_BASE - timedelta(minutes=4),
            location=GeoPoint(lat=40.0, lon=-74.0),
            merchant_location=GeoPoint(lat=40.7, lon=-74.0),
            decision=Decision.PASS,
        )
    )
    store.add_transaction(
        StoredTransaction(
            transaction_id="far2",
            cc_num=3,
            amount=50.0,
            merchant="m_far",
            category="ecommerce",
            timestamp=_BASE,
            location=GeoPoint(lat=51.5, lon=-0.1),
            merchant_location=GeoPoint(lat=51.5, lon=-0.1),
            decision=Decision.PASS,
        )
    )
    drift = store.detect_drift(3)
    assert drift is not None
    assert drift.kind == "sudden"


def test_rich_feature_mode_emits_sixteen_rows(fake_client: PipelineClient) -> None:
    configured = Settings()
    configured.FEATURE_MODE = "rich"
    orch = AnalystOrchestrator(client=fake_client, store=ProfileStore(), settings=configured)
    resp = orch.score(ScoreRequest(transaction=_input(cc_num=13)))
    names = {row.name for row in resp.features}
    assert names == set(FEATURES16)
    assert len(names) == 16
    assert resp.feature_mode == "rich"
    assert len(resp.features16) == 16


def test_basic_mode_reports_basic_and_no_features16(fake_client: PipelineClient) -> None:
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input(cc_num=14)))
    assert resp.feature_mode == "basic"
    assert resp.features16 == []


def test_rescore_is_idempotent(fake_client: PipelineClient) -> None:
    """Re-scoring the same transaction (as /explain does) must not duplicate
    the alert or the customer-history row used for baselines."""
    fake_client.anomaly = 0.9  # type: ignore[attr-defined]
    fake_client.fraud = 0.9  # type: ignore[attr-defined]
    fake_client.action = "DECLINE"  # type: ignore[attr-defined]
    orch = _orch(fake_client)
    tx = _input(cc_num=15, amount=900.0)

    first = orch.score(ScoreRequest(transaction=tx))
    second = orch.score(ScoreRequest(transaction=tx))

    assert first.decision == second.decision == Decision.BLOCK
    alerts = orch.alerts()
    assert len(alerts) == 1
    assert alerts[0].transaction_id == tx.transaction_id
    assert len(orch.store.history(15)) == 1
    assert len(orch.lookup_score(transaction_id=tx.transaction_id).transaction_id) == len(
        tx.transaction_id
    )


def test_explain_does_not_duplicate_alerts(fake_client: PipelineClient) -> None:
    """/explain internally scores; the alert queue must still hold one entry."""
    fake_client.anomaly = 0.9  # type: ignore[attr-defined]
    fake_client.fraud = 0.9  # type: ignore[attr-defined]
    fake_client.action = "DECLINE"  # type: ignore[attr-defined]
    orch = _orch(fake_client)
    tx = _input(cc_num=16, amount=950.0)

    explained = orch.explain(ScoreRequest(transaction=tx))
    assert explained.case_report is not None
    assert len(orch.alerts()) == 1
    assert len(orch.store.history(16)) == 1
