# Authentication Orchestration

**Implements:** PLAN §16

3DS/biometric/WebAuthn step-up, PASS/FAIL/EXPIRE.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
