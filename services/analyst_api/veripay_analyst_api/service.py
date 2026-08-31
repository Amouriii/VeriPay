"""Pipeline orchestrator for the analyst API composite service.

Wires the existing supervised, anomaly, risk-fusion, decision, and
investigation services into the architecture's flow and inserts the live
feedback + drift score adjustments before a decision is finalized.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from veripay_common.enums import DecisionAction, RiskBand, RiskTier

from veripay_analyst_api import adjustments, features16
from veripay_analyst_api.clients import PipelineClient
from veripay_analyst_api.config import Settings
from veripay_analyst_api.config import settings as _default_settings
from veripay_analyst_api.features import build_features, describe_features
from veripay_analyst_api.models import (
    Adjustment,
    AlertItem,
    Baseline,
    CaseReport,
    ContributorShare,
    CustomerProfileResponse,
    Decision,
    DriftInfo,
    ExplainResponse,
    FeatureRow,
    FeedbackByDecisionRow,
    FeedbackInput,
    FeedbackResult,
    FeedbackStats,
    HealthResponse,
    RecentTransaction,
    RetrainResponse,
    ScoreRequest,
    ScoreResponse,
    TransactionInput,
    XgbContribution,
)
from veripay_analyst_api.models import (
    TrustStatus as TrustStatusModel,
)
from veripay_analyst_api.profiles import ProfileStore, StoredFeedback, StoredTransaction
from veripay_analyst_api.reasoning import (
    crosscheck_numbers,
    map_decision,
    map_risk_level,
    verification_action_text,
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _min(value: float, upper: float) -> float:
    return min(value, upper)


class AnalystOrchestrator:
    """Stateless pipeline orchestration over an injected client + profile store."""

    def __init__(
        self,
        client: PipelineClient,
        store: ProfileStore | None = None,
        settings: Settings | None = None,
        *,
        now: datetime | None = None,
    ) -> None:
        self.client = client
        self.store = store or ProfileStore()
        self.settings = settings or _default_settings
        self._now = now
        # Scored results retained so the analyst console can look a scored
        # transaction back up by id/cc_num (the dashboard's /score contract).
        self._scored: dict[str, ScoreResponse] = {}
        self._scored_explain: dict[str, ExplainResponse] = {}
        self._lookup_by_customer: dict[int, str] = {}
        self._alerts: list[AlertItem] = []

    # ---- /score ---------------------------------------------------------
    def score(self, request: ScoreRequest) -> ScoreResponse:
        tx = request.transaction
        # Idempotent by transaction_id: re-scoring the same transaction (e.g.
        # /explain internally scores) must not duplicate the alert or the
        # customer-history row, which would corrupt baselines and the queue.
        if tx.transaction_id in self._scored:
            return self._scored[tx.transaction_id]
        customer = tx.cc_num
        before = self.store.history(customer)
        history_90 = [t for t in before if (self._clock(tx) - _ts(t)).days <= 90]
        metrics = self.store.metrics(history_90)

        if tx.model_features is not None:
            feature_mode = "basic"
            features = dict(tx.model_features)
            feature_rows = describe_features(features, metrics)
            features16_rows: list[FeatureRow] = []
        elif self.settings.use_rich_features:
            feature_mode = "rich"
            rich = features16.compute_features16(tx, before, metrics)
            features = features16.map_to_model(rich, tx, before)
            features16_rows = features16.describe_features16(rich, metrics)
            feature_rows = features16_rows
        else:
            feature_mode = "basic"
            features = dict(build_features(tx, before, metrics))
            feature_rows = describe_features(features, metrics)
            features16_rows = []

        supervised = self.client.supervised_score(tx.transaction_id, features)
        anomaly = self.client.anomaly_score(tx.transaction_id, features)

        raw_fraud = float(supervised.get("fraud_probability", 0.0))
        raw_anomaly = float(anomaly.get("anomaly_score", 0.0))
        sup_available = bool(supervised.get("model_available", True))
        anom_available = bool(anomaly.get("model_available", True))
        model_available = sup_available and anom_available
        model_versions = {
            name: str(payload.get("model_version", "unknown"))
            for name, payload in (("supervised", supervised), ("anomaly", anomaly))
            if payload.get("model_available", False)
        }
        model_fallbacks = [
            name
            for name, payload in (("supervised", supervised), ("anomaly", anomaly))
            if bool(payload.get("fallback", False)) or not bool(
                payload.get("model_available", False)
            )
        ]

        labels = self.store.feedback_for_customer(customer)
        fb = adjustments.feedback_adjustment(
            labels,
            window=self.settings.TRUST_BOOST_WINDOW,
            trust_factor=self.settings.TRUST_BOOST_FACTOR,
            add=self.settings.HEIGHTENED_ALERT_ADD,
        )
        drift_report = self.store.detect_drift(customer)
        drift = adjustments.drift_adjustment(
            drift_report.kind if drift_report else None,
            confirmed_by_feedback=self.store.recent_benign(
                customer, self.settings.TRUST_BOOST_WINDOW
            ),
            gradual_factor=self.settings.GRADUAL_DRIFT_FACTOR,
            sudden_factor=self.settings.SUDDEN_DRIFT_FACTOR,
        )
        combined = adjustments.chain(fb, drift)

        adjusted_fraud = _clamp01(raw_fraud + combined.fraud_add)
        adjusted_anomaly = _clamp01(raw_anomaly * combined.anomaly_factor)

        # Network (graph) scoring axis — fourth fusion component (PLAN §12).
        # Best-effort: a graph-engine failure marks the axis unavailable so
        # risk fusion redistributes this weight across the available axes.
        graph_payload = {
            "transaction_id": tx.transaction_id,
            "cc_num": customer,
            "merchant": tx.merchant,
            "amount": tx.amount,
            "timestamp": self._clock(tx).isoformat(),
            "flagged": self.store.has_confirmed_fraud(customer),
        }
        network_risk = 0.0
        network_available = False
        network_findings: list[str] = []
        network_ego: dict[str, Any] | None = None
        network_community: dict[str, Any] | None = None
        try:
            graph = self.client.graph_score(graph_payload)
            network_risk = float(graph.get("network_risk_score", 0.0))
            network_available = bool(graph.get("available", False))
            network_findings = list(graph.get("findings", []))
            network_ego = graph.get("ego")
        except Exception:  # noqa: BLE001 - downstream graph failure is non-fatal
            pass
        # Best-effort: fetch the full community (multi-hop fraud ring) for the
        # dashboard's community view. Failure is non-fatal.
        if network_available:
            with contextlib.suppress(Exception):
                _ = self.client.graph_community(customer)

        components = [
            {
                "component": "supervised",
                "score": _min(round(adjusted_fraud * 100), 100),
                "weight": 0.5,
                "available": sup_available,
            },
            {
                "component": "anomaly",
                "score": _min(round(adjusted_anomaly * 100), 100),
                "weight": 0.5,
                "available": anom_available,
            },
            {
                "component": "network",
                "score": _min(round(network_risk * 100), 100),
                "weight": self.settings.NETWORK_FUSION_WEIGHT,
                "available": network_available,
            },
        ]
        fusion = self.client.fuse_risk(tx.transaction_id, components)
        unified = int(fusion["unified_score"])
        band = RiskBand(fusion["band"])
        tier = RiskTier(fusion["tier"])

        decision = self.client.decide(
            {
                "transaction_id": tx.transaction_id,
                "risk_score": unified,
                "risk_band": band.value,
                "risk_tier": tier.value,
                "payment_rail": "CARD",
            }
        )
        action = DecisionAction(decision["action"])
        decision_tier = RiskTier(decision["risk_tier"])
        decision_band = RiskBand(decision["risk_band"])

        doc_decision = map_decision(action, decision_tier)
        # Four-quadrant refinement (architecture §6): the fused score alone
        # cannot separate "unusual but legitimate" from "normal-looking fraud".
        # When the cost-aware engine would BLOCK but the fraud probability is
        # high while the anomaly score is low, the transaction matches known
        # fraud while appearing normal → REVIEW_STEALTH (human review + biometric)
        # instead of an automatic freeze.
        fraud_high = adjusted_fraud >= self.settings.FRAUD_QUADRANT_THRESHOLD
        anomaly_low = adjusted_anomaly < self.settings.ANOMALY_QUADRANT_THRESHOLD
        if doc_decision == Decision.BLOCK and fraud_high and anomaly_low:
            doc_decision = Decision.REVIEW_STEALTH
        risk_level = map_risk_level(decision_tier)
        verification_action = verification_action_text(doc_decision, decision_tier)

        # Register this transaction so future drift/profile calls see it.
        self.store.add_transaction(
            StoredTransaction(
                transaction_id=tx.transaction_id,
                cc_num=customer,
                amount=tx.amount,
                merchant=tx.merchant,
                category=tx.category,
                timestamp=self._clock(tx),
                location=tx.location,
                merchant_location=tx.merchant_location,
                decision=doc_decision,
            )
        )

        adjustments_list = self._adjustment_summaries(fb, drift)
        resp = ScoreResponse(
            transaction_id=tx.transaction_id,
            cc_num=customer,
            decision=doc_decision,
            risk_level=risk_level,
            verification_action=verification_action,
            action=action,
            risk_band=decision_band,
            risk_tier=decision_tier,
            fused_risk_score=unified,
            fraud_probability=round(adjusted_fraud, 4),
            anomaly_score=round(adjusted_anomaly, 4),
            raw_fraud_probability=round(raw_fraud, 4),
            raw_anomaly_score=round(raw_anomaly, 4),
            model_available=model_available,
            model_versions=model_versions,
            model_fallbacks=model_fallbacks,
            feature_mode=feature_mode,
            adjustments=adjustments_list,
            features=feature_rows,
            features16=features16_rows,
            anomaly_top_contributors=self._anomaly_contributors(features),
            xgboost_feature_contributions=self._xgb_contributions(features, adjusted_fraud),
            recent_transactions=self._recent_transactions(before),
            network_risk_score=round(network_risk, 4),
            network_available=network_available,
            network_findings=network_findings,
            network_ego=network_ego,
            network_community=network_community,
        )
        # Best-effort observe so future scores on peers see this transaction.
        with contextlib.suppress(Exception):
            self.client.graph_observe(graph_payload)
        # Retain the result so the dashboard's /score|/explain lookups work.
        self._scored[tx.transaction_id] = resp
        self._lookup_by_customer[customer] = tx.transaction_id
        if doc_decision != Decision.PASS:
            self._alerts.append(
                AlertItem(
                    transaction_id=tx.transaction_id,
                    cc_num=customer,
                    customer_name=f"Customer {customer}",
                    amount=round(tx.amount, 2),
                    currency="USD",
                    merchant=tx.merchant,
                    time=self._clock(tx).isoformat(),
                    decision=doc_decision,
                    risk_level=risk_level,
                    fraud_probability=resp.fraud_probability,
                    anomaly_score=resp.anomaly_score,
                )
            )
        return resp

    # ---- /explain -------------------------------------------------------
    def explain(self, request: ScoreRequest) -> ExplainResponse:
        tx = request.transaction
        score = self.score(request)

        history = self.store.history(tx.cc_num)
        # Drop the transaction just scored so the explanation describes prior data.
        prior = [h for h in history if h.transaction_id != tx.transaction_id]
        investigation = self.client.investigate(
            {
                "transaction_id": tx.transaction_id,
                "transaction": {
                    "amount": tx.amount,
                    "merchant": tx.merchant,
                    "category": tx.category,
                },
                "transaction_history": [
                    {"amount": h.amount, "merchant": h.merchant} for h in prior[-20:]
                ],
                "risk_score": score.fused_risk_score,
                "macro_context": {"decision": score.decision.value, "cc_num": tx.cc_num},
            }
        )
        summary = str(investigation.get("summary", ""))

        evidence = [
            f"Fraud probability {score.raw_fraud_probability:.4f}"
            f" (adjusted {score.fraud_probability:.4f}).",
            f"Anomaly score {score.raw_anomaly_score:.4f} (adjusted {score.anomaly_score:.4f}).",
            f"Unified risk score {score.fused_risk_score}/100 ({score.risk_tier.value}).",
            *(a.description for a in score.adjustments if a.description),
        ]
        if summary:
            evidence.append(summary)
        # Network context — the analyst-visible graph findings (PLAN §12).
        if score.network_available:
            evidence.append(
                f"Network risk score {score.network_risk_score:.4f} (graph axis available)."
            )
            evidence.extend(score.network_findings)

        pattern = self._pattern_match(score)
        # Network typology overrides the pattern label when the graph axis is
        # the dominant driver — i.e. the transaction is unremarkable alone but
        # the customer is connected to confirmed-fraud clusters.
        if (
            score.network_available
            and score.network_risk_score
            >= max(score.raw_fraud_probability, score.raw_anomaly_score)
            and score.network_risk_score > 0.0
        ):
            pattern = (
                "Network-connected risk: this customer shares merchant(s) with "
                "confirmed-fraud accounts — coordinated-fraud signal from the "
                "graph axis (PLAN §12)."
            )
        case_report = CaseReport(
            verdict=(f"{score.decision.value} — {self._verdict_phrase(score.decision)}"),
            evidence=evidence,
            pattern_match=pattern,
            recommended_action=score.verification_action,
        )
        # Anti-hallucination: any number the generated text cites must exist in the payload.
        payload = {
            "fraud_probability": score.raw_fraud_probability,
            "anomaly_score": score.raw_anomaly_score,
            "risk_score": score.fused_risk_score,
            "amount": tx.amount,
            "network_risk_score": score.network_risk_score,
        }
        case_report.crosschecked, case_report.hallucination_flagged = crosscheck_numbers(
            f"{score.decision.value} {summary} {' '.join(evidence)}", payload
        )
        result = ExplainResponse(
            transaction_id=tx.transaction_id,
            cc_num=tx.cc_num,
            risk_level=score.risk_level,
            verification_action=score.verification_action,
            case_report=case_report,
            score=score,
        )
        self._scored_explain[tx.transaction_id] = result
        return result

    # ---- /customer/{cc_num}/profile ------------------------------------
    def profile(self, cc_num: int) -> CustomerProfileResponse:
        store = self.store
        trust = store.trust_status(cc_num, self.settings.TRUST_BOOST_WINDOW)
        trust_status = TrustStatusModel(level=trust.level, message=trust.message)
        history = store.history(cc_num)
        if not history:
            empty = Baseline(
                median_amount="—",
                typical_hours="—",
                home_location="—",
                distinct_merchants=0,
                daily_txn_count=0,
            )
            return CustomerProfileResponse(
                cc_num=cc_num,
                long_term_baseline=empty,
                recent_behavior=empty,
                drift_detected=None,
                trust_status=trust_status,
            )
        last_ts = _ts(history[-1])
        long_term = [t for t in history if (last_ts - _ts(t)).days <= 90]
        recent = store.recent(cc_num, 30)

        long_baseline = store.metrics(long_term)
        recent_baseline = store.metrics(recent)
        drift = store.detect_drift(cc_num)
        drift_detected: DriftInfo | None = None
        if drift is not None:
            drift_detected = DriftInfo(
                kind=drift.kind, severity=drift.severity, message=drift.message
            )

        return CustomerProfileResponse(
            cc_num=cc_num,
            long_term_baseline=self._baseline(long_baseline),
            recent_behavior=self._baseline(recent_baseline),
            drift_detected=drift_detected,
            trust_status=trust_status,
        )

    # ---- /customer/{cc_num}/network ------------------------------------
    def network(self, cc_num: int) -> dict[str, Any]:
        """Network (graph) context for a customer, browsable without an alert.

        Calls the graph engine's ego endpoint (PLAN §12) for the score,
        findings, and 1-hop ego graph, and the community endpoint for the full
        multi-hop fraud ring. Both are best-effort: a graph-engine failure
        returns an empty payload with ``available=False`` so the profile page
        stays navigable.
        """
        payload: dict[str, Any] = {
            "cc_num": cc_num,
            "network_risk_score": 0.0,
            "available": False,
            "findings": [],
            "features": {},
            "ego": {"nodes": [], "edges": []},
            "community": None,
        }
        try:
            ego = self.client.graph_ego(cc_num)
            payload["network_risk_score"] = float(ego.get("network_risk_score", 0.0))
            payload["available"] = bool(ego.get("available", False))
            payload["findings"] = list(ego.get("findings", []))
            payload["features"] = ego.get("features", {})
            payload["ego"] = ego.get("ego", {"nodes": [], "edges": []})
        except Exception:  # noqa: BLE001 - graph failure is non-fatal
            pass
        # Fetch the full community (multi-hop ring) separately so the
        # investigator can browse the entire cluster, not just 1-hop peers.
        if payload["available"]:
            with contextlib.suppress(Exception):
                payload["community"] = self.client.graph_community(cc_num)
        return payload

    # ---- /feedback ------------------------------------------------------
    def submit_feedback(self, feedback: FeedbackInput) -> FeedbackResult:
        self.store.record_feedback(
            StoredFeedback(
                transaction_id=feedback.transaction_id,
                cc_num=feedback.cc_num,
                analyst_decision=feedback.analyst_decision,
                decision=feedback.decision,
                notes=feedback.notes,
                timestamp=self._now or datetime.now(UTC),
            )
        )
        # The local copy powers the live trust-boost/heightened-alert
        # adjustments. The canonical label is also forwarded (best-effort) to
        # the append-only feedback_loop and to model_monitor's retrain gate so
        # corrected labels feed periodic retraining (architecture section 11).
        label = adjustments.to_review_label(feedback.analyst_decision)
        steps: list[str] = []
        self._forward_feedback(
            {
                "feedback_loop": lambda: self.client.append_feedback(
                    {
                        "idempotency_key": f"{feedback.transaction_id}:{label}",
                        "transaction_id": feedback.transaction_id,
                        "analyst_id": feedback.analyst_id,
                        "label": label,
                        "reason_codes": [],
                        "decision_action": feedback.decision.value,
                    }
                ),
                "model_monitor": lambda: self.client.record_monitor_label(
                    feedback.transaction_id, label
                ),
            },
            steps,
        )
        return FeedbackResult(
            status="recorded",
            transaction_id=feedback.transaction_id,
            recorded=True,
            note="; ".join(steps) or "recorded locally",
        )

    def _forward_feedback(self, targets: dict[str, Callable[[], object]], steps: list[str]) -> None:
        for name, forward in targets.items():
            try:
                forward()
                steps.append(f"{name}:ok")
            except Exception:  # noqa: BLE001 - downstream failure is non-fatal
                steps.append(f"{name}:unavailable")

    # ---- /feedback/stats ------------------------------------------------
    def feedback_stats(self) -> FeedbackStats:
        records = self.store.all_feedback()
        confirmed = sum(1 for r in records if adjustments.is_confirmed_fraud(r.analyst_decision))
        benign = sum(1 for r in records if adjustments.is_benign(r.analyst_decision))
        legit_only = sum(
            1
            for r in records
            if r.analyst_decision.strip().lower() == "customer_confirmed_legitimate"
        )
        false_alarm = sum(
            1
            for r in records
            if r.analyst_decision.strip().lower() in ("false_alarm", "false_positive")
        )
        total = len(records)
        rows: list[FeedbackByDecisionRow] = []
        by_decision: dict[Decision, list] = {}
        for record in records:
            by_decision.setdefault(record.decision, []).append(record)
        for decision in (
            Decision.BLOCK,
            Decision.REVIEW_STEALTH,
            Decision.REVIEW_UNUSUAL,
            Decision.PASS,
        ):
            bucket = by_decision.get(decision, [])
            bucket_confirmed = sum(
                1 for r in bucket if adjustments.is_confirmed_fraud(r.analyst_decision)
            )
            bucket_fp = sum(1 for r in bucket if adjustments.is_benign(r.analyst_decision))
            rows.append(
                FeedbackByDecisionRow(
                    decision=decision,
                    total_reviewed=len(bucket),
                    confirmed_fraud=bucket_confirmed,
                    false_alarm=bucket_fp,
                    fraud_rate=round(bucket_confirmed / len(bucket), 4) if bucket else 0.0,
                )
            )
        false_positive_rate = (
            round(benign / (confirmed + benign), 4) if (confirmed + benign) else 0.0
        )
        return FeedbackStats(
            total_feedback=total,
            confirmed_fraud=confirmed,
            false_alarm=false_alarm,
            customer_confirmed_legitimate=legit_only,
            false_positive_rate=false_positive_rate,
            feedback_by_decision=rows,
        )

    # ---- /retrain -------------------------------------------------------
    def retrain(self, version: str | None = None) -> RetrainResponse:
        result = self.client.retrain(version)
        raw_metrics = result.get("metrics")
        metrics = raw_metrics if isinstance(raw_metrics, dict) else {}
        return RetrainResponse(
            status=str(result.get("status", "unknown")),
            message=str(result.get("message", "")),
            new_version=result.get("new_version"),
            metrics={k: float(v) for k, v in metrics.items()},
        )

    # ---- /health --------------------------------------------------------
    def health(self) -> HealthResponse:
        upstream = self.client.health()
        models_loaded = [
            name
            for name in ("supervised", "anomaly")
            if upstream.get(name, {}).get("status") == "ok"
        ]
        return HealthResponse(
            status="ok",
            models_loaded=models_loaded,
            model_versions={
                name: str(info.get("model_version", "unknown"))
                for name, info in upstream.items()
                if info.get("model_version") is not None
            },
            upstream={name: info.get("status", "unknown") for name, info in upstream.items()},
        )

    # ---- /alerts + lookups ---------------------------------------------
    def alerts(self) -> list[AlertItem]:
        """Stored non-PASS scoring results, most suspicious first."""
        return sorted(
            self._alerts,
            key=lambda a: a.fraud_probability + a.anomaly_score,
            reverse=True,
        )

    def lookup_score(
        self, transaction_id: str | None = None, cc_num: int | None = None
    ) -> ScoreResponse:
        key = transaction_id or self._lookup_by_customer.get(cc_num or -1)
        if key is None or key not in self._scored:
            raise LookupError(str(key or ""))
        return self._scored[key]

    def lookup_explain(
        self, transaction_id: str | None = None, cc_num: int | None = None
    ) -> ExplainResponse:
        key = transaction_id or self._lookup_by_customer.get(cc_num or -1)
        if key is None or key not in self._scored_explain:
            raise LookupError(str(key or ""))
        return self._scored_explain[key]

    # ---- helpers --------------------------------------------------------
    def _anomaly_contributors(self, features: dict[str, float]) -> list[ContributorShare]:
        """Top features by magnitude, normalized to 100%.

        Advisory ranking derived from the feature vector (the anomaly service
        does not stream per-feature contributions over REST), matching the
        dashboard's contributor panel.
        """
        ordered = [
            "impossible_travel",
            "new_device",
            "velocity_5m",
            "amount_log",
            "distance_km",
            "mcc_risk",
            "hour_of_day",
        ]
        magnitudes: list[tuple[float, str]] = []
        for name in ordered:
            value = abs(float(features.get(name, 0.0)))
            if name in ("amount_log", "distance_km"):
                value = min(value, 60.0)
            magnitudes.append((value, name))
        total = sum(value for value, _ in magnitudes)
        if total <= 0:
            return [ContributorShare(feature="no_dominant_feature", contribution_pct=100.0)]
        top = sorted(magnitudes, key=lambda item: item[0], reverse=True)[:4]
        top_total = sum(value for value, _ in top)
        return [
            ContributorShare(feature=name, contribution_pct=round(value / top_total * 100, 1))
            for value, name in top
        ]

    def _xgb_contributions(
        self, features: dict[str, float], fraud_probability: float
    ) -> list[XgbContribution]:
        """Deterministic per-feature XGBoost-style contribution estimates.

        A true SHAP call is out of scope for the composite; this mirrors the
        dashboard's SHAP panel with sign/direction derived from the feature
        vector and amplitude scaled by the fraud probability.
        """
        definitions = [
            ("impossible_travel", 0.30, 1.0),
            ("new_device", 0.18, 1.0),
            ("velocity_5m", 0.14, 8.0),
            ("distance_km", 0.12, 800.0),
            ("amount_log", 0.20, 6.0),
            ("weekend", 0.06, 1.0),
        ]
        scale = min(1.0, 0.25 + fraud_probability)
        contributions: list[XgbContribution] = []
        for name, weight, reference in definitions:
            value = float(features.get(name, 0.0))
            ratio = min(1.0, value / reference) if reference else 0.0
            direction = 1 if ratio > 0.30 else -1
            contributions.append(
                XgbContribution(
                    feature=name,
                    shap_value=round(direction * weight * scale, 2),
                )
            )
        return contributions

    def _adjustment_summaries(self, fb: Any, drift: Any) -> list[Adjustment]:
        items: list[Adjustment] = []
        for outcome, kind in ((fb, "feedback"), (drift, "drift")):
            if getattr(outcome, "effect", None) not in (None, "no_adjustment"):
                items.append(
                    Adjustment(
                        kind=kind,
                        effect=outcome.effect,
                        description=outcome.description,
                        anomaly_factor=getattr(outcome, "anomaly_factor", 1.0),
                        fraud_add=getattr(outcome, "fraud_add", 0.0),
                    )
                )
        return items

    def _recent_transactions(
        self, history: list[StoredTransaction], limit: int = 10
    ) -> list[RecentTransaction]:
        result: list[RecentTransaction] = []
        for tx in list(reversed(history))[:limit]:
            location = "—"
            point = tx.location or tx.merchant_location
            if point is not None:
                location = f"{point.lat:.3f},{point.lon:.3f}"
            result.append(
                RecentTransaction(
                    time=tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                    amount=round(float(tx.amount), 2),
                    merchant=tx.merchant,
                    category=tx.category,
                    location=location,
                )
            )
        return result

    def _baseline(self, metrics: Any) -> Baseline:
        if metrics.count == 0:
            return Baseline(
                median_amount="—",
                typical_hours="—",
                home_location="—",
                distinct_merchants=0,
                daily_txn_count=0,
            )
        hourly = f"{metrics.hour_low:02d}:00–{metrics.hour_high:02d}:00"
        return Baseline(
            median_amount=f"${metrics.median_amount:,.2f}",
            typical_hours=hourly,
            home_location="—",  # coords available via history; kept non-sensitive here
            distinct_merchants=metrics.distinct_merchants,
            daily_txn_count=int(metrics.daily_txn_count),
        )

    def _pattern_match(self, score: ScoreResponse) -> str:
        if score.fraud_probability >= 0.6 and score.anomaly_score >= 0.6:
            return "Card testing or account-takeover pattern (unusual AND matches known fraud)."
        if score.anomaly_score >= 0.6:
            return "Unusual behaviour but no known-fraud pattern match (likely traveller/holiday)."
        if score.fraud_probability >= 0.6:
            return "Matches a known-fraud pattern while appearing normal (stealth)."
        return "None identified."

    def _verdict_phrase(self, decision: Decision) -> str:
        phrases = {
            Decision.BLOCK: "transaction frozen and escalated to an analyst.",
            Decision.REVIEW_STEALTH: (
                "flagged for analyst review (appears normal but matches fraud)."
            ),
            Decision.REVIEW_UNUSUAL: "held for a soft verification check.",
            Decision.PASS: "no action required.",
        }
        return phrases.get(decision, "reviewed.")

    def _clock(self, tx: TransactionInput) -> datetime:
        value = tx.timestamp
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _ts(tx: StoredTransaction) -> datetime:
    value = tx.timestamp.replace(tzinfo=UTC) if tx.timestamp.tzinfo is None else tx.timestamp
    return value


def create_orchestrator(
    client: PipelineClient,
    store: ProfileStore | None = None,
    settings: Settings | None = None,
) -> AnalystOrchestrator:
    return AnalystOrchestrator(client=client, store=store, settings=settings)


__all__ = ["AnalystOrchestrator", "create_orchestrator"]
