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

## Gap-closure session (feat/blueprint-alignment, 2026-08-29)

- Fixed three web TypeScript compile errors that broke `tsc -b` and `npm run
  build`: `BankPages.tsx` referenced undefined `btnPrimary`/`btnSecondary`
  glass-theme button constants (now defined at module top, matching the glass
  console theme), and `CustomerLogin.tsx` passed a nonexistent `variant="teal"`
  prop to `VeriPayMark` (component accepts only `compact`).
- Web verification after fixes: `tsc --noEmit` clean, ESLint clean, Vitest 1
  passed, `npm run build` succeeds.
- Full Python suite: **111 passed**, one existing FastAPI/httpx deprecation
  warning remains.
- Compose dependency/backend/combined config validation re-verified: **passed**.
- iOS SwiftPM tests re-verified: **3 passed**.
- Ruff check: **passed**.
- Ruff format check: **passed**.
- `git diff --check`: **passed**.
- Local mypy was unavailable because `.venv/bin/mypy` is not installed.
- Android Gradle tests were not run locally because no Gradle wrapper or `gradle`
  executable is available; GitHub CI has an Android job for that environment.

## Deliverables session (2026-08-29, feat/blueprint-alignment)

Core-deliverables gap closure for the submission checklist:

- Added a Mermaid system architecture diagram (components, data flow, APIs,
  5 databases, AI placement) to `docs/architecture.md`.
- Expanded `README.md` with tech stack, prerequisites, env-var table, and a
  step-by-step setup guide.
- New docs: `docs/data.md` (sources/preprocessing/schema/splits),
  `docs/ai-justification.md` (model rationale + AI-removal value analysis),
  `docs/evaluation.md` (measured metrics + rules-only baseline),
  `docs/demo.md` (local demo + deployment prep).
- Real ML implementation: `ml/datasets/generate_synthetic.py` (seeded 10k-row
  labeled corpus, ~3.96% fraud), `ml/supervised/train.py` (XGBoost),
  `ml/anomaly/train.py` (Isolation Forest), `ml/registry/model_registry.py`
  (versioned register/rollback), and real `/api/v1/score` endpoints in
  `services/supervised_model` + `services/anomaly_model` (with deterministic
  fallback when the artifact or deps are absent). `services/investigation_agent`
  now exposes `/api/v1/investigate`.
- Served models verified identical to evaluated models (no early stopping).
  Final metrics: XGBoost ROC-AUC 0.9273 / PR-AUC 0.5251; Isolation Forest
  ROC-AUC 0.8831 / PR-AUC 0.5007. Rules-only baseline: 44.7% flag rate @ 8.5%
  precision vs model 3.1% @ 51.1%.
- CI: added `test-ml` job, gitleaks secret scan, dependency review; base
  pytest job now ignores `ml` (covered by test-ml). Compose ML services mount
  `ml/models` and install `[model]` extras.
- Presentation: `docs/presentation/slides.md` (Marp) + generated
  `veripay.pptx` (13 slides) via `docs/presentation/generate_pptx.py`.
- Demo: `scripts/seed-demo.py` drives the whole pipeline over HTTP
  (ingress → rules → XGBoost → Isolation Forest → fusion → decision → LLM
  explanation); verified end-to-end locally.

## vLLM provider session (2026-08-29, feat/blueprint-alignment)

- Implemented `OpenAiCompatibleLlmProvider` in
  `services/investigation_agent/veripay_investigation_agent/providers.py`
  behind the existing `LocalLlmProvider` protocol: OpenAI-compatible vLLM
  chat-completions calls, temperature 0, defensive parsing, and prompt
  rendering that re-redacts the full context (transaction, 30-day baseline,
  macro context) before anything crosses the LLM boundary.
- `provider_from_settings()` selects the provider from new `LLM_*` settings
  (`LLM_PROVIDER=openai_compatible` requires the `openai` package, else
  deterministic). `services/investigation_agent` `evaluate()` now falls back
  to `DeterministicLocalLlmProvider` when the configured provider raises, and
  `LlmExplanation` gained a `fallback` flag.
- `pyproject.toml` gained the `llm` extra (`openai>=1.30`); the Dockerfile
  installs `.[llm]`; `.env.example` and README env table document the new
  variables; `docs/demo.md` gained a "Swap in a real local LLM (vLLM)"
  section; `docs/evaluation.md` and `docs/ai-justification.md` updated.
- Verification: 141 Python tests pass (8 new provider tests); ruff check and
  format clean; mypy clean (129 files). Live-tested against a mock vLLM
  server: vllm provider used when up (`fallback: false`, PAN tokenized in the
  prompt), deterministic fallback when down (`fallback: true`).

## Baseline A/B test session (2026-08-29, feat/blueprint-alignment)

- Added `ml/supervised/baseline.py` (rules-only deterministic flagging:
  velocity > 5, untrusted device/network, impossible travel, MCC risk >= 0.7)
  and `ml/tests/test_baseline.py`, which trains the real pipeline on the
  committed dataset and asserts on the *same* held-out split that the model
  flags **less than half** of the rules' flag rate at strictly better
  precision (guards the AI-value claim in `docs/evaluation.md`; runs in the
  `test-ml` CI job).
- Refactored `ml/supervised/train.py` to expose `split_indices()` (single
  source of truth for the stratified 70/15/15 split); verified byte-identical
  behavior — trained metrics unchanged (roc_auc 0.9273, threshold 0.2131).
- Verification: 142 Python tests pass; ruff check/format clean; git diff
  --check clean; new baseline test passes in ~7s.

## Drift + automated retraining session (2026-08-29, feat/blueprint-alignment)

- Added `ml/drift/` (reference profile computation + PSI detection; `PSI_TRIGGER
  = 0.25`); training pipelines now write `reference_profile.json` next to each
  artifact and record it in the registry (`register(..., reference_profile=...)`).
- New `services/model_monitor` (port 8025): observation window
  (`/api/v1/monitor/observations`), label ingestion (`/monitor/feedback`),
  drift report (`/monitor/drift`), and gated retraining (`/monitor/retrain`)
  that runs the real training CLI on the base dataset + labeled feedback and
  promotes to `latest` only when held-out ROC-AUC clears the champion within
  a tolerance (default 0.01). Feedback labels are pulled from
  `services/feedback_loop` or submitted directly.
- Wiring: added `model_monitor` to the developer5-services CI matrix, compose
  (8025, mounts `ml/models` + `datasets`), README services table, and
  `docs/architecture.md` (AI layer + component table).
- Live-verified: 40 drifted observations -> `DRIFT` (max PSI 12.8); a real
  subprocess retrain scored 0.898 vs the 0.927 champion and was correctly
  REJECTED (registry untouched). The promotion path is covered by unit tests.
- Verification: 17 model_monitor tests + 5 ml/drift tests; ruff check/format
  clean; mypy clean on the new service; full suite green.

## Deployment prep session (2026-08-29, feat/blueprint-alignment)

- Made cloud deployment genuinely ready: `infra/deploy/veripay.Dockerfile`
  (repo-root build context; installs local `veripay-common` first; binds
  `${PORT:-8000}`), `infra/deploy/render.yaml` (Blueprint: ingress, rule
  engine, risk fusion, decision engine, investigation agent, feedback loop,
  dashboard), `infra/deploy/railway.json`, `scripts/live-demo-tunnel.sh`
  (account-free Cloudflare quick tunnel), and `docs/deployment.md`.
- Honest findings recorded: `infra/terraform/` and `infra/k8s/` are stubs
  and are not used by Render/Railway; per-service Dockerfiles cannot build
  standalone because `veripay-common` is not on PyPI (the new deploy
  Dockerfile fixes this); `ml/models/` is gitignored so cloud builds serve
  the deterministic fallback unless the build trains models.
- NO live URL was produced: Render/Railway deployment requires the owner's
  account + API token (cannot be created here); the instant-tunnel path needs
  cloudflared installed by the user (not globally installed without consent).
  Configs parse-validated; tunnel script `bash -n` clean.

## Engineering boundaries

- Service persistence uses repository/provider protocols and deterministic
  in-memory adapters until the populated PostgreSQL schema is finalized.
  The model monitor uses a bounded in-memory observation window and pulls
  analyst labels over HTTP from the feedback loop.
- ML scoring, attestation, authentication, network, external context, card
  network, Iceberg, Kafka, and data-lake integrations remain explicit provider
  boundaries.
- No service stores, logs, or returns PAN, CVV, private keys, credentials,
  attestation blobs, or provider secrets.
- Shared `proto/`, migrations, and Avro schemas were not changed by these slices.

## CI compose live HTTP smoke test (2026-08-30)

- Added `scripts/compose-smoke.py` — a STRICT end-to-end HTTP walk (fails on
  any failure): /health on each service, then rule_engine -> supervised_model ->
  anomaly_model -> risk_fusion -> decision_engine -> investigation_agent with
  real payloads. Requires no trained models (scoring services use deterministic
  fallback) and no LLM key (investigation falls back to governed explainer).
- Added `compose-smoke` CI job: builds the 6 representative-chain images, `up`
  (no kafka/redis/postgres deps), runs the smoke script. Verified live locally:
  fraud_probability 0.8454, anomaly 0.5402, fusion 45, decision CHALLENGE.
- Local docker Desktop now available; built and ran the whole subset end-to-end.

## Compose healthchecks + depends_on gating (2026-08-30)

- Every backend service now has a `healthcheck` probing uvicorn `/health` via
  Python stdlib urllib (no curl in the slim image), plus
  `depends_on.*.condition: service_healthy` for postgres/redis/kafka so
  backend startup is gated on real readiness.
- postgres (`pg_isready`), redis (`redis-cli ping`), kafka
  (`kafka-topics.sh --list`) get healthchecks in their include files.
- FIXED: `kafka.yml` referenced `bitnami/kafka:3.8`, which no longer resolves
  on Docker Hub (bitnami migrated). Now `bitnamilegacy/kafka:3.8`.
- Verified live: postgres/redis/kafka/ingress/feature_store/audit_store all
  reach `healthy`; ingress only started after kafka was healthy; published
  `/health` returned 200. `docker compose config` (dev/services/combined) OK.

## Git and collaboration

Implementation is uncommitted on `feat/blueprint-alignment` until explicitly
requested. Branch protection requires pull requests for changes to `main`.

## Dockerfile standalone builds (2026-08-30)

- All 25 `services/<name>/Dockerfile`s now build standalone from the repo ROOT
  context: `COPY libs/veripay_common` + `pip install /app/libs/veripay_common`
  (source install, not PyPI), then `pip install -e .` (or `.[model]` /
  `.[llm]` extras) with the package dir copied in. Build:
  `docker build -f services/<name>/Dockerfile -t veripay-<name> .`
- `infra/compose/services.yml` switched each `build:` to
  `context: ../..` + `dockerfile: services/<name>/Dockerfile`.
- New CI `compose-build` job: `docker compose ... build ingress
  supervised_model investigation_agent` (one plain, one `[model]`, one
  `[llm]` variant) + image presence check.
- Verified locally without a docker daemon: compose `config` resolves all 25
  build blocks; a throwaway py3.12 venv replicated each Dockerfile's exact pip
  steps for all three variants (incl. xgboost 3.4.1 via `.[model]`).

## CI hadolint step (2026-08-30)

- Added `Hadolint Dockerfile lint` step (hadolint/hadolint-action@v3.1.0,
  failure-threshold: warning) to the `compose-build` CI job, gating every push.
- The built-image confirm step uses the compose project name from
  `docker compose ... config` + `docker image ls --format` (NOT `docker compose
  images`, which only lists running containers) to verify
  `<project>-<service>` images deterministically.
- All repo Dockerfiles pass hadolint with zero findings (verified locally via
  hadolint/hadolint Docker image). Real `docker compose build` of ingress +
  supervised_model + investigation_agent succeeded end-to-end locally
  (incl. xgboost 3.4.1 via `.[model]`).

## Verification status (feat/blueprint-alignment, 2026-08-29)

- Python: 111 tests passed, ruff check/format passed, git diff --check passed
- Web: tsc clean, ESLint passed, Vitest 1 passed, production build succeeds
- iOS SwiftPM tests: 3 passed
- Compose dependency/backend/combined config validation: passed
- Local mypy unavailable (.venv/bin/mypy not installed); CI installs it
- Android Gradle tests: not run locally (no Gradle wrapper); CI job covers it
- Android deployable app explicitly out of scope this session
- Web build pipeline now verified end-to-end: `tsc --noEmit`, ESLint, Vitest,
  and `npm run build` all pass on this branch (the glass-theme button constants
  and login-mark prop fixes are in place).
