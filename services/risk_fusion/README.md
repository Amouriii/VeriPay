# Risk Fusion Engine

**Implements:** PLAN §18

Weighted fusion -> unified 0-100 score, weight redistribution.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
