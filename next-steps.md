# Next Steps

## Completed in this implementation branch

- Cost-aware decision engine
- Device integrity and GPV boundaries
- Merchant policy evaluation and merchant-rule APIs
- PCI, PSD3/SCA, and network zero-trust compliance evaluation
- Financial and external context normalization
- Append-only analyst feedback loop
- Dispute lifecycle and reporting boundary
- FI Ops Portal backend risk, audit/state, dispute-operation, and regulatory APIs
- Business Portal transaction, spend, policy CRUD, dispute-operation, and webhook APIs
- iOS and Android security SDK contract scaffolds
- Local Compose validation and corrected service build contexts
- Focused CI matrix for all implemented Developer 5 services, mobile SDKs, and
  Compose configuration

## Verification status

- Python: 112 tests passed
- Ruff check and format: passed
- Web Vitest and ESLint: passed
- iOS SwiftPM tests: 3 passed
- Operational portal/device/context regression: 27 tests passed
- Compose dependency, backend, and combined config checks: passed
- Local mypy unavailable
- Local Android Gradle unavailable; CI job added

## Required review and integration work

1. Review and merge PR #7, then rebase or retarget this dependent branch onto
   the merged `main`.
2. Review and open a dedicated pull request for this branch after the final diff
   and CI checks are confirmed.
3. Replace in-memory repositories with PostgreSQL adapters after the populated
   schema, migrations, connection pooling, and transaction conventions are
   finalized.
4. Connect the ML model-serving and feature providers to risk fusion and keep
   decision cost parameters in governed configuration.
5. Integrate real Apple App Attest, Google Play Integrity, WebAuthn/biometric,
   vault, network, external-context, card-network, Kafka, Iceberg, and data-lake
   providers.
6. Add authenticated role enforcement at the FI Ops and Business Portal
   boundaries using the selected identity provider.
7. Run mypy in CI and locally once the development environment includes it, and
   run Android Gradle tests on an Android-enabled runner.
8. Add PostgreSQL/Kafka/Redis integration tests when local infrastructure and
   seeded database fixtures are stable.
