# Graph / Coordinated Fraud Engine

**Implements:** PLAN §12

Entity graph features and `network_risk_score` — the fourth scoring axis
described in `docs/network-analysis.md`. While every other model looks at one
customer at a time, this service looks at the *connections between* customers,
merchants, and shared counterparties.

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/graph/observe` | POST | Record a transaction into the in-memory graph (deduped by `transaction_id`) |
| `/api/v1/graph/score` | POST | Observe + compute the network risk score, findings, and ego graph for a transaction |
| `/api/v1/graph/ego/{cc_num}` | GET | Ego graph (1-hop peers) + features for a customer |
| `/api/v1/graph/community/{cc_num}` | GET | Full Louvain-style community (multi-hop fraud ring) + aggregate cluster stats |
| `/health` | GET | Service health + graph size |

### Score response

```json
{
  "network_risk_score": 0.0,   // 0..1
  "available": false,           // false when the customer has no cross-customer edges
  "findings": ["Shares merchant(s) with 2 confirmed-fraud account(s) …"],
  "features": { "merchant_degree": 1, "shared_counterparty_count": 2, "flagged_neighbor_count": 2, … },
  "ego": { "nodes": […], "edges": […] }
}
```

## Backfill from the training dataset

On first access the store is backfilled from
`datasets/synthetic/transactions_labeled.csv` (the same file used to train the
supervised/anomaly models) so every customer's full merchant history is present
from the very first score, not just transactions that flowed through the
analyst API. Rows with `is_fraud=1` mark that customer as confirmed-fraud — the
graph's risk seeds. Override the path with `VERIPAY_GRAPH_SEED_CSV`; unset it to
disable backfill (the store then warms up transaction-by-transaction).

The dataset now carries `cc_num`, `merchant`, and `timestamp` columns plus an
injected fraud ring of 8 accounts sharing one merchant — regenerate it with
`python ml/datasets/generate_synthetic.py`.

## Prototype scoring model

The Sparkov dataset the current prototype runs on does not carry beneficiary
account IDs, device fingerprints, or IP addresses, so the full beneficiary-level
mule graph is not buildable yet. Per the document's own *prototype approach*
this service builds what the available data *does* support:

- a **customer ↔ merchant bipartite graph** projected onto a **customer ↔
  customer "shared merchant" graph**;
- **temporal co-occurrence** (peer transactions at the same merchant within ±60s);
- **feedback-flag propagation** — confirmed-fraud customers (from the analyst
  feedback loop) seed risk that propagates to peers sharing their merchants.

The `network_risk_score` is a transparent 0..1 blend of node features
(`flagged_exposure` 45%, `shared_counterparty_count` 25%, `co_occurrence_count`
15%, `merchant_fan_in` 15%). It returns `0.0` and `available=false` for an
isolated customer so risk fusion can redistribute the weight without distorting
the score.

The core logic is pure-stdlib (no `networkx` dependency) and lives in
`ml/graph/extract.py` so it is shared by this service and the analyst API.

## Develop
```bash
pip install -e .
pip install -e ../../ml
pytest
uvicorn veripay_graph_engine.main:app --reload --port 8008
```
