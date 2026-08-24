# Rule Engine

**Implements:** PLAN §13

Deterministic hard rules: dCVV mismatch, merchant-lock, burner velocity, impossible travel, signal contradiction.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
