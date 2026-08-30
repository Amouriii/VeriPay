# Analyst API

Composite, analyst-facing boundary that wires the existing scoring, fusion,
decision, investigation, feedback, and monitoring services behind a single
ergonomic surface. Implements the system-architecture flow's analyst surface
and its live score adjustments.

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/alerts` | GET | Stored non-PASS scoring results, most suspicious first (the alert queue) |
| `/score` | POST | Score a transaction (full `transaction` body) **or** look up an already-scored result (`transaction_id` / `cc_num`) — returns numbers, features, decision, risk level, verification action |
| `/explain` | POST | Score + case report — /score output plus the governed explanation; also accepts a `transaction_id` / `cc_num` lookup |
| `/customer/{cc_num}/profile` | GET | Customer baseline, recent behavior, drift detection, trust status |
| `/feedback` | POST | Submit analyst verdict (confirmed_fraud / false_alarm / customer_confirmed_legitimate); applies live adjustments and forwards the append-only label to `feedback_loop` + `model_monitor` (best-effort) |
| `/feedback/stats` | GET | System performance — false positive rates by decision quadrant |
| `/retrain` | POST | Retrain models via the model monitor with corrected labels |
| `/health` | GET | Service health — upstream scoring/explanation availability |

## Feature engine

Set `FEATURE_MODE` (default `basic`) to control how the model feature vector is
built before scoring:

* `basic` — the repo shared model columns derived from raw signals and a short
  past-history window (velocity_5m, distance, hour, trust flags, …).
* `rich` — the implementation of the architecture's 16 causal-sequence features
  (`features16.py`): velocity counts/sums (1h/24h), amount over 90-day median &
  clipped z-score, merchant/category novelty + days since first seen, distance
  from home and previous transaction, implied travel speed (capped at 9,999
  km/h), hour-of-day, night flag, hours since previous transaction, and hour
  deviation from the customer's modal hour. These are mapped onto the same model
  feature vector, and the dashboard's feature table shows all 16 rows.

Both modes are causal: only transactions that occurred strictly before the one
being scored are referenced, so a later transaction never changes an earlier
feature vector.

**Which to default to?** A head-to-head (`compare_modes.py`, `tests/test_compare_modes.py`)
scores both modes over a deterministic labeled customer corpus. Because both
engines are designed to collapse onto the *same* model vector, they are
decision-equivalent: on a 1080-transaction corpus the two modes produced
identical vectors, identical JSON, zero decision divergence, and matching
FPR (0.058) and fraud-catch (0.788) at the reference threshold. `basic` is the
recommended default: it costs less, needs no merchant/category/coordinates or
long history, and is robust to sparse data. `rich` is an explainability opt-in
that surfaces the full 16-feature table — run the comparison again after any
change to the mapping or feature definitions to confirm equivalence holds.

## Score adjustments

Before the decision is finalized the live feedback and drift adjustments are
applied (architecture §7). Both raw and adjusted scores are returned so an
analyst can see exactly what happened.

* **Feedback** — last `TRUST_BOOST_WINDOW` (3) benign verdicts on the customer
  multiply the anomaly score by `TRUST_BOOST_FACTOR` (0.7); any confirmed-fraud
  verdict adds `HEIGHTENED_ALERT_ADD` (0.1) to the fraud probability.
* **Drift** — gradual lifestyle/relocation drift, confirmed by feedback,
  multiplies the anomaly score by `GRADUAL_DRIFT_FACTOR` (0.6); a sudden
  location jump multiplies it by `SUDDEN_DRIFT_FACTOR` (1.2).

## Four-quadrant decision refinement (architecture §6)

Before the decision is finalized, the two raw axes refine the cost-aware
engine's output. A fused 0–100 score cannot separate "unusual but legitimate"
from "normal-looking fraud" — the raw fraud probability and anomaly score can.
When the engine would BLOCK but `fraud_probability >= FRAUD_QUADRANT_THRESHOLD`
(0.5) while `anomaly_score < ANOMALY_QUADRANT_THRESHOLD` (0.5), the decision
becomes REVIEW_STEALTH (matches known fraud while appearing normal — human
review + biometric) instead of an automatic freeze. Both axes high still BLOCK.

The seed's stealth scenario (`seed_1007_stealth`) exercises exactly this cell:
LA history + a large NY purchase scores `fraud ≈ 0.65 / anomaly ≈ 0.49` →
REVIEW_STEALTH.

## Network (graph) scoring axis — PLAN §12

A fourth fusion component is computed by the graph engine (`VERIPAY_GRAPH_URL`):
the `network_risk_score` plus analyst-readable findings and an ego-graph
payload. It enters `risk_fusion` as a weighted component
(`NETWORK_FUSION_WEIGHT`, default 0.2). When the graph engine is unavailable,
the component is marked unavailable so fusion redistributes its weight across
the available supervised/anomaly axes — the pipeline degrades to the prior
two-axis behaviour. The findings are appended to the `/explain` case report,
and when the graph axis is the dominant driver the `pattern_match` surfaces a
"network-connected risk" typology.

## Seeding the alert queue

`docker compose up` runs the `seed_analyst` one-shot service, which scores a
deterministic batch of realistic transactions through this API so the
console's alert queue, scored-transaction lookups, and customer profiles have
data immediately. Re-seed any time with:

```bash
make seed-analyst          # docker compose run --rm seed_analyst
python scripts/seed-analyst-queue.py   # against localhost:8026
```

Scale the batch for larger demo queues:

```bash
python scripts/seed-analyst-queue.py --variants 3 --count 20
```

`--variants` repeats the curated scenario set (jittered amounts, offset
customer numbers, shifted timestamps); `--count` adds synthetic customers with
per-customer merchant/amount variation. All variation is deterministic.

The script is stdlib-only and prints the decision distribution and the
resulting alert queue. It is idempotent per run; re-running after the service
has restarted adds a fresh batch (analyst_api state is in-memory).

## Develop
```bash
pip install -e .
pytest
uvicorn veripay_analyst_api.main:app --reload --port 8026
```

Downstream services are resolved from the `VERIPAY_*_URL` environment variables
(see `.env.example`); in tests an in-memory fake client is injected.