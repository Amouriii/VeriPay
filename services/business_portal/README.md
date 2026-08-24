# Business Portal

**Implements:** Expansion §1 Dev5, §2

B2B treasury portal, merchant fraud manager, ERP sync connectors.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_business_portal.main:app --reload
```
