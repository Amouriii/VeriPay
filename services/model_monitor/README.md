# Model Monitor

**Implements:** PLAN §10, §21

Drift detection and gated automated retraining wired to the model registry:

- Ingests scored transactions (observations) with optional analyst labels.
- Detects feature drift (PSI) against the reference profile of the latest
  registered model.
- Retrains through the training CLI on the base dataset + labeled feedback,
  and promotes the new version to `latest` only when its held-out metrics
  clear a gate versus the current champion.

See `docs/architecture.md` and `docs/evaluation.md` for how this fits the
feedback loop and retraining lifecycle.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
