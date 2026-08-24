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

## Quickstart
```bash
make install      # python + js deps
make up           # docker compose (Kafka, Redis, Postgres, all services)
make test         # pytest + vitest
make lint         # ruff + mypy + eslint
```

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
