# Audit Store

**Implements:** PLAN §22

PostgreSQL persistence: transactions, VCN registry, device registry, audit trail.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
