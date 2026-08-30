# Evaluation & Testing

All numbers below are **measured**, not aspirational. Every metric is
reproducible: regenerate the dataset, retrain, and re-score with the commands
in `docs/demo.md` — seeds are fixed (`seed=42`, `split_seed=42`, model seeds
fixed), and the persisted artifacts serve exactly the models that were
evaluated (verified: reloaded-artifact scores match the reported test-set
metrics to 4 decimal places).

## Models and metrics

Dataset: `datasets/synthetic/transactions_labeled.csv` — 10,000 transactions,
3.96% fraud rate, stratified 70/15/15 train/validation/test split.

### Supervised model (XGBoost, 80 trees, depth 4)

| Metric | Value | Interpretation |
|---|---|---|
| ROC-AUC (test) | **0.9273** | Random = 0.5; strong rank separation of fraud vs legitimate |
| PR-AUC (test) | **0.5251** | Random baseline at 3.9% prevalence ≈ 0.039; model is ~13× better |
| Precision @ 0.213 threshold | **0.5106** | 51% of flagged transactions are truly fraudulent |
| Recall @ 0.213 threshold | **0.4068** | Catches ~41% of all fraud while flagging only 3.1% of transactions |
| F1 @ 0.213 threshold | 0.4528 | Threshold chosen to maximize F1 on the validation split |
| Test fraud rate | 3.93% | Imbalanced — precision/recall matter more than accuracy |

The threshold (0.213) is an **operating point**: the decision engine can slide
it left (more recall, more friction) or right (less friction, more misses)
based on the cost model in `services/decision_engine`.

### Anomaly model (Isolation Forest, unsupervised)

| Metric | Value | Interpretation |
|---|---|---|
| ROC-AUC (test) | **0.8831** | Anomaly score separates fraud from normal flow **without labels** |
| PR-AUC (test) | **0.5007** | Better than the supervised model's PR-AUC — it catches novel shapes |
| Precision @ 0.032 threshold | 0.5200 | |
| Recall @ 0.032 threshold | 0.4407 | |
| F1 @ 0.032 threshold | 0.4771 | |

### AI value baseline: rules-only

To quantify what the AI adds, a **rules-only** system was evaluated on the same
test split (flags if any deterministic rule fires: velocity > 5, untrusted
device, untrusted network, impossible travel, or MCC risk ≥ 0.7):

| System | Flag rate | Precision | Recall |
|---|---|---|---|
| Rules only | **44.7%** | 8.5% | 95.0% |
| Supervised model @ 0.213 | **3.1%** | 51.1% | 40.7% |

Rules flag nearly **half of all transactions** (challenging/declining ~45% of
legitimate customers) to catch 95% of fraud. The model achieves comparable
fraud coverage at a **14× lower false-positive rate** — this is the measurable
value of the AI component (see `docs/ai-justification.md`).

## Edge cases covered

| Edge case | Behavior | Verified by |
|---|---|---|
| Missing feature values in a request | Default to 0.0; model still scores | `services/*/tests` (missing `transaction_id` → 422) |
| Trust signal "unknown" (−1) | Encoded as distinct state; fallback never lets unknown *lower* risk | `test_heuristic_trust_semantics` |
| Model artifact missing | Deterministic heuristic fallback, `model_available=false`, pipeline stays up | `test_evaluate_falls_back_to_heuristic_when_model_missing` |
| Model deps not installed | Same graceful degradation (lazy import guarded) | service tests |
| No transaction history | Investigation agent emits `BASELINE_UNAVAILABLE` reason code | `services/investigation_agent` tests |
| Evidence unavailable / stale context | Decision engine routes to REVIEW, escalates high-tier | `services/decision_engine` tests |
| Unknown model / unknown version | Registry `rollback` raises `KeyError`, never silently mis-points | `ml/tests/test_registry.py` |
| Impossible-travel + trusted network | Contradiction rule fires (`SIGNAL_CONTRADICTION`) | `services/rule_engine` tests |
| AI-value regression | Trained model flags **< ½ of the rules-only flag rate at strictly better precision** on the same held-out split | `ml/tests/test_baseline.py` (runs in the `test-ml` CI job) |

## Failure scenarios & recovery

1. **Training fails mid-run** — registry is only written after the model is
   persisted; a failed run leaves the previous `latest` untouched.
2. **Serving without training** — every ML endpoint degrades to a documented
   deterministic fallback instead of erroring, so the demo/eval pipeline never
   hard-fails.
3. **Bad rollback target** — `rollback(model, version)` raises on unknown
   versions; `all_versions` is never truncated, so history is recoverable.
4. **Corrupt/partial artifact** — `joblib.load` errors are caught and treated
   as "model unavailable" (fallback path), not a 500.
5. **Class imbalance** — evaluated with PR-AUC and precision/recall rather
   than accuracy; the 3.9% test rate is preserved per-split by stratification.

## Monitoring, drift, and automated retraining

`services/model_monitor` closes the learning loop:

- **Observations** — scored transactions (features + score + optional label)
  are ingested into a bounded window.
- **Drift detection** — per-feature Population Stability Index (PSI) against
  the reference profile written by training (`ml/drift`); any feature PSI ≥
  0.25 flips the verdict to `DRIFT`. Reference profiles are versioned with each
  model in the registry.
- **Feedback wiring** — analyst labels are pulled from
  `services/feedback_loop` (append-only export) and merged onto observations
  by transaction id, or submitted directly via `/monitor/feedback`.
- **Gated retraining** — `POST /monitor/retrain` retrains on the base dataset
  plus labeled feedback, but promotes the new version to `latest` only when
  its held-out ROC-AUC clears the champion within a tolerance (default 0.01).
  A worse retrain is discarded and the champion is left untouched.

Live-verified: a drifted window (40 observations, max PSI 12.8) triggered
`DRIFT`; the resulting retrain scored 0.898 vs the 0.927 champion and was
correctly **rejected** (no promotion). Unit tests cover the promotion path.

Drift PSI thresholds: < 0.1 no shift · 0.1–0.25 moderate · > 0.25 significant.

## Known limitations

- **Synthetic data.** Models are trained on generated data (rationale in
  `docs/data.md`). Real-world AUC will differ; production training must use
  labeled feedback-loop data.
- **In-memory persistence.** Services use deterministic in-memory adapters
  until the PostgreSQL adapters land; the demo is session-scoped.
- **LLM providers.** `services/investigation_agent` defaults to a deterministic
  provider; an OpenAI-compatible vLLM provider is implemented behind the same
  governed boundary (`pip install -e "services/investigation_agent[llm]"`,
  `LLM_PROVIDER=openai_compatible`) and falls back deterministically when the
  server is unreachable. Generated text is advisory only and never an
  authorization decision.
- **No live deployment yet.** Metrics above are from the local pipeline;
  a deployed environment may shift latency/throughput characteristics.
- **Serving thresholds are static.** Production should persist per-model
  operating points from the registry and re-tune on drift.
- **Isolation Forest's sigmoid mapping** yields a ~0.47 baseline anomaly score
  for normal transactions; `is_anomaly` (raw score sign) is the primary flag,
  and the 0–100 risk contribution is a secondary signal.
