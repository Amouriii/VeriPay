# Merchant Policy Engine

**Implements:** Expansion §1 Dev4, §2

Custom velocity rules, MCC restrictions, dynamic merchant-lock enforcement.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_merchant_policy.main:app --reload
```
