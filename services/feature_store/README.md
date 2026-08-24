# Feature Store

**Implements:** PLAN §8,§9

Redis/RonDB online feature read/write API.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
