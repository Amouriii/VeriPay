-- Fraud Operations database: analyst-facing fraud investigation and decision data.
CREATE TABLE IF NOT EXISTS fraud_transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_transaction_id TEXT NOT NULL,
    issuer_account_id TEXT,
    merchant_id TEXT,
    amount_minor BIGINT NOT NULL,
    currency TEXT NOT NULL,
    decision TEXT,
    occurred_at_unix_ms BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES fraud_transactions(transaction_id),
    unified_score NUMERIC(5, 2) NOT NULL CHECK (unified_score BETWEEN 0 AND 100),
    decision TEXT NOT NULL CHECK (decision IN ('ALLOW', 'VERIFY', 'BLOCK', 'REVERSE')),
    model_version_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS risk_factors (
    factor_id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES risk_assessments(assessment_id),
    factor_code TEXT NOT NULL,
    contribution NUMERIC(8, 4),
    evidence JSONB
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES fraud_transactions(transaction_id),
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS investigations (
    investigation_id TEXT PRIMARY KEY,
    alert_id TEXT REFERENCES fraud_alerts(alert_id),
    assigned_to TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analyst_actions (
    action_id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id),
    analyst_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status ON fraud_alerts(status);
CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations(status);
