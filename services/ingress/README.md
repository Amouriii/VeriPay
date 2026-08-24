# Ingress Service

**Implements:** PLAN §5,§6.1

ISO 8583 + REST/gRPC ingestion and dual-phase entry point.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
