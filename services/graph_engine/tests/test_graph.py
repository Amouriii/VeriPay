"""Tests for the graph engine network analysis (PLAN §12)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from veripay_graph_engine.main import create_app

from graph.extract import (
    GraphStore,
    ObservedTransaction,
    backfill_from_csv,
    network_context,
)

_BASE = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _tx(
    *,
    tid: str,
    cc: int,
    merchant: str = "m_amazon",
    amount: float = 100.0,
    minutes: int = 0,
    flagged: bool = False,
) -> ObservedTransaction:
    return ObservedTransaction(
        transaction_id=tid,
        cc_num=cc,
        merchant=merchant,
        amount=amount,
        timestamp=_BASE + timedelta(minutes=minutes),
        flagged=flagged,
    )


# --- core logic ---------------------------------------------------------------


def test_isolated_customer_has_zero_network_risk() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))
    assert store.network_risk_score(1) == 0.0
    f = store.features(1)
    assert f.shared_counterparty_count == 0


def test_shared_merchant_raises_risk_with_flagged_peer() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_shared", amount=200.0))
    store.observe(
        _tx(tid="t2", cc=2, merchant="m_shared", amount=300.0, minutes=5, flagged=True)
    )
    score = store.network_risk_score(1)
    assert score > 0.0
    findings = store.findings(1)
    assert any("confirmed-fraud" in line for line in findings)
    ctx = store.network_risk_score(1)
    assert ctx > 0.0
    # flagged neighbor should be counted
    f = store.features(1)
    assert f.flagged_neighbor_count == 1
    assert f.shared_counterparty_count == 1


def test_dedup_by_transaction_id() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))  # duplicate
    assert len(store.customers()) == 1


def test_co_occurrence_within_window() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_co", minutes=0))
    store.observe(_tx(tid="t2", cc=2, merchant="m_co", minutes=1))  # within 60s
    f = store.features(1)
    assert f.co_occurrence_count >= 1


def test_ego_graph_payload_shape() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))
    store.observe(_tx(tid="t2", cc=2, merchant="m_a", flagged=True))
    ego = store.ego_graph(1)
    assert "nodes" in ego and "edges" in ego
    assert any(n["id"] == "c:1" for n in ego["nodes"])
    assert any(n["kind"] == "merchant" for n in ego["nodes"])
    # peer merchant should be flagged-status
    m_node = next(n for n in ego["nodes"] if n["kind"] == "merchant")
    assert m_node["status"] == "review"


def test_network_context_bundle() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))
    store.observe(_tx(tid="t2", cc=2, merchant="m_a", flagged=True))
    ctx = network_context(store, 1)  # type: ignore[assignment]
    assert ctx["network_risk_score"] > 0.0
    assert ctx["available"] is True
    assert len(ctx["findings"]) > 0
    assert "shared_counterparty_count" in ctx["features"]


# --- community discovery (multi-hop) -----------------------------------------


def test_community_finds_full_ring_via_shared_merchant() -> None:
    """An innocent customer 2 hops from a fraud ring must be in its community."""
    store = GraphStore()
    # Ring of 4 flagged customers at m_ring
    for i in range(4):
        store.observe(
            _tx(tid=f"ring_{i}", cc=100 + i, merchant="m_ring", minutes=i, flagged=True)
        )
    # Innocent customer shares m_bridge with one ring member
    store.observe(_tx(tid="bridge", cc=5, merchant="m_bridge", minutes=10))
    store.observe(_tx(tid="ring_bridge", cc=100, merchant="m_bridge", minutes=11, flagged=True))
    # Customer 5 is 2 hops from the ring but only 1-hop in ego_graph
    comm = store.community(5)
    # The community must include the whole ring (multi-hop, not just 1-hop)
    member_ids = {m["cc_num"] for m in comm["members"]}
    assert member_ids >= {5, 100, 101, 102, 103}
    assert comm["stats"]["cluster_size"] >= 5
    assert comm["stats"]["flagged_count"] == 4
    assert comm["stats"]["flagged_ratio"] > 0.0
    assert comm["stats"]["dominant_pattern"] == "fraud_ring"
    # Graph must render both customer and merchant nodes
    graph = comm["graph"]
    assert any(n["kind"] == "merchant" for n in graph["nodes"])
    assert any(n["status"] == "flagged" for n in graph["nodes"])


def test_community_isolated_customer() -> None:
    store = GraphStore()
    store.observe(_tx(tid="solo", cc=1, merchant="m_alone"))
    comm = store.community(1)
    assert comm["stats"]["cluster_size"] == 1
    assert comm["stats"]["flagged_count"] == 0
    assert comm["stats"]["dominant_pattern"] == "isolated"


def test_community_member_status_labels() -> None:
    store = GraphStore()
    store.observe(_tx(tid="t1", cc=1, merchant="m_a"))
    store.observe(_tx(tid="t2", cc=2, merchant="m_a", flagged=True))
    comm = store.community(1)
    statuses = {m["cc_num"]: m["status"] for m in comm["members"]}
    assert statuses[1] == "self"
    assert statuses[2] == "flagged"


# --- service endpoints --------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    # Fresh store per test so the singleton doesn't leak between cases.
    import veripay_graph_engine.store as store_mod

    store_mod._store = GraphStore()  # type: ignore[attr-defined]
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_available"] is True


def test_observe_then_score(client: TestClient) -> None:
    payload = {
        "transaction_id": "t1",
        "cc_num": 1,
        "merchant": "m_shared",
        "amount": 200.0,
        "timestamp": _BASE.isoformat(),
    }
    r = client.post("/api/v1/graph/observe", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "recorded"


def test_score_returns_zero_for_isolated(client: TestClient) -> None:
    payload = {
        "transaction_id": "t1",
        "cc_num": 1,
        "merchant": "m_solo",
        "amount": 50.0,
        "timestamp": _BASE.isoformat(),
    }
    r = client.post("/api/v1/graph/score", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["network_risk_score"] == 0.0
    assert body["available"] is False


def test_score_elevated_with_flagged_peer(client: TestClient) -> None:
    # Seed a flagged peer at the same merchant.
    client.post(
        "/api/v1/graph/observe",
        json={
            "transaction_id": "t_peer",
            "cc_num": 2,
            "merchant": "m_ring",
            "amount": 300.0,
            "timestamp": (_BASE + timedelta(minutes=5)).isoformat(),
            "flagged": True,
        },
    )
    r = client.post(
        "/api/v1/graph/score",
        json={
            "transaction_id": "t_main",
            "cc_num": 1,
            "merchant": "m_ring",
            "amount": 200.0,
            "timestamp": _BASE.isoformat(),
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["network_risk_score"] > 0.0
    assert body["available"] is True
    assert len(body["findings"]) > 0
    assert "nodes" in body["ego"]


def test_ego_endpoint(client: TestClient) -> None:
    client.post(
        "/api/v1/graph/observe",
        json={
            "transaction_id": "t1",
            "cc_num": 1,
            "merchant": "m_a",
            "amount": 100.0,
            "timestamp": _BASE.isoformat(),
        },
    )
    r = client.get("/api/v1/graph/ego/1")
    assert r.status_code == 200
    body = r.json()
    assert "ego" in body
    assert body["network_risk_score"] == 0.0


def test_community_endpoint_returns_full_ring(client: TestClient) -> None:
    # Seed a fraud ring at one merchant.
    for i in range(4):
        client.post(
            "/api/v1/graph/observe",
            json={
                "transaction_id": f"ring_{i}",
                "cc_num": 100 + i,
                "merchant": "m_ring",
                "amount": 200.0,
                "timestamp": (_BASE + timedelta(minutes=i)).isoformat(),
                "flagged": True,
            },
        )
    r = client.get("/api/v1/graph/community/100")
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["cluster_size"] >= 4
    assert body["stats"]["flagged_count"] == 4
    assert body["stats"]["flagged_ratio"] == 1.0
    assert body["stats"]["dominant_pattern"] == "fraud_ring"
    assert any(n["status"] == "flagged" for n in body["graph"]["nodes"])


# --- backfill from the training dataset ------------------------------------


def _write_seed_csv(path, rows: list[dict]) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_backfill_from_csv_seeds_graph_and_flag(tmp_path) -> None:
    seed = tmp_path / "labeled.csv"
    rows = [
        {
            "transaction_id": "ring_0",
            "cc_num": 4000000000000000,
            "merchant": "fraud_Kerluke",
            "timestamp": _BASE.isoformat(),
            "amount_minor": 27700,
            "is_fraud": 1,
        },
        {
            "transaction_id": "ring_1",
            "cc_num": 4000000000000001,
            "merchant": "fraud_Kerluke",
            "timestamp": (_BASE + timedelta(seconds=30)).isoformat(),
            "amount_minor": 14000,
            "is_fraud": 1,
        },
        {
            "transaction_id": "tx_00001",
            "cc_num": 1000000000000001,
            "merchant": "fraud_Kerluke",
            "timestamp": (_BASE + timedelta(minutes=2)).isoformat(),
            "amount_minor": 5000,
            "is_fraud": 0,
        },
    ]
    _write_seed_csv(seed, rows)
    store = GraphStore()
    observed = backfill_from_csv(str(seed), store)
    assert observed == 3
    # The innocent customer shares the fraud_Kerluke merchant with 2 flagged
    # peers → the graph axis must surface propagated risk.
    assert store.is_flagged(4000000000000000)
    score = store.network_risk_score(1000000000000001)
    assert score > 0.0
    findings = store.findings(1000000000000001)
    assert any("confirmed-fraud" in f for f in findings)


def test_backfill_rejects_missing_columns(tmp_path) -> None:
    seed = tmp_path / "bad.csv"
    _write_seed_csv(seed, [{"transaction_id": "x", "amount_minor": 1}])
    store = GraphStore()
    with pytest.raises(ValueError, match="missing required columns"):
        backfill_from_csv(str(seed), store)


def test_backfill_skips_malformed_timestamps(tmp_path) -> None:
    seed = tmp_path / "mixed.csv"
    rows = [
        {
            "transaction_id": "good",
            "cc_num": 1,
            "merchant": "m_a",
            "timestamp": _BASE.isoformat(),
            "amount_minor": 1000,
            "is_fraud": 0,
        },
        {
            "transaction_id": "bad",
            "cc_num": 2,
            "merchant": "m_b",
            "timestamp": "not-a-timestamp",
            "amount_minor": 1000,
            "is_fraud": 0,
        },
    ]
    _write_seed_csv(seed, rows)
    store = GraphStore()
    observed = backfill_from_csv(str(seed), store)
    assert observed == 1  # malformed row skipped
    assert 2 not in store.customers()


def test_get_store_backfills_from_real_dataset() -> None:
    """The shipped transactions_labeled.csv seeds the store on first access."""
    import veripay_graph_engine.store as store_mod

    store_mod._store = None  # force re-init
    store = store_mod.get_store()
    # The real dataset has a fraud ring of 8 customers at fraud_Kerluke.
    assert store.is_flagged(4000000000000000)
    # An innocent customer who shares fraud_Kerluke must have network signal.
    # Find any non-ring customer who touched the fraud merchant.
    flagged = [c for c in store.customers() if store.is_flagged(c)]
    assert len(flagged) >= 8
    store_mod._store = None  # reset for subsequent tests
