# Assumptions

## Persistence

- The database is being populated independently.
- Backend services use repository protocols and in-memory adapters until the
  final PostgreSQL schema and connection conventions are available.
- The in-memory adapters are development/test implementations, not production
  persistence.

## Risk evaluation

- The ML decision engine and policy/risk services are still being designed.
- Ingress therefore uses a deterministic baseline score only as a temporary
  integration placeholder.
- Downstream ML, policy, fusion, and decision services should replace or enrich
  this baseline through explicit service contracts.

## Token security

- PAN and dCVV secrets belong in an external PCI-compliant vault/provider.
- The token vault service stores and returns metadata only.
- The current dCVV endpoint models a provider comparison boundary using an
  expected value for deterministic tests; production should receive a secure
  provider result rather than accept raw expected secrets over the public API.
- Token IDs are treated as non-secret references.

## API contracts

- The frozen OpenAPI transaction contract is the source of truth for ingress
  request and response shapes.
- Existing service scaffolds use FastAPI, Pydantic, Python 3.11+, and injectable
  service boundaries.
- Existing shared enums in `libs/veripay_common` are used instead of creating
  duplicate enum definitions.

## CI

- GitHub Actions should run focused tests for each completed backend service.
- CI does not require Kafka, Redis, PostgreSQL, or external vault providers for
  these unit/API tests.
- Repository-wide CI remains authoritative for lint, type checking, protocol
  checks, and the complete test suite.

## Git and collaboration

- Changes remain uncommitted until explicitly requested.
- Shared boundaries such as `proto/`, `libs/`, migrations, and Avro schemas are
  not changed by the initial Developer 1 implementation.
- Before adding PostgreSQL or external integrations, confirm the database
  schema, credentials strategy, idempotency requirements, and service-to-service
  authentication model.
