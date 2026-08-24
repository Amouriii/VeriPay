# Contract-First Parallel Execution Strategy

All five work-trees operate against strict, pre-defined interface contracts
frozen on Day 1. This eliminates blocking dependencies during development.

## Day-1 contract definitions

| Contract type | Location | Owner |
|---|---|---|
| Protobuf definitions | `proto/veripay/*/v1/*.proto` | All (shared boundary) |
| OpenAPI specs | `docs/contracts/openapi.yaml` | Dev 1 + Dev 2 |
| Kafka Avro schemas | `datasets/schemas/avro/*.avsc` | Dev 4 |

## Mocking matrix

### Dev 1 + Dev 2 (Full-Stack Pair)
- Frozen OpenAPI endpoints: `/api/v1/transactions`, `/api/v1/disputes`,
  `/api/v1/merchant/rules`, `/api/v1/investigate/{tx_id}`.
- Dev 2 uses MSW (`web/src/mocks/handlers.ts`) to build React UI against mock
  responses without waiting for live backend routes.
- Dev 1 implements backend persistence and ingress handlers against mock Kafka
  event outputs on `tx.ingress.raw`.

### Dev 4 (ML & Pipeline)
- Exposes gRPC `ModelScoringService` (`proto/veripay/scoring/v1/scoring.proto`).
- Publishes feature schema for Redis key structures
  (`user:{id}:velocity:5m`).
- Generates mock streaming events on `tx.ingress.raw` so Dev 1 and Dev 5 can
  test downstream triggers.

### Dev 3 (LLM Copilot)
- Exposes REST endpoint `/api/v1/investigate/{tx_id}` accepting feature
  attribution arrays, returning structured markdown summaries.
- Dev 2 integrates the summary box into the Fraud Ops UI using mock response
  payloads while Dev 3 tunes prompt guardrails and TreeSHAP calculations.

### Dev 5 (Policy & Core Engine)
- Consumes mock ML scores from Dev 4's mock gRPC server.
- Consumes token statuses from Dev 1's mock token service.
- Implements Risk Fusion algorithm and H3 spatial matching independently,
  returning decision routes (ALLOW, BLOCK, VERIFY).

## Local integration infrastructure

`docker-compose.dev.yml` (Dev 5 owned, `infra/compose/`):
- Local Kafka cluster (Redpanda or Apache Kafka)
- Local Redis Cluster for online feature store testing
- PostgreSQL container pre-seeded with schema migrations
- WireMock container hosting contract stubs (`infra/wiremock/mappings/`)

## CI guardrails
- GitHub Actions checks Protobuf breaking changes on every PR (`buf breaking`).
- OpenAPI spec breaking changes checked via `oasdiff` (to be added).
- All five jobs must pass before merge to `main`.
