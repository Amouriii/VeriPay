# LLM Investigation Agent

**Implements:** PLAN §20

LLM copilot + explainability with guardrails.

See `docs/architecture.md` for how this service fits the end-to-end pipeline.

## Develop
```bash
pip install -e .
pytest
uvicorn app.main:app --reload
```
