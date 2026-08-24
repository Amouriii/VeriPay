# Contributing to VeriPay

## Parallel work-tree workflow
1. `git checkout main && git pull`
2. `git checkout -b feat/<service>-<topic>` (e.g. `feat/ingress-iso8583-parser`)
3. Implement only within your assigned directory (see ownership map in
   `docs/architecture.md`).
4. If you must change a contract, edit `proto/` or `libs/` and open a PR to
   `main` **first**; other work-trees rebase onto it.
5. `make lint && make test` before pushing.
6. Conventional commits enforced via pre-commit (`feat:`, `fix:`, `chore:`...).

## CI
GitHub Actions (`.github/workflows/ci.yml`) runs on every branch and PR:
- **buf** — `buf lint` + `buf breaking` against `main` (catches contract drift early).
- **lint** — `ruff check`, `ruff format --check`, `mypy`, and `eslint`.
- **test-python** — `pytest` across all services + libs.
- **test-web** — `vitest` for the analyst dashboard.

## Adding a new service
Copy `services/<existing>` as a template, update `pyproject.toml` name and
description, add the service to `infra/compose/services.yml`, and add a row to
`docs/architecture.md`.
