-- VeriPay expansion schema: Banking/FI + Business/Merchant entities (PLAN Expansion §2, §3).

-- --- Financial Institution entities ---
CREATE TABLE IF NOT EXISTS issuer_accounts (
    issuer_account_id   TEXT PRIMARY KEY,
    bank_routing_number  TEXT NOT NULL,
    settlement_account   TEXT NOT NULL,
    network              TEXT NOT NULL CHECK (network IN ('VISA','MASTERCARD','AMEX','DISCOVER')),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS network_settlement_batches (
    batch_id             TEXT PRIMARY KEY,
    issuer_account_id    TEXT NOT NULL REFERENCES issuer_accounts(issuer_account_id),
    network              TEXT NOT NULL CHECK (network IN ('VISA','MASTERCARD','AMEX','DISCOVER')),
    total_amount_minor   BIGINT NOT NULL,
    currency             TEXT NOT NULL,
    settlement_date_unix_ms BIGINT NOT NULL,
    status               TEXT NOT NULL CHECK (status IN ('PENDING','SETTLED','REJECTED','REVERSED')),
    transaction_count    INTEGER NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS card_network_messages (
    message_id           TEXT PRIMARY KEY,
    batch_id             TEXT REFERENCES network_settlement_batches(batch_id),
    raw_message_ref       TEXT NOT NULL,  -- tokenized reference, never raw PAN
    network              TEXT NOT NULL CHECK (network IN ('VISA','MASTERCARD','AMEX','DISCOVER')),
    message_type         TEXT NOT NULL,
    timestamp_unix_ms    BIGINT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ledger_audits (
    ledger_id            BIGSERIAL PRIMARY KEY,
    batch_id             TEXT REFERENCES network_settlement_batches(batch_id),
    entry_type           TEXT NOT NULL CHECK (entry_type IN ('debit','credit','reversal')),
    amount_minor         BIGINT NOT NULL,
    currency             TEXT NOT NULL,
    account_ref          TEXT NOT NULL,
    posted_at_unix_ms    BIGINT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- Business / Merchant entities ---
CREATE TABLE IF NOT EXISTS merchant_profiles (
    merchant_id          TEXT PRIMARY KEY,
    business_name        TEXT NOT NULL,
    category             TEXT NOT NULL CHECK (category IN ('ECOMMERCE','B2B_CORPORATE','RETAIL','DIGITAL_GOODS')),
    mcc                  TEXT,
    webhook_url          TEXT,
    active               BOOLEAN NOT NULL DEFAULT true,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS merchant_lock_rules (
    lock_id              TEXT PRIMARY KEY,
    merchant_id          TEXT NOT NULL REFERENCES merchant_profiles(merchant_id),
    allowed_mccs         TEXT,           -- comma-separated MCC list
    max_spend_per_txn_minor BIGINT,
    daily_spend_limit_minor  BIGINT,
    enforce_merchant_lock   BOOLEAN NOT NULL DEFAULT true,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corporate_vcn_policies (
    policy_id            TEXT PRIMARY KEY,
    business_id          TEXT NOT NULL,
    max_vendor_spend_minor BIGINT,
    monthly_spend_limit_minor BIGINT,
    allowed_mccs         TEXT,
    vcn_expiry_hours     INTEGER,
    require_biometric_provisioning BOOLEAN NOT NULL DEFAULT false,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dispute_cases (
    dispute_id           TEXT PRIMARY KEY,
    transaction_id       TEXT NOT NULL REFERENCES transactions(transaction_id),
    merchant_id          TEXT REFERENCES merchant_profiles(merchant_id),
    issuer_account_id    TEXT REFERENCES issuer_accounts(issuer_account_id),
    amount_minor         BIGINT NOT NULL,
    currency             TEXT NOT NULL,
    status               TEXT NOT NULL CHECK (status IN ('OPENED','REPRESENTED','ACCEPTED','REVERSED','EXPIRED')),
    reason               TEXT NOT NULL CHECK (reason IN ('FRAUD','AUTHORIZATION','PROCESSING_ERROR','CONSUMER','MERCHANT')),
    evidence_ref         TEXT,
    opened_at_unix_ms    BIGINT NOT NULL,
    resolved_at_unix_ms  BIGINT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- Compliance triggers ---
CREATE TABLE IF NOT EXISTS compliance_triggers (
    trigger_id           TEXT PRIMARY KEY,
    transaction_id       TEXT NOT NULL REFERENCES transactions(transaction_id),
    standard             TEXT NOT NULL CHECK (standard IN ('PCI_DSS_4_0','PSD3_SCA','NETWORK_ZERO_TRUST')),
    requirement          TEXT NOT NULL,
    satisfied            BOOLEAN NOT NULL DEFAULT false,
    detail               TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_disputes_tx ON dispute_cases(transaction_id);
CREATE INDEX IF NOT EXISTS idx_compliance_tx ON compliance_triggers(transaction_id);
CREATE INDEX IF NOT EXISTS idx_settlement_issuer ON network_settlement_batches(issuer_account_id);
