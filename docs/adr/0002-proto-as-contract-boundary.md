# ADR-0002: proto/ as the contract boundary

## Status
Accepted (2026-08-24)

## Context
Services need to communicate via gRPC. Contract drift between services causes
silent failures during parallel development.

## Decision
All inter-service interfaces are defined in `proto/veripay/*.proto` under buf
management. Services import generated stubs; they never hand-write message types.
`libs/veripay_common` mirrors the wire enums for ergonomic Python use but defers
to proto as the source of truth.

## Consequences
- Contract changes land on `main` first and are rebased by work-trees.
- `make proto` regenerates Python + TS stubs from a single source.
- Breaking changes are caught by `buf breaking` against the main branch.
