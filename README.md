# VeriPay

Real-time payment fraud-detection platform. See `docs/architecture.md` and the
upstream `PLAN.md` for the authoritative design (sections 4–24).

## Repository map

```
VeriPay/
├─ proto/veripay/     gRPC + message contracts (shared boundary)
├─ libs/              shared code: veripay_common (py), veripay_ts (ts)
├─ services/          16 FastAPI/gRPC services, one per diagrammed component
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
