-- Mobile database: mobile identity, device security, and verification records.
CREATE TABLE IF NOT EXISTS mobile_users (
    mobile_user_id TEXT PRIMARY KEY,
    customer_user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS registered_devices (
    device_id TEXT PRIMARY KEY,
    mobile_user_id TEXT NOT NULL REFERENCES mobile_users(mobile_user_id),
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    attestation_provider TEXT,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS device_security (
    security_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES registered_devices(device_id),
    integrity_state TEXT NOT NULL,
    public_key_fingerprint TEXT,
    last_checked_at TIMESTAMPTZ,
    detail JSONB
);

CREATE TABLE IF NOT EXISTS verification_requests (
    request_id TEXT PRIMARY KEY,
    mobile_user_id TEXT NOT NULL REFERENCES mobile_users(mobile_user_id),
    transaction_id TEXT NOT NULL,
    challenge_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS verification_attempts (
    attempt_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES verification_requests(request_id),
    device_id TEXT REFERENCES registered_devices(device_id),
    result TEXT NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS push_tokens (
    push_token_id TEXT PRIMARY KEY,
    mobile_user_id TEXT NOT NULL REFERENCES mobile_users(mobile_user_id),
    device_id TEXT REFERENCES registered_devices(device_id),
    provider TEXT NOT NULL,
    token TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS mobile_audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    mobile_user_id TEXT,
    device_id TEXT,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
