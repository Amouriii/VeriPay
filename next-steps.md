# Next Steps

## Current position

Developer 1's initial backend slices are implemented locally:

- Transaction ingress API
- PCI-safe token vault metadata and lifecycle API
- Append-only audit store API
- Focused tests for all three services
- Dedicated GitHub Actions verification jobs for all three services

## Recommended implementation order

1. Implement merchant ingress:
   - Merchant-facing transaction and webhook APIs
   - VCN issuance request boundary
   - Webhook delivery records and retry-safe event identifiers
2. Implement banking gateway:
   - Authorization adapter boundary
   - ISO 20022/settlement request models
   - Explicit external-provider failure handling
3. Implement corporate spend:
   - Per-merchant spend tracking
   - Corporate VCN policy boundary
   - Daily and per-transaction limits
4. Implement auth orchestration:
   - 3DS challenge lifecycle
   - Biometric/WebAuthn challenge state
   - Idempotent completion and expiration handling
5. Replace in-memory adapters with PostgreSQL adapters after the populated schema is finalized.
6. Add integration tests across ingress, token vault, audit store, and downstream risk services.
7. Add OpenAPI contract validation and database-backed CI checks when those dependencies are stable.

## Verification requirements

Every new backend slice should include:

- Focused unit/API tests
- Ruff lint and format checks
- Mypy-compatible typing
- A focused GitHub Actions job or an update to the shared backend test job
- No secrets, PANs, CVVs, or production credentials in fixtures or logs
