# VeriPay Architecture

See `PLAN.md` (sections 4–24) for the authoritative design. This document maps
each diagrammed box to its scaffold location and PLAN section.

| Component | Location | PLAN |
|---|---|---|
| Ingress (ISO 8583 / REST / gRPC) | `services/ingress` | §5, §6.1 |
| Token Vault & dCVV Validation | `services/token_vault` | §6.1, §22 |
| Event Streaming (Kafka) | `infra/compose/kafka.yml` + `streaming/` | §9 |
| Real-time Streaming (Flink) | `streaming/jobs/` | §9 |
| Raw Event / Audit (Postgres) | `services/audit_store` | §22 |
| Online Feature Store (Redis) | `services/feature_store` | §8, §9 |
| Supervised Model (XGBoost) | `services/supervised_model` + `ml/supervised` | §10 |
| Anomaly (Isolation Forest) | `services/anomaly_model` + `ml/anomaly` | §11 |
| Graph Risk Engine | `services/graph_engine` + `ml/graph` | §12 |
| Rule / Security Engine | `services/rule_engine` | §13 |
| Financial Context | `services/financial_context` | §17 |
| External Context | `services/external_context` | §17 |
| Device Integrity + GPV | `services/device_integrity` + `mobile/` | §14, §15 |
| Risk Fusion | `services/risk_fusion` + `ml/fusion` | §18 |
| Cost-Aware Decision Router | `services/decision_engine` | §19 |
| LLM Investigation / Explainability | `services/investigation_agent` | §20 |
| Auth Orchestration (3DS/Biometric) | `services/auth_orchestration` | §16 |
| Human Feedback Loop | `services/feedback_loop` | §21 |
| Analyst Dashboard | `web/` | §20 |
| Contracts (gRPC) | `proto/veripay/` | all |
| Shared enums/constants | `libs/veripay_common`, `libs/veripay_ts` | all |

## Expansion: Banking/FI + Business/Merchant

| Component | Location | Expansion § |
|---|---|---|
| Banking Gateway (ISO 20022) | `services/banking_gateway` | §1 Dev1, §2 |
| Merchant Ingress (VCN, webhooks) | `services/merchant_ingress` | §1 Dev1, §2 |
| Corporate Spend Service | `services/corporate_spend` | §1 Dev1, §2 |
| Settlement Sync | `streaming/jobs/settlement_sync.py` | §1 Dev2 |
| Merchant Aggregations | `streaming/jobs/merchant_aggregations.py` | §1 Dev2 |
| Issuer Risk Models | `ml/issuer_risk/` | §1 Dev3 |
| Fraud Ring Engine | `ml/fraud_ring/` | §1 Dev3 |
| Merchant Risk Models | `ml/merchant_risk/` | §1 Dev3 |
| B2B Credit Risk | `ml/b2b_credit/` | §1 Dev3 |
| Merchant Policy Engine | `services/merchant_policy` | §1 Dev4, §2 |
| Compliance Engine (PCI/PSD3) | `services/compliance_engine` | §1 Dev4, §2 |
| Dispute Engine | `services/dispute_engine` | §1 Dev5, §3 |
| Dispute Sync (→ Iceberg) | `streaming/jobs/dispute_sync.py` | §1 Dev5, §3 |
| FI Ops Portal | `services/fi_ops_portal` + `web/src/pages/FiOpsConsole.tsx` | §1 Dev5, §2 |
| Business Portal | `services/business_portal` + `web/src/pages/BusinessTreasury.tsx` | §1 Dev5, §2 |

See `docs/developer-ownership.md` for the full 5-developer work-tree map.

## Shared boundary (merge-coordination point)
- `proto/` — wire contracts
- `libs/` — read-only shared code mirroring proto

Everything else is owned by exactly one work-tree.
