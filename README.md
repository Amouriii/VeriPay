# VeriPay

Real-time payment fraud-detection platform. See `docs/architecture.md` and the
upstream `PLAN.md` for the authoritative design (sections 4–24).

## Repository map

```
VeriPay/
├─ proto/veripay/     gRPC + message contracts (shared boundary)
├─ libs/              shared code: veripay_common (py), veripay_ts (ts)
├─ services/          26 FastAPI/gRPC services, one per diagrammed component
├─ streaming/         Apache Flink (PyFlink) feature aggregation jobs
├─ web/               Vite + React + TS analyst dashboard
├─ ml/                XGBoost / Isolation Forest / graph / fusion pipelines
├─ mobile/            iOS (Secure Enclave) & Android (Keystore) SDK stubs
├─ infra/             docker-compose, k8s/Helm, terraform
├─ datasets/          JSON schemas, fixtures, SQL migrations
└─ docs/              ADRs, architecture, contributing, runbooks
```

## Databases

The platform uses five logical PostgreSQL databases:

| Database | Owns |
|---|---|
| `veripay_customer_db` | Users, customers, accounts, devices, funding cards, VCNs, transactions, security events |
| `veripay_bank_db` | Bank users, fraud and risk statistics, disputes, audit logs, settlement, policies, and model versions |
| `veripay_fraud_ops_db` | Fraud transactions, risk assessments, risk factors, fraud alerts, investigations, and analyst actions |
| `veripay_merchant_db` | Merchants, merchant users, merchant transactions, rules, limits, and disputes |
| `veripay_mobile_db` | Mobile users, registered devices, device security, verification requests and attempts, push tokens, and mobile audit logs |

Fraud Operations has its own database because it has a separate analyst-facing
workload and lifecycle. Relationships between databases use stable IDs and service/API
contracts rather than PostgreSQL foreign keys, since PostgreSQL cannot enforce
foreign keys across databases. The migrations are in
`datasets/migrations/{customer,bank,fraud_ops,merchant,mobile}`.

## Tech stack

- **Backend:** Python 3.12, FastAPI, gRPC (protobuf/buf), pydantic v2
- **Data/streaming:** Apache Kafka, PyFlink, Redis, PostgreSQL 16 (five logical databases)
- **ML:** XGBoost, scikit-learn (Isolation Forest), TreeSHAP-style attribution, a governed local-LLM explanation boundary
- **Frontend:** Vite + React 18 + TypeScript + Tailwind
- **Mobile:** Swift (iOS Secure Enclave/App Attest) and Kotlin (Android Keystore/Play Integrity) SDK contracts
- **Infra:** Docker Compose (local), Terraform + Kubernetes/Helm (cloud-ready), GitHub Actions CI/CD

## Prerequisites

- **Docker** with Docker Compose v2 (for the full local stack)
- **Python 3.11+** (3.12 recommended) and `pip`
- **Node.js 20+** and npm
- **GNU Make** (Windows: use Git Bash or WSL; `scripts/migrate-local.ps1` is provided for PowerShell)
- **Buf** (only if regenerating gRPC code: `buf generate proto`)

## Environment variables

All services read configuration from environment variables with safe local
defaults. Copy a template or export values explicitly:

| Variable | Default | Used by |
|---|---|---|---|
| `HTTP_PORT` | `8000` (per service) | every FastAPI service |
| `GRPC_PORT` | `50051` | services with gRPC entry points |
| `LOG_LEVEL` | `INFO` | every service |
| `POSTGRES_DSN` | `postgresql://veripay:veripay@localhost:5432/veripay_<db>` | persistence services |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | streaming producers/consumers |
| `REDIS_URL` | `redis://localhost:6379` | feature store |
| `MODEL_PATH` | `<repo>/ml/models/<model>/latest/model.joblib` | ML serving services |
| `LLM_PROVIDER` | `deterministic` | investigation agent — `deterministic` or `openai_compatible` (local vLLM) |
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS` | vLLM defaults (`http://localhost:8000/v1`, `EMPTY`, …) | investigation agent (vLLM provider) |
| `VITE_API_BASE` | `http://localhost:8000` | web dashboard (`web/.env.example`) |
| `VITE_ANALYST_API_BASE` | *(unset → MSW mocks)* | analyst console — set to the `analyst_api` service (e.g. `http://localhost:8026`) to serve it live |

`.env.example` files exist per service (`services/*/.env.example`) and for the
web app (`web/.env.example`). Never commit real secrets; `.env` is gitignored.

## Setup (step by step)

1. **Install dependencies**
   ```bash
   make install
   ```
   This installs `libs/veripay_common`, every service under `services/`, the
   ML package (`ml/`), and the web app's npm dependencies.

2. **Start the local stack** (Kafka, Redis, PostgreSQL, all services)
   ```bash
   make up
   ```
   Compose migrates the five `veripay_*_db` databases automatically via the
   `migrate` service (SQL lives in `datasets/migrations/`).

3. **(Optional) Train the ML models**
   ```bash
   pip install -e "ml[training]"
   python ml/datasets/generate_synthetic.py
   python ml/supervised/train.py
   python ml/anomaly/train.py
   ```
   This generates the labeled synthetic dataset, trains XGBoost + Isolation
   Forest, evaluates them, and registers versions in `ml/models/registry.json`.

4. **Run the web dashboard**
   ```bash
   cd web && npm run dev
   ```
   Open the printed URL (default `http://localhost:5173`). The dashboard uses
   MSW mocks against the frozen OpenAPI contracts, so it is fully navigable
   without a running backend.

   From the bank console sidebar, “Analyst Console” opens the fraud-analysis
   workspace (Alert Queue, Transaction Detail with evidence & feature/timeline
   tabs, Customer Profile, Feedback Panel, System Performance, and Model
   Info/Retrain), served by the analyst API (`/score`, `/explain`,
   `/customer/{cc_num}/profile`, `/feedback`, `/feedback/stats`, `/retrain`,
   `/health`).

5. **Run tests and lint**
   ```bash
   make test    # pytest + vitest
   make lint    # ruff + mypy + eslint
   ```

See `docs/demo.md` for a guided end-to-end demonstration and
`docs/deployment.md` for going live (Render/Railway configs in
`infra/deploy/`).

## Quickstart
```bash
make install      # python + js deps
make up           # docker compose (Kafka, Redis, Postgres, all services)
make test         # pytest + vitest
make lint         # ruff + mypy + eslint
```

The local PostgreSQL server listens on `localhost:5432`. Compose creates and
migrates `veripay_customer_db`, `veripay_bank_db`, `veripay_fraud_ops_db`, `veripay_merchant_db`, and `veripay_mobile_db`; service
connections should select the appropriate database in `POSTGRES_DSN`.

For an existing local PostgreSQL installation, run the domain migrations with
PowerShell. The script defaults to the `veripay_*_db` names:

```powershell
.\scripts\migrate-local.ps1
```

If your databases use the Compose names instead, pass them explicitly:

```powershell
.\scripts\migrate-local.ps1 `
	-CustomerDatabase customer_db `
	-BankDatabase bank_db `
	-FraudOperationsDatabase fraud_ops_db `
	-MerchantDatabase merchant_db `
	-MobileDatabase mobile_db
```

The script invokes `psql -f` once per database. It does not run the legacy
combined files `datasets/migrations/001_init.sql` or
`datasets/migrations/002_banking_business.sql`.

## Parallel development
Each work-tree owns **one** directory (a service, `streaming/`, `web/`, etc.).
The only shared/coordination surface is `proto/` and `libs/` — contract changes
land on `main` first. See `docs/contributing.md`.

## Services
| Service | Port | PLAN |
|---|---|---|
| ingress | 8001 | §5, §6.1 |
| token_vault | 8002 | §6.1, §22 |
| audit_store | 8003 | §22 |
| feature_store | 8004 | §8, §9 |
| rule_engine | 8005 | §13 |
| supervised_model | 8006 | §10 |
| anomaly_model | 8007 | §11 |
| graph_engine | 8008 | §12 |
| financial_context | 8009 | §17 |
| external_context | 8010 | §17 |
| device_integrity | 8011 | §14, §15 |
| risk_fusion | 8012 | §18 |
| decision_engine | 8013 | §19 |
| investigation_agent | 8014 | §20 |
| auth_orchestration | 8015 | §16 |
| feedback_loop | 8016 | §21 |
| **Expansion — Banking/FI + Business** | | |
| banking_gateway | 8017 | Expansion §1 Dev1 |
| merchant_ingress | 8018 | Expansion §1 Dev1 |
| merchant_policy | 8019 | Expansion §1 Dev4 |
| dispute_engine | 8020 | Expansion §1 Dev5 |
| compliance_engine | 8021 | Expansion §1 Dev4 |
| fi_ops_portal | 8022 | Expansion §1 Dev5 |
| business_portal | 8023 | Expansion §1 Dev5 |
| corporate_spend | 8024 | Expansion §1 Dev1 |
| model_monitor | 8025 | §21 (drift + automated retraining) |
| analyst_api | 8026 | Analyst console: /score, /explain, /customer profile, /feedback, /feedback/stats, /retrain (§20) |
| seed_analyst | — | One-shot: seeds the analyst console alert queue via `analyst_api` (`docker compose run --rm seed_analyst` to re-seed) |
