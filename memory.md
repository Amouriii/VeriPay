# Project Memory

## Project

VeriPay is a real-time payment fraud-detection platform organized as a Python
service monorepo with shared contracts in `proto/`, shared Python types in
`libs/veripay_common`, backend services in `services/`, and a React frontend in
`web/`.

## Ownership

Developer 1 owns the backend/API gateway scope:

- Ingress
- Token vault
- Banking gateway
- Merchant ingress
- Corporate spend
- Audit store
- Auth orchestration

Developer 2 owns frontend applications and portals. Developer 3 owns the LLM
investigation agent and explainability. Developer 4 owns streaming, feature
engineering, and ML models. Developer 5 owns policy, security, mobile, and core
risk engines.

## Completed local work

The current uncommitted work implements:

- `services/ingress`: transaction list, transaction submission, risk lookup,
  injectable repository, deterministic baseline authorization response
- `services/token_vault`: PCI-safe token metadata, token creation/listing,
  consumption lifecycle, expiration/exhaustion handling, dCVV validation
- `services/audit_store`: append-only audit events, duplicate event protection,
  transaction state save/load, injectable repository
- Focused tests for all three services
- Dedicated CI jobs in `.github/workflows/ci.yml` for ingress, token vault, and
  audit store

## Verification

The local virtual environment verified:

- 16 combined service tests passing
- Ruff checks passing
- Ruff format checks passing

There is an existing FastAPI/httpx deprecation warning from the installed test
client dependency. Mypy was not run locally because it is not installed in the
local `.venv`; the existing GitHub Actions lint job installs it.

## Git state

The implementation is intentionally uncommitted. The repository was clean at
the beginning of this work aside from changes made during this session.
