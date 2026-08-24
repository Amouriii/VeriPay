# ADR-0001: Monorepo layout

## Status
Accepted (2026-08-24)

## Context
VeriPay is a multi-component fraud platform developed in parallel work-trees.
We need a structure where work-trees own disjoint directories and merge cleanly.

## Decision
Single monorepo. Each boxed component in the architecture diagram is one
self-contained directory under `services/` (Python/FastAPI), `streaming/`
(PyFlink), `web/` (Vite+React), `ml/`, or `mobile/`. Shared code lives in
`libs/`; shared contracts in `proto/`.

## Consequences
- A work-tree owns exactly one service directory and edits it freely.
- The only merge-coordination surface is `proto/` and `libs/` (narrow by design).
- Service builds are independent (each has its own Dockerfile + pyproject.toml).
