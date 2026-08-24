# Corporate Spend Service

**Implements:** Expansion §1 Dev1, §2

Per-merchant spend tracking, corporate VCN policy enforcement.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_corporate_spend.main:app --reload
```
