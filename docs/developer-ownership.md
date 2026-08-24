# Developer Work-Tree Ownership Map

This document maps the expanded Banking/FI and Business/Merchant domains to
five parallel developer work-trees. Each developer owns a disjoint set of
directories and merges cleanly except at the shared `proto/` + `libs/` boundary.

## Ownership matrix

### Developer 1 — Gateway & Protocols
Owns all network-facing ingress and protocol translation.

| Service / dir | Domain | Responsibility |
|---|---|---|
| `services/ingress` | Core | ISO 8583 + REST/gRPC ingestion, dual-phase entry |
| `services/banking_gateway` | FI | ISO 20022 XML, Visa/MC host messaging, core banking gRPC hooks |
| `services/merchant_ingress` | Business | Merchant Ingress APIs, VCN issuance endpoints, webhook push engine |

### Developer 2 — Data Pipeline & Ledger Streaming
Owns all Kafka/Flink streaming and ledger synchronization.

| Service / dir | Domain | Responsibility |
|---|---|---|
| `services/audit_store` | Core | PostgreSQL audit trails, VCN registry |
| `services/feature_store` | Core | Redis/RonDB online feature read/write |
| `streaming/jobs/velocity_aggregations.py` | Core | tx_count_5m/1h/24h, spend windows |
| `streaming/jobs/token_velocity.py` | Core | VCN generation, failed dCVV, revoked counts |
| `streaming/jobs/behavioral_features.py` | Core | z-score, 7/30-day limits |
| `streaming/jobs/raw_event_sink.py` | Core | Kafka → PG/Iceberg audit sink |
| `streaming/jobs/settlement_sync.py` | FI | Bank settlement streams, clearing files, ACH/FedNow ledger sync |
| `streaming/jobs/merchant_aggregations.py` | Business | Per-merchant velocity, merchant aggregations, corporate spend tracking |

### Developer 3 — Risk AI & Institutional Models
Owns all ML models, training pipelines, and risk scoring.

| Service / dir | Domain | Responsibility |
|---|---|---|
| `services/supervised_model` | Core | XGBoost/LightGBM serving + TreeSHAP |
| `services/anomaly_model` | Core | Isolation Forest, normalized 0-100 score |
| `services/graph_engine` | Core | Entity graph features, graph_risk_score |
| `services/risk_fusion` | Core | Weighted fusion → unified 0-100 score |
| `ml/supervised/` | Core | XGBoost training pipeline |
| `ml/anomaly/` | Core | Isolation Forest training |
| `ml/graph/` | Core | Graph feature extraction |
| `ml/fusion/` | Core | Fusion weight tuning |
| `ml/issuer_risk/` | FI | Portfolio-wide issuer risk models |
| `ml/fraud_ring/` | FI | Cross-institutional fraud ring engines |
| `ml/merchant_risk/` | Business | Merchant category risk profiling, collusion models |
| `ml/b2b_credit/` | Business | B2B supplier credit risk algorithms |

### Developer 4 — Policy, Compliance & Business Rules
Owns all deterministic rules, compliance, and customizable business policy.

| Service / dir | Domain | Responsibility |
|---|---|---|
| `services/rule_engine` | Core | Hard rules: dCVV mismatch, merchant-lock, burner velocity |
| `services/financial_context` | Core | Cash-flow / behavioral baseline |
| `services/external_context` | Core | Economic / seasonal / geographic normalization |
| `services/compliance_engine` | FI | PCI-DSS 4.0, PSD3/SCA triggers, network zero-trust constraints |
| `services/merchant_policy` | Business | Custom velocity rules, MCC restrictions, dynamic merchant-lock |

### Developer 5 — Operations & Analytics Portals
Owns all operator-facing services, portals, and feedback loops.

| Service / dir | Domain | Responsibility |
|---|---|---|
| `services/decision_engine` | Core | Cost-aware router → DecisionAction |
| `services/investigation_agent` | Core | LLM copilot + explainability |
| `services/auth_orchestration` | Core | 3DS/biometric/WebAuthn step-up |
| `services/feedback_loop` | Core | Analyst review labels → Iceberg, drift/retrain |
| `services/dispute_engine` | Both | Chargeback/dispute lifecycle, regulatory reporting |
| `services/fi_ops_portal` | FI | Institutional fraud ops console, regulatory audit dashboard |
| `services/business_portal` | Business | B2B treasury portal, merchant fraud manager, ERP sync |
| `web/` | Both | Analyst dashboard + new FI/Business portal pages |

## Shared boundary (merge-coordination point)
- `proto/` — wire contracts (all developers coordinate here)
- `libs/` — read-only shared code mirroring proto
- `datasets/migrations/` — shared SQL schema (coordinate changes)

Everything else is owned by exactly one developer's work-tree.
