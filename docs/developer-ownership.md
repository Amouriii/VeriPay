# Developer Work-Tree Allocation & Parallel Architecture

This document is the authoritative developer contribution plan, matching the
Contributions.md specification. Five engineers work concurrently with zero
work-tree contention using a contract-first architecture.

## Architecture overview

```
               +-------------------------------------------------------+
               |             DEV 1 (BE) + DEV 2 (FE) PAIR              |
               | Ingress Gateway, Web Apps, Portals & API Integration  |
               +---------------------------+---------------------------+
                                           |
    +--------------------------------------+--------------------------------------+
    |                                      |                                      |
    v                                      v                                      v
+-----------------------+      +-----------------------+      +-----------------------+
|        DEV 3          |      |        DEV 4          |      |        DEV 5          |
|  Inference LLM Agent  |      |  Data Preprocessing   |      |   Policy, Security,   |
|   & Explainability    |      |      & ML Models      |      |   Mobile & "The Rest" |
+-----------------------+      +-----------------------+      +-----------------------+
```

## Dev 1 (Backend & API Gateway) — Full-Stack Pair (BE)

**Primary repository:** `repo-app-backend`
**Scope:** Financial Ingress, Token Vault Integration, Web Hooks, Backend APIs.

| Service / dir | Responsibility |
|---|---|
| `services/ingress` | ISO 8583 parsing (0100/0110/0400), REST/gRPC ingestion |
| `services/token_vault` | PCI-DSS Token Vault (HashiCorp/VGS), VCN detokenization, dCVV validation |
| `services/banking_gateway` | Core banking authorization hooks, ISO 20022, settlement sync |
| `services/merchant_ingress` | Merchant Ingress APIs, VCN issuance, webhook push engine |
| `services/corporate_spend` | Per-merchant spend tracking, corporate VCN policy |
| `services/audit_store` | PostgreSQL audit trails, VCN registry, state |
| `services/auth_orchestration` | 3DS/biometric/WebAuthn step-up backend |

**Day-1 contracts:** OpenAPI specs for `/api/v1/transactions`, `/api/v1/disputes`,
`/api/v1/merchant/rules`.

## Dev 2 (Frontend Applications & Portals) — Full-Stack Pair (FE)

**Primary repository:** `repo-web-frontends`
**Scope:** Web apps, UIs, out-of-band auth interfaces.

| Service / dir | Responsibility |
|---|---|
| `web/` | Vite + React + TS + Tailwind frontend |
| `web/src/pages/Dashboard.tsx` | Fraud Operations Portal: investigation UI, risk scores, TreeSHAP |
| `web/src/pages/FiOpsConsole.tsx` | Institutional Bank Console: settlement, portfolio risk, disputes |
| `web/src/pages/BusinessTreasury.tsx` | Business & Merchant Portal: spend controls, VCN policy, disputes |
| `web/src/pages/Investigation.tsx` | LLM copilot interaction, review feedback workflows |
| `web/src/pages/TransactionDetail.tsx` | Real-time risk score display, SHAP reason codes |
| Consumer Web Ingress (in `web/`) | Browser telemetry, WebAuthn triggers, EMV 3DS 2.3 web challenge flows |

**Day-1 approach:** Uses MSW (Mock Service Worker) to build all React UI
components against frozen OpenAPI specs without waiting for live backend.

## Dev 3 (Inference LLM Agent & Explainability) — AI Specialist

**Primary repository:** `repo-llm-copilot`
**Scope:** Natural language intelligence, explainability, analyst assistance.

| Service / dir | Responsibility |
|---|---|
| `services/investigation_agent` | LLM Copilot Engine, async investigation endpoints |
| `ml/supervised/` (TreeSHAP) | Fast TreeSHAP determinism for XGBoost/LightGBM |

**Key contracts:**
- REST endpoint `/api/v1/investigate/{tx_id}` — accepts feature attribution
  arrays, returns structured markdown summaries.
- LLM Guardrails: zero auto-decision authority (cannot block accounts or alter rules).

## Dev 4 (Data Preprocessing, Streaming & ML) — ML / Data Engineer

**Primary repository:** `repo-data-ml`
**Scope:** Event streaming, feature engineering, ML models.

| Service / dir | Responsibility |
|---|---|
| `services/feature_store` | Redis Cluster / RonDB online feature store |
| `services/supervised_model` | XGBoost/LightGBM serving via gRPC |
| `services/anomaly_model` | Isolation Forest serving |
| `services/graph_engine` | Coordinated fraud network analysis |
| `streaming/jobs/*.py` | All 7 Flink jobs (velocity, token, behavioral, raw sink, settlement, merchant, dispute) |
| `ml/supervised/` | XGBoost training pipeline |
| `ml/anomaly/` | Isolation Forest training |
| `ml/graph/` | Graph feature extraction |
| `ml/fusion/` | Fusion weight tuning |
| `ml/issuer_risk/` | Portfolio-wide issuer risk models |
| `ml/fraud_ring/` | Cross-institutional fraud ring engines |
| `ml/merchant_risk/` | Merchant category risk profiling |
| `ml/b2b_credit/` | B2B supplier credit risk |

**Key contract:** gRPC `ModelScoringService` (see `proto/veripay/scoring/v1/scoring.proto`).
**Kafka topics:** `tx.ingress.raw`, `tx.features.enriched` (Avro schemas in `datasets/schemas/avro/`).

## Dev 5 (Policy, Security, Mobile & Core Engine) — Core Systems Engineer

**Primary repository:** `repo-policy-core`
**Scope:** Native mobile, GPV, rules, fusion, local infra.

| Service / dir | Responsibility |
|---|---|
| `services/rule_engine` | dCVV mismatch, merchant-lock, burner velocity, zero-trust |
| `services/risk_fusion` | Weighted fusion to 0-100 unified score |
| `services/decision_engine` | Cost-aware decision router (ALLOW/VERIFY/BLOCK/REVERSE) |
| `services/device_integrity` | GPV engine, H3 spatial indexing, challenge nonces |
| `services/compliance_engine` | PCI-DSS 4.0, PSD3/SCA, network zero-trust |
| `services/merchant_policy` | Custom velocity rules, MCC restrictions |
| `services/financial_context` | Cash-flow / behavioral baseline |
| `services/external_context` | Economic / seasonal / geographic normalization |
| `services/feedback_loop` | Analyst review labels to Iceberg, drift/retrain |
| `services/dispute_engine` | Chargeback/dispute lifecycle, regulatory reporting |
| `services/fi_ops_portal` | Institutional fraud ops console backend |
| `services/business_portal` | B2B treasury portal backend |
| `mobile/ios/` | Secure Enclave ECDSA P-256, App Attest, biometric step-up |
| `mobile/android/` | Android Keystore, Play Integrity, biometric step-up |
| `infra/compose/` | `docker-compose.dev.yml` local infra (Kafka, Redis, PG, WireMock) |

## Shared boundary (merge-coordination point)

All five developers coordinate changes at these narrow boundaries:

- `proto/` — wire contracts (Protobuf definitions)
- `libs/` — read-only shared code mirroring proto
- `datasets/migrations/` — shared SQL schema
- `datasets/schemas/avro/` — Kafka Avro schemas
- `docs/contracts/` — OpenAPI specs and contract-first execution plan

Everything else is owned by exactly one developer's work-tree.
