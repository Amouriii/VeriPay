"""Tests for the network (graph) scoring axis integration (PLAN §12)."""

from __future__ import annotations

from datetime import UTC, datetime

from veripay_analyst_api.clients import PipelineClient
from veripay_analyst_api.config import settings
from veripay_analyst_api.models import (
    Decision,
    RiskLevel,
    ScoreRequest,
    TransactionInput,
)
from veripay_analyst_api.profiles import ProfileStore
from veripay_analyst_api.service import AnalystOrchestrator

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _input(cc_num: int = 7, amount: float = 100.0, **overrides: object) -> TransactionInput:
    fields: dict[str, object] = {
        "transaction_id": f"tx_{cc_num}",
        "cc_num": cc_num,
        "amount": amount,
        "merchant": "m_amazon",
        "category": "ecommerce",
        "timestamp": _BASE,
    }
    fields.update(overrides)
    return TransactionInput(**fields)


def _orch(client: PipelineClient, store: ProfileStore | None = None) -> AnalystOrchestrator:
    return AnalystOrchestrator(client=client, store=store or ProfileStore(), settings=settings)


def test_network_unavailable_when_graph_engine_down(fake_client: PipelineClient) -> None:
    fake_client.graph_fails = True  # type: ignore[attr-defined]
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input()))
    assert resp.network_available is False
    assert resp.network_risk_score == 0.0
    # fusion must still succeed (third component marked unavailable)
    assert resp.fused_risk_score >= 0
    assert fake_client.graph_calls == 1  # type: ignore[attr-defined]


def test_network_component_present_when_available(fake_client: PipelineClient) -> None:
    fake_client.network_risk = 0.6  # type: ignore[attr-defined]
    fake_client.network_available = True  # type: ignore[attr-defined]
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input()))
    assert resp.network_available is True
    assert resp.network_risk_score == round(0.6, 4)
    assert resp.network_findings  # populated by the fake
    assert resp.network_ego is not None


def test_network_findings_appear_in_explain(fake_client: PipelineClient) -> None:
    fake_client.network_risk = 0.8  # type: ignore[attr-defined]
    fake_client.network_available = True  # type: ignore[attr-defined]
    orch = _orch(fake_client)
    explain = orch.explain(ScoreRequest(transaction=_input()))
    # network evidence line + findings should be in the case report
    joined = " ".join(explain.case_report.evidence)
    assert "Network risk score" in joined
    assert "confirmed-fraud" in joined
    # anti-hallucination crosscheck must not flag payload numbers
    assert explain.case_report.crosschecked is True
    assert explain.case_report.hallucination_flagged is False


def test_network_typology_overrides_pattern_when_dominant(fake_client: PipelineClient) -> None:
    # graph score dominates the (low) supervised/anomaly scores
    fake_client.network_risk = 0.7  # type: ignore[attr-defined]
    fake_client.network_available = True  # type: ignore[attr-defined]
    fake_client.fraud = 0.1  # type: ignore[attr-defined]
    fake_client.anomaly = 0.1  # type: ignore[attr-defined]
    explain = _orch(fake_client).explain(ScoreRequest(transaction=_input()))
    assert "Network-connected risk" in explain.case_report.pattern_match


def test_network_observed_after_score(fake_client: PipelineClient) -> None:
    # graph_observe should be invoked best-effort; expose a counter via the fake.
    fake_client.network_available = True  # type: ignore[attr-defined]
    _orch(fake_client).score(ScoreRequest(transaction=_input()))
    assert fake_client.graph_calls == 1  # type: ignore[attr-defined]


def test_low_network_keeps_passing_pipeline(fake_client: PipelineClient) -> None:
    # default fake: network unavailable → behaves like the old 2-axis pipeline.
    resp = _orch(fake_client).score(ScoreRequest(transaction=_input()))
    assert resp.decision == Decision.PASS
    assert resp.risk_level == RiskLevel.LOW
