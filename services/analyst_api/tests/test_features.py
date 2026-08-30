import math
from datetime import UTC, datetime, timedelta

from veripay_analyst_api.features import build_features
from veripay_analyst_api.models import Decision, TransactionInput
from veripay_analyst_api.profiles import StoredTransaction

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)  # a Monday


def _tx(txid: str, ts: datetime, amount: float = 20.0) -> StoredTransaction:
    return StoredTransaction(
        transaction_id=txid,
        cc_num=1,
        amount=amount,
        merchant="m_" + txid,
        category="retail",
        timestamp=ts,
        location=None,
        merchant_location=None,
        decision=Decision.PASS,
    )


def _current(ts: datetime, amount: float = 100.0) -> TransactionInput:
    return TransactionInput(
        transaction_id="current",
        cc_num=1,
        amount=amount,
        merchant="m_current",
        timestamp=ts,
    )


def test_build_features_basics() -> None:
    current = _current(_BASE, amount=100.0)
    features = build_features(current, [])
    # amount_log is in minor units (cents) to match the training matrix.
    assert features["amount_log"] == round(math.log1p(100.0 * 100.0), 4)
    assert features["hour_of_day"] == 10.0
    assert features["weekend"] == 0.0  # Monday
    assert features["velocity_5m"] == 0.0
    assert features["impossible_travel"] == 0.0


def test_velocity_counts_only_past_transactions_within_five_minutes() -> None:
    history = [
        _tx("past_recent", _BASE - timedelta(minutes=3)),
        _tx("past_old", _BASE - timedelta(minutes=30)),
    ]
    features = build_features(_current(_BASE), history)
    assert features["velocity_5m"] == 1.0


def test_causality_future_transaction_does_not_change_features() -> None:
    history_no_future = [_tx("past_recent", _BASE - timedelta(minutes=3))]
    current = _current(_BASE)
    before = build_features(current, history_no_future)

    history_with_future = history_no_future + [_tx("future", _BASE + timedelta(hours=1))]
    after = build_features(current, history_with_future)

    assert before == after
    assert after["velocity_5m"] == 1.0
