# Live Demo / Deployment

This document is the reliable demonstration path for evaluation, plus the
prepared deployment path for going live.

## Local demo (evaluation run-through, ~15 minutes)

The full stack runs locally with Docker Compose; the ML pipeline trains and
serves real models; the dashboard is navigable against MSW mocks. Nothing in
this flow touches external services, so it is fully offline and repeatable.

### 0. Prerequisites

Docker + Compose v2, Python 3.11+, Node 20+ (see `README.md` → Prerequisites).

### 1. Install and start the stack

```bash
make install
make up
```

`make up` brings up Kafka, Redis, PostgreSQL (5 databases), and every service,
then runs the `migrate` service which applies
`datasets/migrations/{customer,bank,fraud_ops,merchant,mobile}/001_*.sql`.

Check readiness:

```bash
curl -s localhost:8001/health     # ingress
curl -s localhost:8013/health     # decision engine
```

### 2. Train and register the ML models

```bash
pip install -e "ml[training]"
python -m ml.datasets.generate_synthetic          # -> datasets/synthetic/transactions_labeled.csv
python ml/supervised/train.py                     # XGBoost: train, evaluate, register
python ml/anomaly/train.py                        # Isolation Forest: train, evaluate, register
```

Expected output: metrics written to `ml/models/registry.json` and reported in
`docs/evaluation.md` (AUC, precision/recall at threshold).

### 3. Score a transaction with the supervised model

Start the model-serving service (it loads the artifact trained in step 2).
The compose stack already runs it; to run it standalone:

```bash
pip install -e "services/supervised_model[model]"
HTTP_PORT=8006 veripay-supervised_model
```

Score a high-risk synthetic transaction:

```bash
curl -s -X POST localhost:8006/api/v1/score \
  -H 'Content-Type: application/json' \
  -d '{
    "transaction_id": "tx_9001",
    "features": {
      "amount_log": 11.5, "mcc_risk": 0.9, "velocity_5m": 14,
      "device_trust": 0, "network_trust": 0, "impossible_travel": 1,
      "new_device": 1, "hour_of_day": 3, "weekend": 1, "distance_km": 1200
    }
  }'
```

Compare with a low-risk transaction (small amount, trusted device, daytime).
The response includes `fraud_probability`, `risk_score` (0–100), and the model
name/version.

### 4. Authorize a transaction end-to-end (rules → fusion → decision)

```bash
curl -s -X POST localhost:8001/api/v1/transactions \
  -H 'Content-Type: application/json' \
  -d '{
    "transaction_id": "tx_demo_1",
    "user_id": "u_100",
    "amount_minor": 4999,
    "currency": "USD",
    "merchant_id": "m_amazon",
    "channel": "CARD_NOT_PRESENT",
    "payment_rail": "CARD"
  }'
```

Then run the cost-aware decision on a fused score:

```bash
curl -s -X POST localhost:8013/api/v1/decision/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"transaction_id": "tx_demo_1", "risk_score": 42, "payment_rail": "CARD"}'
```

The response shows the chosen action, reason code, expected cost, tier
friction/workflow, and explanation mode.

### 5. Explain a transaction with the LLM investigation agent

```bash
curl -s -X POST localhost:8014/api/v1/investigate \
  -H 'Content-Type: application/json' \
  -d '{
    "transaction_id": "tx_demo_1",
    "transaction": {"amount_minor": 4999, "merchant_id": "m_amazon"},
    "transaction_history": [],
    "risk_score": 42,
    "macro_context": {"country": "US"}
  }'
```

The response is a structured explanation with regulatory reason codes
(guarded by deterministic PII redaction).

### 6. Web dashboard

```bash
cd web && npm run dev
```

Open `http://localhost:5173`. Navigable flows (MSW mocks against frozen
OpenAPI contracts):

- **Fraud Ops console** — Dashboard, transaction detail with risk score and
  reason codes, Investigation (LLM copilot), Feedback.
- **Bank / FI console** — settlement, portfolio risk, disputes.
- **Business Treasury** — merchant policy CRUD, spend controls, VCN policy,
  disputes.
- **Customer flows** — personal & business demo verification flows
  (push approve/deny, biometric step-up).

### 7. Verification story

Show: trained-model metrics → live model score on a synthetic transaction →
rule finding → fused 0–100 score → cost-aware decision → governed LLM
explanation → analyst dashboard. Then run:

```bash
make test && make lint
```

### Model monitoring & automated retraining

The learning loop is demonstrable with the model monitor (port 8025):

1. Feed scored transactions (optionally drifted features) as observations,
   and analyst labels via `/api/v1/monitor/feedback` or the feedback loop.
2. `GET /api/v1/monitor/drift` — per-feature PSI vs the latest model's
   reference profile; verdict `DRIFT` when any feature PSI ≥ 0.25.
3. `POST /api/v1/monitor/retrain` — retrains on the base dataset + labeled
   feedback (real `ml/supervised/train.py` run) and promotes the new version
   to `latest` only if it clears the champion within tolerance.

Verified end-to-end: 40 drifted observations → `DRIFT` (max PSI 12.8) → a
retrain scoring 0.898 vs the 0.927 champion was correctly **not** promoted.

### (Optional) Swap in a real local LLM (vLLM) for the investigation agent

The investigation agent defaults to a deterministic explainer. To use a real
local LLM, run an OpenAI-compatible server (e.g., vLLM) and point the service
at it:

```bash
pip install -e "services/investigation_agent[llm]"
LLM_PROVIDER=openai_compatible \
LLM_BASE_URL=http://localhost:8000/v1 \
LLM_MODEL=your-model \
HTTP_PORT=8014 veripay-investigation_agent
```

The vLLM provider builds prompts **only from redacted context** (the
transaction, 30-day baseline, and macro context are all tokenized before
anything crosses the boundary) and falls back to the deterministic explainer
whenever the server is unreachable or returns no text. The LLM can never
authorize a payment — it only summarizes evidence (see
`docs/blueprint-alignment.md`). The optional Helm inference workload can serve
the vLLM endpoint on GPU nodes.

Any OpenAI-compatible endpoint works, including hosted ones. Example — Groq
(no local GPU needed):

```bash
pip install -e "services/investigation_agent[llm]"
export LLM_PROVIDER=openai_compatible
export LLM_BASE_URL=https://api.groq.com/openai/v1
export LLM_API_KEY=gsk_<your-key>   # from env/secret manager; never commit
export LLM_MODEL=openai/gpt-oss-20b
HTTP_PORT=8014 veripay-investigation_agent
```

## Deployment

Three paths to a live URL, all documented in `docs/deployment.md`:

1. **Instant tunnel (no account, works now)** — `brew install cloudflared`
   then `scripts/live-demo-tunnel.sh 5173` (or `8001`) prints a public
   `https://<random>.trycloudflare.com` URL to the running local service.
2. **Render Blueprint** — `infra/deploy/render.yaml` provisions free web
   services for the core demo chain from this repo (New → Blueprint → connect
   `github.com/Amouriii/VeriPay`).
3. **Railway** — `infra/deploy/railway.json` + `railway up` per service.

All services build from `infra/deploy/veripay.Dockerfile` (repo-root context,
installs the local `veripay-common` package first, binds the injected
`PORT`). Note: `infra/terraform/` and `infra/k8s/` are stubs and are **not**
used by Render/Railway. A live URL requires a Render/Railway account (or
cloudflared) — the configs are ready, so going live is one command once an
account exists. Documented env vars are in `README.md` → Environment
variables.
