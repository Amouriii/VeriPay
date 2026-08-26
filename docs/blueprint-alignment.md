# Blueprint alignment

VeriPay keeps its continuous `0–100` model score for compatibility and derives the
blueprint's authoritative operational tiers at the policy boundary:

- 0–5: silent pass
- 6–25: push approve/deny, 30-second decline timeout
- 26–50: push plus hardware biometric, decline and temporary lock on timeout
- 51–100: exact amount/currency, biometric, confirmation swipe, and analyst escalation

Card and ISO 8583 rails use the fast path; wires and instant-transfer rails use the
secondary path. Local-LLM explanations are advisory only and are never authorization
decisions. Inputs cross a deterministic PII redaction/tokenization boundary, include
at most a 30-day baseline and supplied macro context, and produce structured reason
codes.

Verification tokens are signed, transaction/device/session bound, and constrained to
10–30 seconds. Production deployments must replace the local HMAC adapters with HSM/KMS
and approved AEAD providers. The optional Helm inference workload supports a local
vLLM OpenAI-compatible server on NVIDIA GPU nodes and can be autoscaled.

Audit integrations should persist immutable feature snapshots, policy outcomes, and
LLM evidence with a five-year sliding retention policy. The in-memory implementation
is a contract/test adapter; production storage must enforce retention and WORM semantics.
