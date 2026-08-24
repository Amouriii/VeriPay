# Banking Gateway

**Implements:** Expansion §1 Dev1, §2

ISO 20022, Visa/MC host messaging, core banking gRPC hooks, settlement sync.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_banking_gateway.main:app --reload
```
