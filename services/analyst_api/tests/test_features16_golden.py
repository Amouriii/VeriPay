"""Golden regression fixture for ``features16``.

Pins the exact 16 causal features produced for a realistic seeded history so
any future change to the engine — window boundaries, amount stats, distance
math, or temporal logic — is surfaced as a diff instead of silently drifting.

The scenario uses coordinates all on the same meridian (lon = -74.0) so the
distances are interpretable: 0.5° of latitude ≈ 55.6 km on a 6371 km radius
Earth, and the current transaction is one hour after the most recent history
row, so implied velocity equals that distance in km/h.

90-day baseline (from the four history rows): amounts [40, 60, 20, 30],
median 35.0, mean 37.5, sample std 17.078251, modal hour 9.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from veripay_analyst_api.features import FEATURE_COLUMNS
from veripay_analyst_api.features16 import FEATURES16, compute_features16, map_to_model
from veripay_analyst_api.models import Decision, GeoPoint, TransactionInput
from veripay_analyst_api.profiles import ProfileStore, StoredTransaction

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)  # Monday 10:00
_HOME = GeoPoint(lat=40.0, lon=-74.0)


def _tx(
    txid: str,
    amount: float,
    merchant: str,
    category: str,
    ts: datetime,
) -> StoredTransaction:
    return StoredTransaction(
        transaction_id=txid,
        cc_num=1,
        amount=amount,
        merchant=merchant,
        category=category,
        timestamp=ts,
        location=_HOME,
        merchant_location=_HOME,
        decision=Decision.PASS,
    )


def _history() -> list[StoredTransaction]:
    return [
        _tx("h1", 40, "m_home", "grocery", _BASE - timedelta(hours=25)),
        _tx("h2", 60, "m_home", "grocery", _BASE - timedelta(hours=20)),
        _tx("h3", 20, "m_gas", "auto", _BASE - timedelta(hours=3)),
        _tx("h4", 30, "m_home", "grocery", _BASE - timedelta(hours=1)),
    ]


def _current() -> TransactionInput:
    return TransactionInput(
        transaction_id="current",
        cc_num=1,
        amount=100.0,
        merchant="m_flight",  # a merchant this customer has never used
        category="travel",  # a category this customer has never used
        timestamp=_BASE,
        location=GeoPoint(lat=40.5, lon=-74.0),
        merchant_location=GeoPoint(lat=40.5, lon=-74.0),
    )


# Every number below was produced by the engine and cross-checked by hand.
_EXPECTED: dict[str, float] = {
    "txn_count_1h": 1.0,  # only h4 (1h ago) falls inside the 1-hour window
    "txn_count_24h": 3.0,  # h2 (20h), h3 (3h), h4 (1h); h1 (25h) is outside
    "amt_sum_1h": 30.0,  # h4 amount
    "amt_sum_24h": 110.0,  # 60 + 20 + 30
    "amt_over_median_90d": 2.8571,  # 100 / median 35.0
    "amt_zscore_90d": 3.6596,  # (100 - 37.5) / 17.078251
    "is_new_merchant": 1.0,  # "m_flight" unseen in prior history
    "is_new_category": 1.0,  # "travel" unseen in prior history
    "days_since_first_seen_merchant": 0.0,  # merchant is new → 0
    "dist_from_home_km": 55.6,  # home (40.0) → merchant (40.5) on meridian
    "dist_from_prev_txn_km": 55.6,  # last row (40.0) → current (40.5)
    "implied_velocity_kmh": 55.6,  # 55.6 km / 1.0 h
    "hour_of_day": 10.0,
    "is_night": 0.0,  # 10:00 is not 00:00–05:00
    "hours_since_prev_txn": 1.0,  # h4 is exactly one hour earlier
    "hour_deviation_from_customer_mode": 1.0,  # modal hour 9, current hour 10
}


def test_features16_golden_regression() -> None:
    history = _history()
    current = _current()
    metrics = ProfileStore().metrics(history)
    got = compute_features16(current, history, metrics)
    assert set(got) == set(FEATURES16)
    assert len(got) == 16
    assert got == _EXPECTED


def test_features16_golden_maps_to_model_columns() -> None:
    # The golden engine output must still map onto the exact model vector.
    history = _history()
    current = _current()
    metrics = ProfileStore().metrics(history)
    model = map_to_model(compute_features16(current, history, metrics), current, history)
    assert set(model) == set(FEATURE_COLUMNS)
    # amount_log uses minor units (cents) to match the training matrix.
    assert model["amount_log"] == round(math.log1p(100.0 * 100.0), 4)
    assert model["distance_km"] == 55.6
    assert model["velocity_5m"] == 0.0  # no prior transaction within 5 minutes
