# Compliance Engine

**Implements:** Expansion §1 Dev4, §2

PCI-DSS 4.0, PSD3/SCA triggers, network zero-trust constraints.

See  for which developer owns this service.

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_compliance_engine.main:app --reload
```
