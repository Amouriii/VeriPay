# Assumptions

## Repository and branching

- PR #5 is merged into `main` and contains the Developer 1 backend foundation.
- PR #7 contains the rule/risk foundation, has green checks, and remains blocked
  by branch protection.
- The current Developer 5 expansion is on a dependent feature branch and does
  not rewrite PR #7.
- Changes remain uncommitted until explicitly requested.

## Persistence and providers

- In-memory repositories are deterministic development/test adapters only.
- PostgreSQL persistence will be added after the populated schema and database
  transaction conventions are finalized.
- ML models, feature stores, attestation services, biometric/WebAuthn flows,
  vaults, card networks, external context providers, Kafka, Iceberg, and data
  lakes are represented by explicit boundaries, not live integrations.
- Portal access-policy responses describe required roles; they do not enforce
  identity until the repository's authentication provider is selected and wired.
- Portal policy and dispute actions are injectable composition boundaries; the
  production implementation must delegate them to merchant-policy and dispute
  services rather than rely on the in-memory adapters.

## Risk and compliance

- Rule findings, risk fusion, context scores, and decision routing are
  explainable deterministic foundations, not production-calibrated fraud or loss
  estimates.
- Decision cost defaults are placeholders and require governed business-owner
  calibration.
- Compliance controls are modeled explicitly and fail closed for mandatory
  unavailable evidence by default.
- Regulatory, PCI-DSS, PSD3/SCA, card-network, regional, and retention behavior
  requires legal/security/compliance review before production use.

## Security and privacy

- PAN, CVV, private keys, credentials, attestation blobs, provider secrets, and
  raw biometric data are never stored, logged, or returned by these services or
  test fixtures.
- Mobile implementations expose provider contracts and deterministic test
  adapters. Secure Enclave, Android Keystore, App Attest, Play Integrity, and
  biometric APIs require platform runtime wiring and device testing.
- Device and location signals are sensitive and require production retention,
  access control, and audit policies.

## Verification and CI

- The local Python, web, Swift, Compose, Ruff, and diff checks reported in
  `memory.md` are authoritative for this checkout.
- Local mypy was not available; GitHub CI installs it in the shared lint job.
- Local Android Gradle tests were not available because no Gradle executable or
  wrapper exists in the checkout; a CI job runs them on an Android-capable
  runner.
- Existing FastAPI/httpx test-client deprecation warning is non-failing and
  predates this expansion.
- Focused CI jobs do not start Kafka, Redis, PostgreSQL, WireMock, or external
  providers; Compose CI validates configuration only.
