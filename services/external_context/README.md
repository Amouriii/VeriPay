# External Context

**Implements:** PLAN §17

Economic / seasonal / geographic normalization.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
