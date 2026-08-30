"""Extract graph / coordinated-fraud features (PLAN §12).

Pure-stdlib (no networkx dependency) prototype implementation of the network
analysis described in ``docs/network-analysis.md``. The ``ml`` package is
installed as ``veripay-ml`` and its modules are top-level (``graph`` not
``ml.graph``); the service mirrors that import path.

The Sparkov dataset the current prototype runs on does not carry beneficiary
account IDs, device fingerprints, or IP addresses, so the full beneficiary-
level mule graph is not buildable. Per the document's own *prototype approach*
we build what the available data *does* support: a customer ↔ merchant
bipartite graph projected onto a customer ↔ customer "shared merchant" graph,
plus temporal co-occurrence and feedback-flag propagation (confirmed-fraud
customers seed risk that propagates to peers sharing their merchants).

The same module backs the ``graph_engine`` service (runtime scoring) and the
``analyst_api`` composite (explanation context), and is unit-tested directly.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

# How close two transactions at the same merchant must be (in seconds) to count
# as a temporal co-occurrence — a proxy for coordinated activity.
CO_OCCURRENCE_WINDOW_SECONDS = 60.0

# A customer is considered "flagged" when at least this many of their recorded
# transactions carry a flagged=True marker (or a confirmed-fraud label).
FLAGGED_TXN_THRESHOLD = 1

# Safety cap on community discovery so the prototype stays fast on large graphs.
COMMUNITY_MAX_NODES = 500

# Weights for the transparent network-risk blend. They sum to 1.0 and are
# documented so an analyst can audit how the score was produced.
WEIGHT_FLAGGED_EXPOSURE = 0.45
WEIGHT_SHARED_COUNTERPARTY = 0.25
WEIGHT_CO_OCCURRENCE = 0.15
WEIGHT_MERCHANT_FAN_IN = 0.15


@dataclass(frozen=True)
class ObservedTransaction:
    """A transaction recorded into the graph store.

    ``flagged`` marks transactions whose customer is confirmed-fraud (from the
    analyst feedback loop); these seed risk that propagates to connected peers.
    """

    transaction_id: str
    cc_num: int
    merchant: str
    amount: float
    timestamp: datetime
    location: tuple[float, float] | None = None
    flagged: bool = False


@dataclass
class NodeFeatures:
    """Per-customer graph features (the document's node-level feature table)."""

    merchant_degree: int = 0  # distinct merchants (out-degree proxy)
    merchant_fan_in: int = 0  # distinct customers at this customer's merchants
    shared_counterparty_count: int = 0  # other customers sharing >=1 merchant
    co_occurrence_count: int = 0  # same-merchant ±60s peers
    flagged_neighbor_count: int = 0  # shared peers that are confirmed-fraud
    flagged_exposure: float = 0.0  # flagged_neighbor_count / max(1, shared)
    cluster_size: int = 1  # connected-component size over shared-merchant graph
    cluster_flagged_ratio: float = 0.0  # flagged fraction of the component


@dataclass
class GraphStore:
    """In-memory customer ↔ merchant bipartite graph + projections."""

    _txns: dict[str, ObservedTransaction] = field(default_factory=dict)
    # customer -> set(merchant)
    _customer_merchants: dict[int, set[str]] = field(default_factory=dict)
    # merchant -> set(customer)
    _merchant_customers: dict[str, set[int]] = field(default_factory=dict)
    # merchant -> list[(timestamp, cc_num, txn_id)]  (kept for co-occurrence)
    _merchant_events: dict[str, list[tuple[datetime, int, str]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # customer -> flagged tx count
    _flagged_count: dict[int, int] = field(default_factory=lambda: defaultdict(int))

    # ------------------------------------------------------------------ observe
    def observe(self, tx: ObservedTransaction) -> None:
        """Record a transaction, deduplicating by transaction_id.

        Dedup matters because the analyst ``/explain`` path re-scores (and thus
        re-observes) the same transaction; we must not inflate the graph.
        """
        if tx.transaction_id in self._txns:
            return
        self._txns[tx.transaction_id] = tx
        self._customer_merchants.setdefault(tx.cc_num, set()).add(tx.merchant)
        self._merchant_customers.setdefault(tx.merchant, set()).add(tx.cc_num)
        self._merchant_events[tx.merchant].append((tx.timestamp, tx.cc_num, tx.transaction_id))
        if tx.flagged:
            self._flagged_count[tx.cc_num] += 1

    def is_flagged(self, cc_num: int) -> bool:
        return self._flagged_count.get(cc_num, 0) >= FLAGGED_TXN_THRESHOLD

    def customers(self) -> list[int]:
        return list(self._customer_merchants.keys())

    def merchants_for(self, cc_num: int) -> set[str]:
        return set(self._customer_merchants.get(cc_num, set()))

    # ------------------------------------------------------------------ features
    def features(self, cc_num: int, *, window_days: int | None = None) -> NodeFeatures:
        """Compute the node feature vector for ``cc_num``.

        ``window_days`` restricts the graph to transactions within that many
        days of the customer's most recent transaction (None = all history).
        """
        merchants = self._scoped_merchants(cc_num, window_days)
        if not merchants:
            return NodeFeatures()

        merchant_degree = len(merchants)
        # Distinct *other* customers seen at this customer's merchants.
        peers: set[int] = set()
        fan_in = 0
        for m in merchants:
            crowd = self._scoped_customers(m, window_days)
            crowd.discard(cc_num)
            peers |= crowd
            fan_in += len(crowd)
        fan_in = min(fan_in, max(1, merchant_degree) * 1000)  # bounded sum

        flagged_neighbors = {p for p in peers if self.is_flagged(p)}
        shared = len(peers)
        flagged_exposure = len(flagged_neighbors) / shared if shared else 0.0

        co_occurrence = self._co_occurrence(cc_num, merchants, window_days)

        cluster_size, cluster_flagged_ratio = self._component_stats(cc_num, window_days)

        return NodeFeatures(
            merchant_degree=merchant_degree,
            merchant_fan_in=fan_in,
            shared_counterparty_count=shared,
            co_occurrence_count=co_occurrence,
            flagged_neighbor_count=len(flagged_neighbors),
            flagged_exposure=round(flagged_exposure, 4),
            cluster_size=cluster_size,
            cluster_flagged_ratio=round(cluster_flagged_ratio, 4),
        )

    # ------------------------------------------------------------------ score
    def network_risk_score(self, cc_num: int, *, window_days: int | None = None) -> float:
        """Transparent 0..1 blend of the node features.

        Dominated by flagged-exposure (propagated confirmed-fraud risk) and the
        breadth of shared counterparties; co-occurrence and merchant fan-in add
        smaller increments. Returns 0.0 when the customer is isolated (no
        shared merchants with anyone), so the fusion layer can mark the axis
        unavailable without distorting the score.
        """
        f = self.features(cc_num, window_days=window_days)
        if f.shared_counterparty_count == 0:
            return 0.0

        # Saturating transforms: diminishing returns past a handful of peers.
        flagged = min(1.0, f.flagged_exposure)
        shared = min(1.0, f.shared_counterparty_count / 5.0)
        co_occ = min(1.0, f.co_occurrence_count / 3.0)
        fan = min(1.0, f.merchant_fan_in / 10.0)

        score = (
            WEIGHT_FLAGGED_EXPOSURE * flagged
            + WEIGHT_SHARED_COUNTERPARTY * shared
            + WEIGHT_CO_OCCURRENCE * co_occ
            + WEIGHT_MERCHANT_FAN_IN * fan
        )
        return round(min(1.0, max(0.0, score)), 4)

    # ------------------------------------------------------------------ findings
    def findings(self, cc_num: int, *, window_days: int | None = None) -> list[str]:
        """Analyst-readable indicator strings, each citing store-derived numbers."""
        f = self.features(cc_num, window_days=window_days)
        out: list[str] = []
        if f.flagged_neighbor_count:
            out.append(
                f"Shares merchant(s) with {f.flagged_neighbor_count} confirmed-fraud "
                f"account(s) (flagged exposure {f.flagged_exposure:.0%})."
            )
        if f.shared_counterparty_count:
            out.append(
                f"Connected to {f.shared_counterparty_count} other customer(s) via "
                f"{f.merchant_degree} shared merchant(s)."
            )
        if f.co_occurrence_count:
            out.append(
                f"{f.co_occurrence_count} temporal co-occurrence(s) — peer "
                f"transaction(s) at the same merchant within "
                f"{int(CO_OCCURRENCE_WINDOW_SECONDS)}s."
            )
        if f.cluster_flagged_ratio:
            out.append(
                f"Community of {f.cluster_size} account(s) with a "
                f"{f.cluster_flagged_ratio:.0%} confirmed-fraud ratio."
            )
        return out

    # ------------------------------------------------------------------ ego
    def ego_graph(
        self, cc_num: int, *, window_days: int | None = None, limit: int = 24
    ) -> dict[str, Any]:
        """Dashboard payload: customer center + merchant + peer nodes + edges."""
        merchants = sorted(self._scoped_merchants(cc_num, window_days))
        nodes: list[dict[str, Any]] = [
            {"id": f"c:{cc_num}", "kind": "customer", "label": str(cc_num), "status": "self"}
        ]
        edges: list[dict[str, Any]] = []
        peer_set: set[int] = set()
        for m in merchants:
            crowd = self._scoped_customers(m, window_days)
            crowd.discard(cc_num)
            status = "review" if any(self.is_flagged(p) for p in crowd) else "normal"
            nodes.append({"id": f"m:{m}", "kind": "merchant", "label": m, "status": status})
            vol = self._edge_volume(cc_num, m, window_days)
            edges.append({"from": f"c:{cc_num}", "to": f"m:{m}", "weight": round(vol, 2)})
            peer_set |= crowd

        # Cap peer nodes rendered to keep the ego graph legible.
        for p in sorted(peer_set)[: max(0, limit - len(merchants) - 1)]:
            status = "flagged" if self.is_flagged(p) else "normal"
            nodes.append({"id": f"c:{p}", "kind": "customer", "label": str(p), "status": status})
            # connect peer to first shared merchant
            shared_merchants = self._scoped_merchants(cc_num, window_days)
            shared = sorted(shared_merchants & self._scoped_merchants(p, window_days))
            if shared:
                edges.append({"from": f"c:{p}", "to": f"m:{shared[0]}", "weight": 1.0})
        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------ community
    def community_graph(
        self,
        cc_num: int,
        *,
        window_days: int | None = None,
        node_limit: int = 60,
    ) -> dict[str, Any]:
        """Full multi-hop community around ``cc_num`` for the dashboard.

        Unlike ``ego_graph`` (1-hop peers only), this renders the entire
        connected component of the shared-merchant projection the customer
        belongs to — the Louvain-style community — with aggregate cluster
        stats so an analyst can see the whole fraud ring at once.
        """
        members = self._community_members(cc_num, window_days)
        if not members:
            members = {cc_num}
        members = set(sorted(members)[:node_limit])  # cap rendered nodes

        # Collect every merchant touched by any member, with per-merchant stats.
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        merchant_members: dict[str, set[int]] = defaultdict(set)
        for c in members:
            status = "self" if c == cc_num else ("flagged" if self.is_flagged(c) else "normal")
            nodes.append({"id": f"c:{c}", "kind": "customer", "label": str(c), "status": status})
        # Merchant nodes that connect >=2 members (the ring's shared merchants).
        merchants_seen: set[str] = set()
        for c in members:
            for m in self._scoped_merchants(c, window_days):
                merchants_seen.add(m)
                merchant_members[m].add(c)
        for m in sorted(merchants_seen):
            crowd = merchant_members[m] & members
            if len(crowd) < 1:
                continue
            status = "review" if any(self.is_flagged(p) for p in crowd) else "normal"
            nodes.append({"id": f"m:{m}", "kind": "merchant", "label": m, "status": status})
            for c in crowd:
                vol = self._edge_volume(c, m, window_days)
                edges.append({"from": f"c:{c}", "to": f"m:{m}", "weight": round(vol, 2)})
        return {"nodes": nodes, "edges": edges}

    def community(
        self, cc_num: int, *, window_days: int | None = None, node_limit: int = 60
    ) -> dict[str, Any]:
        """Community payload: full graph + aggregate cluster stats.

        Aggregates: cluster size, flagged count + ratio, distinct shared
        merchants, total volume across the cluster, and the member list with
        each member's status — the fraud-ring overview an investigator needs.
        """
        members = self._community_members(cc_num, window_days)
        if not members:
            members = {cc_num}
        flagged_members = [c for c in members if self.is_flagged(c)]
        shared_merchants: set[str] = set()
        total_volume = 0.0
        for c in members:
            for m in self._scoped_merchants(c, window_days):
                shared_merchants.add(m)
                total_volume += self._edge_volume(c, m, window_days)
        return {
            "graph": self.community_graph(cc_num, window_days=window_days, node_limit=node_limit),
            "stats": {
                "cluster_size": len(members),
                "flagged_count": len(flagged_members),
                "flagged_ratio": round(len(flagged_members) / max(1, len(members)), 4),
                "distinct_shared_merchants": len(shared_merchants),
                "total_volume": round(total_volume, 2),
                "dominant_pattern": self._community_pattern(
                    members, flagged_members, shared_merchants
                ),
            },
            "members": [
                {
                    "cc_num": c,
                    "status": (
                        "self" if c == cc_num else "flagged" if self.is_flagged(c) else "normal"
                    ),
                }
                for c in sorted(members)[:node_limit]
            ],
        }

    def _community_pattern(
        self,
        members: set[int],
        flagged_members: list[int],
        shared_merchants: set[str],
    ) -> str:
        """Human-readable typology label for the cluster."""
        if not members or len(members) <= 1:
            return "isolated"
        flagged_ratio = len(flagged_members) / len(members)
        if flagged_ratio >= 0.5 and len(members) >= 3:
            return "fraud_ring"
        if flagged_ratio > 0 and flagged_ratio < 0.5:
            return "mixed_cluster"
        if len(shared_merchants) == 1 and len(members) >= 3:
            return "shared_merchant_collapse"
        return "normal_cluster"

    # ------------------------------------------------------------------ helpers
    def _cutoff(self, window_days: int | None) -> datetime | None:
        if window_days is None:
            return None
        latest = max((t.timestamp for t in self._txns.values()), default=datetime.min)
        return latest - timedelta(days=window_days)

    def _scoped_merchants(self, cc_num: int, window_days: int | None) -> set[str]:
        cutoff = self._cutoff(window_days)
        if cutoff is None:
            return self.merchants_for(cc_num)
        return {
            t.merchant for t in self._txns.values() if t.cc_num == cc_num and t.timestamp >= cutoff
        }

    def _scoped_customers(self, merchant: str, window_days: int | None) -> set[int]:
        cutoff = self._cutoff(window_days)
        if cutoff is None:
            return set(self._merchant_customers.get(merchant, set()))
        return {
            t.cc_num
            for t in self._txns.values()
            if t.merchant == merchant and t.timestamp >= cutoff
        }

    def _edge_volume(self, cc_num: int, merchant: str, window_days: int | None) -> float:
        cutoff = self._cutoff(window_days)
        return sum(
            float(t.amount)
            for t in self._txns.values()
            if t.cc_num == cc_num
            and t.merchant == merchant
            and (cutoff is None or t.timestamp >= cutoff)
        )

    def _co_occurrence(self, cc_num: int, merchants: set[str], window_days: int | None) -> int:
        cutoff = self._cutoff(window_days)
        count = 0
        for m in merchants:
            events = self._merchant_events.get(m, [])
            for ts, cust, _tid in events:
                if cust == cc_num:
                    continue
                if cutoff is not None and ts < cutoff:
                    continue
                # does cc_num have an event at m within the window of this peer event?
                for my_ts, my_cust, _ in events:
                    if my_cust != cc_num:
                        continue
                    if cutoff is not None and my_ts < cutoff:
                        continue
                    if abs((my_ts - ts).total_seconds()) <= CO_OCCURRENCE_WINDOW_SECONDS:
                        count += 1
                        break
        return count

    def _component_stats(self, cc_num: int, window_days: int | None) -> tuple[int, float]:
        """Connected-component size + flagged ratio over the shared-merchant graph."""
        component = self._community_members(cc_num, window_days)
        if not component:
            return 1, 0.0
        flagged_in_component = sum(1 for c in component if self.is_flagged(c))
        ratio = flagged_in_component / len(component)
        return len(component), round(ratio, 4)

    def _community_members(self, cc_num: int, window_days: int | None) -> set[int]:
        """Multi-hop BFS over the shared-merchant projection (label propagation).

        Returns every customer reachable from ``cc_num`` through any chain of
        shared merchants, capped at ``COMMUNITY_MAX_NODES`` for the prototype.
        This is the Louvain-equivalent community: the connected component of
        the bipartite projection that this customer belongs to.
        """
        seen: set[int] = set()
        frontier = {cc_num}
        while frontier:
            nxt: set[int] = set()
            for cust in frontier:
                if cust in seen:
                    continue
                seen.add(cust)
                cust_merchants = self._scoped_merchants(cust, window_days)
                for m in cust_merchants:
                    for peer in self._scoped_customers(m, window_days):
                        if peer != cust and peer not in seen:
                            nxt.add(peer)
            frontier = nxt
            if len(seen) > COMMUNITY_MAX_NODES:
                break
        return seen


def network_context(
    store: GraphStore, cc_num: int, *, window_days: int | None = 30
) -> dict[str, Any]:
    """Bundle the score + findings + ego payload the analyst API / dashboard use."""
    score = store.network_risk_score(cc_num, window_days=window_days)
    findings = store.findings(cc_num, window_days=window_days)
    features = store.features(cc_num, window_days=window_days)
    available = bool(features.shared_counterparty_count)
    return {
        "network_risk_score": score,
        "available": available,
        "findings": findings,
        "features": {
            "merchant_degree": features.merchant_degree,
            "merchant_fan_in": features.merchant_fan_in,
            "shared_counterparty_count": features.shared_counterparty_count,
            "co_occurrence_count": features.co_occurrence_count,
            "flagged_neighbor_count": features.flagged_neighbor_count,
            "flagged_exposure": features.flagged_exposure,
            "cluster_size": features.cluster_size,
            "cluster_flagged_ratio": features.cluster_flagged_ratio,
        },
        "ego": store.ego_graph(cc_num, window_days=window_days),
    }


REQUIRED_BACKFILL_COLUMNS = ("transaction_id", "cc_num", "merchant", "timestamp")


def backfill_from_csv(path: str, store: GraphStore, *, limit: int | None = None) -> int:
    """Load transactions from the labeled dataset into ``store``.

    The same ``datasets/synthetic/transactions_labeled.csv`` used to train the
    supervised/anomaly models now also seeds the graph: every row with a
    ``cc_num`` and ``merchant`` becomes an observed edge, and ``is_fraud=1``
    rows mark that customer as confirmed-fraud (the graph's risk seeds).
    Returns the number of transactions observed.

    Kept pandas-free on the hot path: pandas is only imported lazily so the
    graph engine does not acquire a pandas runtime dependency unless backfill
    is actually enabled.
    """
    import csv  # local import keeps the module stdlib-clean for non-backfill use
    from datetime import datetime

    observed = 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_BACKFILL_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Backfill CSV missing required columns: {missing}")
        for row in reader:
            if limit is not None and observed >= limit:
                break
            try:
                amount = float(row.get("amount_minor") or row.get("amount") or 0.0) / 100.0
            except (TypeError, ValueError):
                amount = 0.0
            flagged = str(row.get("is_fraud", "")).strip() in ("1", "True", "true")
            try:
                ts = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
            except ValueError:
                continue  # skip malformed timestamps rather than fail the seed
            store.observe(
                ObservedTransaction(
                    transaction_id=str(row["transaction_id"]),
                    cc_num=int(row["cc_num"]),
                    merchant=str(row["merchant"]),
                    amount=amount,
                    timestamp=ts,
                    flagged=flagged,
                )
            )
            observed += 1
    return observed
