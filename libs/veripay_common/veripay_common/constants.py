"""Canonical thresholds and configuration constants (PLAN §7, §9, §14, §15)."""

from __future__ import annotations

# --- Operational risk tiers (blueprint §4) ---
RISK_TIER_NO_RISK_MAX = 5
RISK_TIER_LOW_MAX = 25
RISK_TIER_MODERATE_MAX = 50
RISK_TIER_HIGH_MAX = 100

# Legacy RiskBand projections retained for migration compatibility.
RISK_SCORE_APPROVE_MAX = 25  # 0-25 => APPROVE projection
RISK_SCORE_VERIFY_MAX = 50  # 26-50 => VERIFY projection
RISK_SCORE_BLOCK_MAX = 100  # 51-100 => BLOCK projection

# --- Dual-latency processing budgets (blueprint §3) ---
FAST_PATH_DEADLINE_MS = 500
FAST_PATH_ML_BUDGET_MS = 50
SECONDARY_PATH_DEADLINE_MS = 5_000
VERIFICATION_TOKEN_MIN_TTL_SEC = 10
VERIFICATION_TOKEN_MAX_TTL_SEC = 30
DEFAULT_VERIFICATION_TOKEN_TTL_SEC = 30

# --- GPV distance classification (PLAN §14) ---
GPV_MATCH_MAX_M = 100.0
GPV_LIKELY_MATCH_MAX_M = 300.0

# --- H3 resolutions (PLAN §14) ---
H3_RES_SHOPPING_AREA = 8
H3_RES_STORE_LEVEL = 10

# --- Device challenge nonces (PLAN §15) ---
CHALLENGE_NONCE_BITS = 128
CHALLENGE_NONCE_TTL_SEC = 90

# --- Streaming windows (PLAN §9) ---
WINDOWS = {
    "tx_count_5m": {"type": "tumbling", "size": "5min"},
    "tx_count_1h": {"type": "tumbling", "size": "1h"},
    "tx_count_24h": {"type": "tumbling", "size": "24h"},
    "spend_1h": {"type": "tumbling", "size": "1h"},
    "spend_24h": {"type": "tumbling", "size": "24h"},
    "token_gen_1h": {"type": "tumbling", "size": "1h"},
}

# --- Component weights for risk fusion (PLAN §18) ---
# Weights are redistributed across available components when a signal is missing.
DEFAULT_FUSION_WEIGHTS = {
    "supervised": 0.30,
    "anomaly": 0.15,
    "graph": 0.10,
    "rules": 0.15,
    "device": 0.10,
    "gpv": 0.05,
    "financial": 0.10,
    "external": 0.05,
}

# --- Reason codes (PLAN §13, §20) ---
REASON_DCVV_MISMATCH = "DCVV_MISMATCH"
REASON_MERCHANT_LOCK_VIOLATION = "MERCHANT_LOCK_VIOLATION"
REASON_BURNER_VELOCITY = "BURNER_VELOCITY_SPIKE"
REASON_IMPOSSIBLE_TRAVEL = "IMPOSSIBLE_TRAVEL"
REASON_SIGNAL_CONTRADICTION = "SIGNAL_CONTRADICTION"
REASON_NEW_DEVICE = "NEW_DEVICE"
