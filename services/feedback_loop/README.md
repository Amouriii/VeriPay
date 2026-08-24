# Human Feedback Loop

**Implements:** PLAN §21

Analyst review labels -> Iceberg, drift/retrain triggers.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
