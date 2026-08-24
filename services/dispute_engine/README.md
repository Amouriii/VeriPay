# Dispute Engine

**Implements:** Expansion §1 Dev5, §3

Chargeback/dispute lifecycle, async sync to Iceberg for retraining.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_dispute_engine.main:app --reload
```
