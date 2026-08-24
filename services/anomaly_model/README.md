# Behavioral Anomaly Model

**Implements:** PLAN §11

Isolation Forest serving, normalized 0-100 anomaly score.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
