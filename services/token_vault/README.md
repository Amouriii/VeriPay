# Token Vault & dCVV Engine

**Implements:** PLAN §6.1,§22

VCN->PAN conversion, dCVV validation, merchant-lock enforcement.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
