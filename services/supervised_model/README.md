# Supervised Fraud Model

**Implements:** PLAN §10,§20

XGBoost/LightGBM serving + TreeSHAP explainability.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
