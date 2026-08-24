# Device Integrity & GPV

**Implements:** PLAN §14,§15

Attestation verification, challenge nonces, GPV signal intake.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
