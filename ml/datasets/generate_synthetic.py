"""Deterministic synthetic labeled transaction generator (PLAN §10, §11).

Produces ``datasets/synthetic/transactions_labeled.csv``: a seeded, fully
reproducible corpus of card transactions with a ``is_fraud`` label. The fraud
label is generated from a latent propensity that combines the same signals the
deterministic rule engine uses, plus unobserved noise, so the supervised model
learns patterns that simple thresholds cannot express.

Run from the repository root:

    python ml/datasets/generate_synthetic.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_SEED = 42
DEFAULT_N_ROWS = 10_000

DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "transactions_labeled.csv"
)

# A pool of synthetic card numbers (cc_num) and merchant labels so the
# dataset can build a customer<->merchant graph (PLAN 12). Merchants are named
# per-MCC so shared-merchant edges form naturally; a small fraud ring shares
# one merchant and is labelled fraud to seed the graph axis.
N_CUSTOMERS = 500
FRAUD_RING_SIZE = 8  # accounts that share one merchant and are all fraud
FRAUD_RING_MERCHANT = "fraud_Kerluke"

# Timestamps span the 30 days before the dataset's generation moment so the
# graph engine's default 30-day window sees the full history.
_WINDOW_DAYS = 30

# Merchant category codes with a prior fraud-risk band in [0, 1]. The prior is
# deliberately coarse; the model learns finer interactions from the data.
MCC_RISK: dict[int, float] = {
    5411: 0.10,  # grocery stores
    4900: 0.10,  # utilities
    4121: 0.20,  # taxis
    5412: 0.20,  # supermarkets
    5712: 0.25,  # furniture / department
    5814: 0.30,  # fast food
    7995: 0.30,  # gambling
    5691: 0.35,  # clothing
    5311: 0.40,  # department stores (high value)
    5812: 0.45,  # restaurants (card-not-present risk)
    4814: 0.55,  # telecom
    5968: 0.70,  # digital goods / subscriptions
    4829: 0.80,  # money transfer
    6011: 0.85,  # cash advances
}

# Coefficients of the latent fraud propensity logit. Sign/scale are chosen to
# mirror domain knowledge: untrusted device/network, impossible travel, new
# devices, night hours, velocity, and high-risk MCCs all raise fraud odds.
_LATENT_COEFFICIENTS: dict[str, float] = {
    "intercept": -7.4,
    "amount_log": 0.10,
    "mcc_risk": 1.30,
    "velocity_5m": 0.10,
    "device_untrusted": 1.60,
    "network_untrusted": 1.35,
    "impossible_travel": 2.30,
    "new_device": 1.80,
    "night_hour": 0.55,
    "weekend": 0.35,
    "distance_km": 0.0012,
}

FEATURE_COLUMNS: list[str] = [
    "amount_log",
    "mcc_risk",
    "velocity_5m",
    "device_trust",
    "network_trust",
    "impossible_travel",
    "new_device",
    "hour_of_day",
    "weekend",
    "distance_km",
]


def _merchant_for(mcc: int, rng: np.random.Generator) -> str:
    """A deterministic-ish merchant name per MCC so accounts share merchants."""
    # Map MCC to a stable name stem; a few merchants per category.
    stems = {
        5411: "GroceryMart",
        4900: "UtilityCo",
        4121: "CityTaxi",
        5412: "SuperMart",
        5712: "HomeGoods",
        5814: "FastBites",
        7995: "BetHouse",
        5691: "ApparelShop",
        5311: "DeptStore",
        5812: "CafeNapoli",
        4814: "TelecomNet",
        5968: "DigitalGoods",
        4829: "WireTransferPlus",
        6011: "CashAdvance",
    }
    stem = stems.get(mcc, f"MCC{mcc}")
    return f"{stem}{int(rng.integers(0, 3))}"  # 3 merchants per stem


def generate(n_rows: int = DEFAULT_N_ROWS, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Return ``n_rows`` seeded synthetic labeled transactions.

    Fully deterministic for a given ``seed``: same rows, same labels, same CSV.
    Carries ``cc_num``, ``merchant`` and ``timestamp`` so the graph engine
    (PLAN 12) can backfill its customer<->merchant store from this same file.
    """
    rng = np.random.default_rng(seed)

    # Reserve FRAUD_RING_SIZE rows for the injected fraud ring so the total row
    # count equals n_rows exactly (tests rely on this). For tiny n_rows we skip
    # the ring entirely to preserve the contract.
    ring_n = FRAUD_RING_SIZE if n_rows > FRAUD_RING_SIZE else 0
    base_n = n_rows - ring_n

    mccs = np.array(sorted(MCC_RISK))
    mcc_idx = rng.integers(0, len(mccs), size=base_n)
    mcc = mccs[mcc_idx]
    mcc_risk = np.array([MCC_RISK[int(code)] for code in mcc])

    # Deterministic customer ids (cc_num) drawn from a fixed pool.
    cc_num = rng.integers(1_000_000_000_000_000, 1_000_000_000_000_000 + N_CUSTOMERS, size=base_n)

    # Merchant label per MCC: a few named merchants per category so accounts
    # genuinely share merchants (and thus form shared-merchant graph edges).
    merchant = np.array([_merchant_for(int(code), rng) for code in mcc], dtype=object)

    # Timestamps spread evenly across the trailing 30-day window.
    base_unix = (np.datetime64("2026-09-15T00:00:00", "s") - np.timedelta64(0, "s")).astype(
        np.int64
    )
    seconds_in_window = _WINDOW_DAYS * 24 * 3600
    ts_unix = base_unix - rng.integers(0, seconds_in_window, size=base_n)
    timestamp = pd.to_datetime(ts_unix, unit="s", utc=True).astype(str)

    # Inject a fraud ring: ring_n accounts that all transact at one shared
    # merchant (FRAUD_RING_MERCHANT) within a tight window and are all labelled
    # fraud. This gives the graph axis a clear, detectable cluster.
    ring_customers = np.array(
        [4_000_000_000_000_000 + i for i in range(ring_n)]
    )
    ring_ts = pd.to_datetime(
        base_unix - rng.integers(0, 3600, size=ring_n), unit="s", utc=True
    ).astype(str)
    ring_amounts = np.round(np.exp(rng.normal(4.4, 0.6, size=ring_n)) * 100).astype(int)

    # amount in minor units, log-normal; most spend is small with a fat tail
    amount_minor = np.round(np.exp(rng.normal(4.4, 0.95, size=base_n)) * 100).astype(int)
    amount_log = np.log1p(amount_minor)

    # hour of day (slight day-time mass), weekend flag
    hour_of_day = rng.integers(0, 24, size=base_n)
    weekend = rng.integers(0, 2, size=base_n)
    night_hour = ((hour_of_day < 6) | (hour_of_day >= 23)).astype(int)

    # trust signals: mostly trusted; untrusted/unknown are minority states
    device_trust = rng.choice([1, 0, -1], size=base_n, p=[0.72, 0.18, 0.10])
    network_trust = rng.choice([1, 0, -1], size=base_n, p=[0.78, 0.13, 0.09])
    device_untrusted = (device_trust == 0).astype(int)
    network_untrusted = (network_trust == 0).astype(int)

    # velocity: elevated when the device is untrusted or new
    velocity_5m = rng.poisson(1.5 + 4.0 * device_untrusted + 3.0 * (rng.random(base_n) < 0.05))

    new_device = rng.binomial(1, 0.08, size=base_n)

    # distance: log-normal; impossible-travel events imply long distances
    distance_km = np.round(np.exp(rng.normal(1.6, 1.2, size=base_n)), 2)
    impossible_travel = rng.binomial(1, 0.03, size=base_n)
    distance_km = np.where(
        impossible_travel == 1,
        distance_km + rng.integers(500, 5000, size=base_n),
        distance_km,
    )

    logit = (
        _LATENT_COEFFICIENTS["intercept"]
        + _LATENT_COEFFICIENTS["amount_log"] * amount_log
        + _LATENT_COEFFICIENTS["mcc_risk"] * mcc_risk
        + _LATENT_COEFFICIENTS["velocity_5m"] * velocity_5m
        + _LATENT_COEFFICIENTS["device_untrusted"] * device_untrusted
        + _LATENT_COEFFICIENTS["network_untrusted"] * network_untrusted
        + _LATENT_COEFFICIENTS["impossible_travel"] * impossible_travel
        + _LATENT_COEFFICIENTS["new_device"] * new_device
        + _LATENT_COEFFICIENTS["night_hour"] * night_hour
        + _LATENT_COEFFICIENTS["weekend"] * weekend
        + _LATENT_COEFFICIENTS["distance_km"] * distance_km
        + rng.normal(0.0, 0.7, size=base_n)  # unobserved latent factor
    )
    fraud_probability = 1.0 / (1.0 + np.exp(-logit))
    is_fraud = rng.binomial(1, fraud_probability).astype(int)

    frame = pd.DataFrame(
        {
            "transaction_id": [f"tx_{i:05d}" for i in range(base_n)],
            "cc_num": cc_num,
            "merchant": merchant,
            "timestamp": timestamp,
            "amount_minor": amount_minor,
            "amount_log": amount_log,
            "mcc": mcc,
            "mcc_risk": mcc_risk,
            "hour_of_day": hour_of_day,
            "weekend": weekend,
            "velocity_5m": velocity_5m,
            "device_trust": device_trust,
            "network_trust": network_trust,
            "impossible_travel": impossible_travel,
            "new_device": new_device,
            "distance_km": distance_km,
            "is_fraud": is_fraud,
        }
    )
    if ring_n == 0:
        return frame
    # Prepend the fraud ring so the graph has a clear shared-merchant cluster.
    ring_full = pd.DataFrame(index=range(ring_n), columns=frame.columns)
    ring_full["transaction_id"] = [f"ring_{i:04d}" for i in range(ring_n)]
    ring_full["cc_num"] = ring_customers
    ring_full["merchant"] = FRAUD_RING_MERCHANT
    ring_full["timestamp"] = ring_ts
    ring_full["amount_minor"] = ring_amounts
    ring_full["amount_log"] = np.log1p(ring_amounts)
    ring_full["mcc"] = np.full(ring_n, 4829, dtype=object)
    ring_full["mcc_risk"] = float(MCC_RISK[4829])
    # Ring model-feature columns drawn deterministically so they're valid inputs.
    ring_full["hour_of_day"] = rng.integers(0, 24, size=ring_n)
    ring_full["weekend"] = rng.integers(0, 2, size=ring_n)
    ring_full["velocity_5m"] = rng.poisson(2.0, size=ring_n)
    ring_full["device_trust"] = rng.choice([1, 0, -1], size=ring_n, p=[0.4, 0.4, 0.2])
    ring_full["network_trust"] = rng.choice([1, 0, -1], size=ring_n, p=[0.5, 0.3, 0.2])
    ring_full["impossible_travel"] = rng.binomial(1, 0.2, size=ring_n)
    ring_full["new_device"] = rng.binomial(1, 0.5, size=ring_n)
    ring_full["distance_km"] = np.round(np.exp(rng.normal(2.0, 1.0, size=ring_n)), 2)
    ring_full["is_fraud"] = 1  # the whole ring is confirmed fraud
    return pd.concat([ring_full, frame], ignore_index=True)


def _int(value: str) -> int:
    return int(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the synthetic labeled transaction dataset."
    )
    parser.add_argument(
        "--n-rows", type=_int, default=DEFAULT_N_ROWS, help="Number of transactions (default 10000)"
    )
    parser.add_argument("--seed", type=_int, default=DEFAULT_SEED, help="Random seed (default 42)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    args = parser.parse_args()

    frame = generate(n_rows=args.n_rows, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    fraud_rate = float(frame["is_fraud"].mean())
    print(f"Wrote {len(frame)} rows to {args.output}")
    print(f"Fraud rate: {fraud_rate:.2%} (target ~3%)")


if __name__ == "__main__":
    main()
