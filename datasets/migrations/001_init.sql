-- VeriPay initial schema (PLAN §22). PostgreSQL.
CREATE TABLE IF NOT EXISTS users (
    user_id          TEXT PRIMARY KEY,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS devices (
    device_id        TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    platform         TEXT NOT NULL CHECK (platform IN ('ios','android')),
    public_key_pem   TEXT,
    trust_state      TEXT NOT NULL DEFAULT 'UNKNOWN',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS funding_cards (
    funding_card_id  TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- PLAN §22 — VirtualCardToken entity
CREATE TABLE IF NOT EXISTS virtual_card_tokens (
    token_id                 TEXT PRIMARY KEY,
    user_id                  TEXT NOT NULL REFERENCES users(user_id),
    parent_funding_card_id   TEXT NOT NULL REFERENCES funding_cards(funding_card_id),
    merchant_lock_id         TEXT,
    dcvv_seed_key            TEXT NOT NULL,
    dcvv_refresh_interval_sec INTEGER NOT NULL,
    usage_limit_amount       BIGINT NOT NULL,
    expires_at               TIMESTAMPTZ NOT NULL,
    status                   TEXT NOT NULL CHECK (status IN ('ACTIVE','EXHAUSTED','REVOKED')),
    type                     TEXT NOT NULL CHECK (type IN ('SINGLE_USE','MERCHANT_LOCKED','SUBSCRIPTION','DYNAMIC_CVV')),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES users(user_id),
    mti              TEXT NOT NULL CHECK (mti IN ('0100','0110','0400')),
    channel          TEXT NOT NULL CHECK (channel IN ('CARD_PRESENT','CARD_NOT_PRESENT')),
    merchant_id      TEXT,
    mcc              TEXT,
    currency         TEXT NOT NULL,
    amount_minor     BIGINT NOT NULL,
    payment_instrument TEXT,
    timestamp_unix_ms BIGINT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id         BIGSERIAL PRIMARY KEY,
    transaction_id   TEXT NOT NULL REFERENCES transactions(transaction_id),
    event_type       TEXT NOT NULL,
    payload          JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_ts ON transactions(user_id, timestamp_unix_ms);
CREATE INDEX IF NOT EXISTS idx_audit_tx ON audit_log(transaction_id);
