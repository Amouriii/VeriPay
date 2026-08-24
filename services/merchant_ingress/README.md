# Merchant Ingress

**Implements:** Expansion §1 Dev1, §2

Merchant Ingress APIs, VCN issuance endpoints, webhook push engine.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_merchant_ingress.main:app --reload
```
