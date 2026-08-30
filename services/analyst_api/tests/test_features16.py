from datetime import UTC, datetime, timedelta

from veripay_analyst_api.features import FEATURE_COLUMNS
from veripay_analyst_api.features16 import FEATURES16, compute_features16, map_to_model
from veripay_analyst_api.models import Decision, GeoPoint, TransactionInput
from veripay_analyst_api.profiles import BaselineMetrics, StoredTransaction

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)  # Monday, 10:00


def _tx(
    txid: str,
    ts: datetime,
    amount: float = 20.0,
    merchant: str = "m_home",
    category: str = "retail",
) -> StoredTransaction:
    return StoredTransaction(
        transaction_id=txid,
        cc_num=1,
        amount=amount,
        merchant=merchant,
        category=category,
        timestamp=ts,
        location=GeoPoint(lat=40.0, lon=-74.0),
        merchant_location=GeoPoint(lat=40.0, lon=-74.1),
        decision=Decision.PASS,
    )


def _current(
    ts: datetime = _BASE,
    amount: float = 100.0,
    merchant: str = "m_current",
    category: str = "travel",
) -> TransactionInput:
    return TransactionInput(
        transaction_id="current",
        cc_num=1,
        amount=amount,
        merchant=merchant,
        category=category,
        timestamp=ts,
    )


def test_all_sixteen_features_are_emitted() -> None:
    features = compute_features16(_current(), [])
    assert set(features.keys()) == set(FEATURES16)
    assert len(FEATURES16) == 16


def test_velocity_counts_only_past_transactions() -> None:
    history = [
        _tx("p1", _BASE - timedelta(minutes=10)),
        _tx("p2", _BASE - timedelta(minutes=40)),
        _tx("p3", _BASE - timedelta(hours=3)),
    ]
    features = compute_features16(_current(_BASE), history)
    assert features["txn_count_1h"] == 2.0
    assert features["txn_count_24h"] == 3.0
    assert features["amt_sum_1h"] == 40.0  # p1 + p2 within the hour


def test_causality_future_transaction_does_not_change_features() -> None:
    history = [_tx("p", _BASE - timedelta(minutes=10))]
    current = _current(_BASE)
    before = compute_features16(current, history)
    after = compute_features16(current, history + [_tx("future", _BASE + timedelta(hours=1))])
    assert before == after


def test_merchant_and_category_novelty() -> None:
    history = [_tx("p", _BASE - timedelta(days=2), merchant="m_amazon", category="ecommerce")]
    features = compute_features16(_current(_BASE, merchant="m_new", category="travel"), history)
    assert features["is_new_merchant"] == 1.0
    assert features["is_new_category"] == 1.0

    repeat = compute_features16(_current(_BASE, merchant="m_amazon", category="ecommerce"), history)
    assert repeat["is_new_merchant"] == 0.0
    assert repeat["is_new_category"] == 0.0
    assert repeat["days_since_first_seen_merchant"] == 2.0


def test_amount_ratio_and_zscore_clipped() -> None:
    metrics = BaselineMetrics(median_amount=50.0, mean_amount=100.0, amount_std=1.0, count=10)
    features = compute_features16(_current(_BASE, amount=100.0), [], metrics)
    assert features["amt_over_median_90d"] == 2.0
    assert features["amt_zscore_90d"] == 0.0  # amount == mean

    huge = compute_features16(_current(_BASE, amount=10000.0), [], metrics)
    assert huge["amt_zscore_90d"] == 10.0  # clipped at ±10


def test_temporal_features() -> None:
    metrics = BaselineMetrics(hour_mode=10, count=5)
    features = compute_features16(_current(_BASE, amount=10.0), [], metrics)
    assert features["hour_of_day"] == 10.0
    assert features["is_night"] == 0.0
    assert features["hour_deviation_from_customer_mode"] == 0.0

    night = compute_features16(
        TransactionInput(
            transaction_id="n",
            cc_num=1,
            amount=10.0,
            merchant="m",
            timestamp=datetime(2026, 8, 11, 3, 0, tzinfo=UTC),
        ),
        [],
        metrics,
    )
    assert night["is_night"] == 1.0


def test_map_to_model_emits_exact_model_columns() -> None:
    features = compute_features16(_current(_BASE), [], None)
    model = map_to_model(features, _current(_BASE), [])
    assert set(model.keys()) == set(FEATURE_COLUMNS)
    assert model["hour_of_day"] == 10.0
