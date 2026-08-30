# AI Implementation & Justification

VeriPay's AI surface has three components, each chosen for a distinct reason
and each with an explicit "what breaks if removed" analysis below.

## 1. Supervised model — XGBoost (`ml/supervised`, `services/supervised_model`)

**What it does.** Trains a gradient-boosted decision-tree ensemble on the
labeled synthetic transaction dataset to produce a fraud probability
(`fraud_probability`) for every transaction. The score feeds
`services/risk_fusion` alongside deterministic rules.

**Why XGBoost.**

- **Tabular benchmark** — for dense, heterogeneous tabular features
  (amount, velocity, trust flags, time), gradient-boosted trees remain the
  strongest out-of-the-box family; deep nets rarely beat them without
  large-scale feature engineering.
- **Feature robustness** — tree splits are invariant to monotonic scaling and
  tolerate the −1 "unknown" encodings without imputation.
- **Explainability** — native feature-importance and per-prediction attribution
  (TreeSHAP, declared in `ml/pyproject.toml`) satisfy the analyst-facing
  explainability requirement of PLAN §20 without a separate interpretability
  stack.
- **Operational fit** — a single-process model serves sub-millisecond
  predictions per transaction with no GPU dependency, matching the real-time
  card-rail latency path in the blueprint.

**What would happen if it were removed.** The platform would fall back to
rules + fusion only. Hard rules catch *known* patterns (velocity limits,
MCC locks, impossible travel) but cannot generalize: novel fraud patterns,
soft-risk interactions (e.g., "new device + night + moderate amount" that no
single rule trips), and slow-drift attacks go undetected. The supervised score
is the only component that converts *historical fraud outcomes into a
probability for never-before-seen transactions*, which is precisely what
fusion needs for cost-aware decisioning. Removing it turns the decision engine
into a threshold engine over rules — measurable degradation in fraud recall at
equal false-decline cost (see `docs/evaluation.md`, "without AI" baseline).

## 2. Anomaly model — Isolation Forest (`ml/anomaly`, `services/anomaly_model`)

**What it does.** Unsupervised isolation of outliers in the same feature
space. It flags transactions that deviate from the bulk distribution even when
no historical label exists for that pattern.

**Why Isolation Forest.**

- **Label-free** — fraud is rare and labels are late (analyst review);
  unsupervised isolation works from day one, before the feedback loop has
  accumulated enough labels.
- **Linear cost & no distance metric** — isolation-based scoring scales to
  high-cardinality streams and avoids the curse of dimensionality that
  distance-based detectors (kNN, LOF) suffer in tabular feature spaces.
- **Complementarity** — anomaly scores are near-orthogonal to XGBoost's
  supervised signal: XGBoost finds *known-shape* fraud, Isolation Forest finds
  *anything unusual*.

**What would happen if it were removed.** Zero-day and account-takeover-style
fraud that no labeled example resembles would score normally and likely pass
the rules. The anomaly component is the safety net that keeps the platform
responsive to novel attack shapes before retraining catches up.

## 3. LLM investigation agent (`services/investigation_agent`)

**What it does.** Converts the fused risk score, 30-day transaction baseline,
macro context, and structured reason codes into analyst-readable natural
language. It is a governed boundary: inputs pass through deterministic PII
redaction/tokenization, only a ≤30-day baseline and supplied macro context are
included, output is structured with regulatory reason codes, and the LLM has
**zero authorization authority** — it can never block, allow, or alter a
decision (see `docs/blueprint-alignment.md`).

**Why a local, governed LLM boundary (and a deterministic default provider).**

- **Cost/latency** — explanations are advisory and async on the fast path; a
  local provider (vLLM/OpenAI-compatible, optional Helm workload) avoids
  per-call API fees and keeps PII inside the boundary.
- **Deterministic fallback** — `DeterministicLocalLlmProvider` produces the
  same structured summary from the same inputs, making the contract testable
  and the system behavior predictable in evaluation/demo environments.
- **Interchangeable provider** — an OpenAI-compatible vLLM provider
  (`OpenAiCompatibleLlmProvider`) is implemented behind the same protocol
  (`LLM_PROVIDER=openai_compatible`); it builds prompts only from redacted
  context and degrades to the deterministic fallback when the server is
  unreachable.
- **Guardrails first** — the redaction and reason-code layers are deterministic
  and unit-tested; the stochastic LLM is an interchangeable provider behind a
  protocol, so the platform's regulatory posture does not depend on prompt
  behavior.

**What would happen if it were removed.** The platform would still make the
same decisions (the LLM never decides), but analyst productivity collapses:
fraud operators would hand-read risk factors, raw feature lists, and reason
codes instead of receiving one governed paragraph per case. Investigation
turnaround and the explainability requirement of PLAN §20 (which regulators
and the analyst dashboard depend on) would be unmet. This is a UX/efficiency
AI, deliberately separated from the authorization path.

## Why the mix (value argument)

- **Rules** = guaranteed, explainable, cheap coverage of known policy.
- **Supervised model** = generalizes fraud risk from history into a
  probability for the decision engine's cost model.
- **Anomaly model** = catches the unknown.
- **LLM agent** = makes all of the above consumable by humans without
  compromising privacy or control.

Removing any one of the three AI components leaves a measurable, documented
hole (Table below). This is the "AI relevance" argument: each component
carries value that deterministic infrastructure alone does not.

| Removed component | Resulting behavior | Impact |
|---|---|---|
| XGBoost supervised model | Rules-only risk scoring | Novel-fraud recall drops; decision engine loses probability inputs for cost minimization |
| Isolation Forest anomaly | No novelty detection | Zero-day / ATO fraud passes until labels arrive |
| LLM investigation agent | No NL explanations | Analyst workflow degrades; PLAN §20 explainability unmet (decisions unaffected) |
