# Cost-Aware Decision Engine

**Implements:** PLAN §19

Expected-value router -> DecisionAction.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
