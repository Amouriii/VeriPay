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


def generate(n_rows: int = DEFAULT_N_ROWS, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Return ``n_rows`` seeded synthetic labeled transactions.

    Fully deterministic for a given ``seed``: same rows, same labels, same CSV.
    """
    rng = np.random.default_rng(seed)

    mccs = np.array(sorted(MCC_RISK))
    mcc_idx = rng.integers(0, len(mccs), size=n_rows)
    mcc = mccs[mcc_idx]
    mcc_risk = np.array([MCC_RISK[int(code)] for code in mcc])

    # amount in minor units, log-normal; most spend is small with a fat tail
    amount_minor = np.round(np.exp(rng.normal(4.4, 0.95, size=n_rows)) * 100).astype(int)
    amount_log = np.log1p(amount_minor)

    # hour of day (slight day-time mass), weekend flag
    hour_of_day = rng.integers(0, 24, size=n_rows)
    weekend = rng.integers(0, 2, size=n_rows)
    night_hour = ((hour_of_day < 6) | (hour_of_day >= 23)).astype(int)

    # trust signals: mostly trusted; untrusted/unknown are minority states
    device_trust = rng.choice([1, 0, -1], size=n_rows, p=[0.72, 0.18, 0.10])
    network_trust = rng.choice([1, 0, -1], size=n_rows, p=[0.78, 0.13, 0.09])
    device_untrusted = (device_trust == 0).astype(int)
    network_untrusted = (network_trust == 0).astype(int)

    # velocity: elevated when the device is untrusted or new
    velocity_5m = rng.poisson(1.5 + 4.0 * device_untrusted + 3.0 * (rng.random(n_rows) < 0.05))

    new_device = rng.binomial(1, 0.08, size=n_rows)

    # distance: log-normal; impossible-travel events imply long distances
    distance_km = np.round(np.exp(rng.normal(1.6, 1.2, size=n_rows)), 2)
    impossible_travel = rng.binomial(1, 0.03, size=n_rows)
    distance_km = np.where(
        impossible_travel == 1,
        distance_km + rng.integers(500, 5000, size=n_rows),
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
        + rng.normal(0.0, 0.7, size=n_rows)  # unobserved latent factor
    )
    fraud_probability = 1.0 / (1.0 + np.exp(-logit))
    is_fraud = rng.binomial(1, fraud_probability).astype(int)

    return pd.DataFrame(
        {
            "transaction_id": [f"tx_{i:05d}" for i in range(n_rows)],
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
