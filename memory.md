# Project Memory

## Project

VeriPay is a real-time payment fraud-detection platform organized as a Python
service monorepo with shared contracts in `proto/`, shared Python types in
`libs/veripay_common`, backend services in `services/`, and a React frontend in
`web/`.

## Ownership

Developer 1 owns the backend/API gateway scope. Developer 2 owns frontend
applications and portals. Developer 3 owns the LLM investigation agent and
explainability. Developer 4 owns streaming, feature engineering, and ML models.
Developer 5 owns policy, security, mobile, and core risk engines.

## Completed Developer 1 foundation

PR #5 is merged into `main` and includes transaction ingress, PCI-safe token
vault lifecycle and dCVV validation, append-only audit storage, focused tests,
and dedicated CI jobs.

## Developer 5 implementation

PR #7 contains the deterministic rule engine and weighted risk fusion foundation.
It is open against `main`, has green checks, and remains blocked by repository
branch policy. The current branch `feat/developer5-core-expansion` contains the
next implementation slices:

- Cost-aware decision routing with explicit expected-cost candidates, hard
  reversal/compliance/challenge controls, and evidence-unavailable handling.
- Device integrity provider boundaries, single-use expiring challenge nonces,
  deterministic attestation adapter, and GPV distance evaluation.
- Merchant policy repository/CRUD and deterministic MCC, transaction, daily,
  velocity, and disabled-policy findings.
- Explicit PCI tokenization, PSD3/SCA, device, and network zero-trust outcomes.
- Financial and external context normalization with provenance, freshness,
  confidence, and unavailable/stale states.
- Append-only, idempotent analyst review feedback and filtered export boundary.
- Dispute creation, idempotent case handling, lifecycle transitions, evidence
  references, sync-provider boundary, and regulatory reports.
- FI Ops APIs for risk evidence, audit/state views, dispute transitions, access
  policy, and regulatory summaries.
- Business Portal APIs for transactions, spend summaries, merchant policy CRUD,
  dispute views/transitions, webhook delivery status, and access policy.
- iOS SwiftPM provider contracts for Secure Enclave/App Attest, biometric-gated
  dCVV access, and expiring single-use nonces.
- Android Kotlin provider contracts for Keystore/Play Integrity, biometric-gated
  dCVV access, and expiring single-use nonces.
- Local infrastructure documentation, corrected Compose build contexts, and
  dependency inclusion for standalone service-stack validation.

## Verification completed

- Full Python suite: **111 passed**, one existing FastAPI/httpx deprecation
  warning remains.
- Focused control group: **28 passed**.
- Context and feedback group: **20 passed**.
- Dispute and portal group: **22 passed**.
- Operational portal/device/context regression group: **27 passed**.
- Ruff check: **passed**.
- Ruff format check: **passed**.
- `git diff --check`: **passed**.
- Web Vitest: **1 passed**.
- Web ESLint: **passed**.
- iOS SwiftPM tests: **3 passed**.
- Compose dependency, backend, and combined configurations: **passed**.
- Local mypy was unavailable because `.venv/bin/mypy` is not installed.
- Android Gradle tests were not run locally because no Gradle wrapper or `gradle`
  executable is available; GitHub CI has an Android job for that environment.

## Engineering boundaries

- Service persistence uses repository/provider protocols and deterministic
  in-memory adapters until the populated PostgreSQL schema is finalized.
- ML scoring, attestation, authentication, network, external context, card
  network, Iceberg, Kafka, and data-lake integrations remain explicit provider
  boundaries.
- No service stores, logs, or returns PAN, CVV, private keys, credentials,
  attestation blobs, or provider secrets.
- Shared `proto/`, migrations, and Avro schemas were not changed by these slices.

## Git and collaboration

Implementation is uncommitted on `feat/developer5-core-expansion` until explicitly
requested. Branch protection requires pull requests for changes to `main`.
