-- Merchant database: merchant users, controls, transactions, and disputes.
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    category TEXT NOT NULL,
    mcc TEXT,
    webhook_url TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS merchant_users (
    merchant_user_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    customer_transaction_id TEXT NOT NULL,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    occurred_at_unix_ms BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    rule_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS limits (
    limit_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    max_spend_per_txn_minor BIGINT,
    daily_spend_limit_minor BIGINT,
    monthly_spend_limit_minor BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS disputes (
    dispute_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    merchant_transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    status TEXT NOT NULL,
    reason TEXT,
    evidence_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_merchant_transactions_merchant_ts ON transactions(merchant_id, occurred_at_unix_ms);
