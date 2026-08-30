-- Bank database: financial institution operations and reporting data.
CREATE TABLE IF NOT EXISTS bank_users (
    bank_user_id TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fraud_statistics (
    statistic_id BIGSERIAL PRIMARY KEY,
    bank_id TEXT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    fraud_count BIGINT NOT NULL DEFAULT 0,
    fraud_amount_minor BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS risk_statistics (
    statistic_id BIGSERIAL PRIMARY KEY,
    bank_id TEXT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    average_score NUMERIC(5, 2),
    blocked_count BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transaction_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statistic_date DATE NOT NULL,
    transaction_type VARCHAR(50),
    transaction_count BIGINT NOT NULL DEFAULT 0,
    total_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    average_amount NUMERIC(18, 2)
);

CREATE TABLE IF NOT EXISTS fraud_policies (
    policy_id TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
    policy_name TEXT NOT NULL,
    policy_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_versions (
    model_version_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    deployed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'AVAILABLE'
);

CREATE TABLE IF NOT EXISTS disputes (
    dispute_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    issuer_account_id TEXT,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_ref TEXT,
    opened_at_unix_ms BIGINT NOT NULL,
    resolved_at_unix_ms BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    actor_id TEXT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS issuer_accounts (
    issuer_account_id TEXT PRIMARY KEY,
    bank_routing_number TEXT NOT NULL,
    settlement_account TEXT NOT NULL,
    network TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS network_settlement_batches (
    batch_id TEXT PRIMARY KEY,
    issuer_account_id TEXT NOT NULL REFERENCES issuer_accounts(issuer_account_id),
    total_amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    settlement_date_unix_ms BIGINT NOT NULL,
    status TEXT NOT NULL,
    transaction_count INTEGER NOT NULL DEFAULT 0
);

