# Graph / Coordinated Fraud Engine

**Implements:** PLAN §12

Entity graph features and graph_risk_score.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
