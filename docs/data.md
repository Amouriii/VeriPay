# Data & Preprocessing

## Data sources

### 1. Real transactional schemas and fixtures (`datasets/`)

The platform ships contract-level data assets that define the shape of every
record the services exchange:

| Asset | Contents |
|---|---|
| `datasets/schemas/*.json` | JSON schemas for transactions, device integrity/GPV signals, virtual card tokens, merchant profiles, disputes, compliance triggers, and issuer accounts |
| `datasets/schemas/avro/` | Avro schemas for the Kafka topics (`tx.ingress.raw`, `tx.features.enriched`) |
| `datasets/fixtures/` | Hand-written sample payloads (e.g., `transactions_sample.json`) used by tests and docs |
| `datasets/migrations/` | SQL DDL for the five logical PostgreSQL databases (`customer`, `bank`, `fraud_ops`, `merchant`, `mobile`) |

These are **authoritative for structure** but are not training volumes — they
contain a handful of rows for contract validation, not statistics.

### 2. Synthetic labeled dataset (`datasets/synthetic/`)

Because no production transaction corpus is available, the ML pipelines train
on a **deterministically generated synthetic dataset**
(`ml/datasets/generate_synthetic.py` → `datasets/synthetic/transactions_labeled.csv`).

Generation rationale:

- **Reproducibility** — the generator is fully seeded (`seed=42` default), so
  the committed CSV, the models trained from it, and every metric in
  `docs/evaluation.md` are reproducible byte-for-byte on any machine.
- **Domain grounding** — feature distributions and fraud mechanisms are
  calibrated to the fraud literature and to the exact fields the services
  already consume (amount, MCC, velocity, device/network trust, impossible
  travel, new device, transaction hour). Synthetic data lets us demonstrate
  the *full* pipeline (train → serve → fuse → decide → explain) with
  measurable behavior while avoiding any privacy or licensing constraints.
- **Contamination realism** — the fraud label is generated from a
  ground-truth score that combines the same signals the deterministic rule
  engine uses, plus an unobserved latent factor, so the ML models learn
  patterns the rules cannot express as thresholds.

Real-world analogs for production: labeled card-transaction fraud data from
Kaggle (IEEE-CIS), payment-rail logs, and analyst-remediated cases from the
feedback loop (`services/feedback_loop`), which is the designed production
label source.

## Schema & format

`datasets/synthetic/transactions_labeled.csv` — one row per transaction,
comma-separated, no header comments:

| Column | Type | Meaning |
|---|---|---|
| `transaction_id` | string | `tx_<n>` |
| `amount_minor` | int | Amount in minor currency units (e.g., cents) |
| `amount_log` | float | `log1p(amount_minor)` — used by models for scale robustness |
| `mcc` | int | Merchant category code (e.g., 5712) |
| `mcc_risk` | float | Prior category risk in [0, 1] derived from MCC bands |
| `hour_of_day` | int | Transaction hour 0–23 (UTC) |
| `weekend` | int | 1 if Saturday/Sunday else 0 |
| `velocity_5m` | int | Transactions by this card in the last 5 minutes |
| `device_trust` | int | 1 = trusted device, 0 = untrusted, −1 = unknown |
| `network_trust` | int | 1 = trusted network, 0 = untrusted, −1 = unknown |
| `impossible_travel` | int | 1 if location/time implies impossible travel |
| `new_device` | int | 1 if the device is new to the account |
| `distance_km` | float | Distance from the account's home location |
| `is_fraud` | int | **Label** — 1 = fraudulent, 0 = legitimate |

The model feature vector (used by both `ml/supervised` training and the
`services/supervised_model` serving endpoint) is a fixed, ordered subset:

```
amount_log, mcc_risk, velocity_5m, device_trust, network_trust,
impossible_travel, new_device, hour_of_day, weekend, distance_km
```

`FEATURE_COLUMNS` in `ml/supervised/features.py` is the single source of truth
for this ordering; the serving service mirrors it.

## Preprocessing / cleaning

Applied inside `ml/supervised/train.py` (and mirrored by `ml/anomaly/train.py`):

1. **Load & validate** — read CSV, assert no missing values in the feature
   columns and that the label is binary.
2. **Identity columns dropped** — `transaction_id`, `amount_minor`, and `mcc`
   are excluded from the model matrix (they are identifiers or already
   transformed into `amount_log` / `mcc_risk`). No PAN, CVV, or other PCI data
   ever enters the dataset — the generator never produces it.
3. **Missing-signal encoding** — device/network trust is tricategorical
   (trusted / untrusted / unknown); unknown is encoded as −1 so the model can
   learn "signal absent" as a distinct state rather than imputing a value.
4. **Log transform** — amount is log-transformed to tame the heavy right tail
   of transaction values.
5. **No scaling** — XGBoost and Isolation Forest are tree-based / split-based
   and invariant to monotonic feature scaling, so no normalization is applied.
6. **Class balance** — the generator targets a ~3% fraud rate (realistic for
   card fraud). Training keeps the natural imbalance and evaluates with
   precision/recall and PR-AUC (which are robust to imbalance) in addition to
   ROC-AUC.

## Train / validation / test split

`ml/supervised/train.py` splits **stratified by label** to preserve the fraud
rate in every fold:

| Split | Share | Purpose |
|---|---|---|
| Train | 70% | Fit the XGBoost ensemble |
| Validation | 15% | Early stopping and threshold selection |
| Test | 15% | Held-out evaluation reported in `docs/evaluation.md` |

- The split is seeded (`split_seed=42`) so evaluation numbers are
  reproducible; no model sees test rows during training.
- The anomaly model (Isolation Forest) is unsupervised and trains on the full
  feature matrix (minus labels); it is still **evaluated** against the held-out
  test labels to report separation quality (see `docs/evaluation.md`).
