"""Module-level graph store for the graph engine service (PLAN §12).

A process-singleton ``GraphStore`` (from ``ml/graph/extract.py``) accumulated
from observed transactions, mirroring the in-memory convention of
``analyst_api.ProfileStore``. On first access the store is backfilled from the
labeled dataset so every customer's full merchant history is present, not just
transactions that flowed through the analyst API. A real deployment would
persist to the customer Postgres; the prototype keeps it in memory.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

# The ``ml`` package is installed as ``veripay-ml`` and its modules are
# top-level (e.g. ``graph.extract``, not ``ml.graph.extract``). We deliberately
# avoid adding a veripay-ml runtime dependency to the service's pyproject so
# the service stays dependency-light; the monorepo layout provides the module.
_ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

from graph.extract import GraphStore, backfill_from_csv  # noqa: E402
from veripay_graph_engine.config import settings  # noqa: E402

_store: GraphStore | None = None


def get_store() -> GraphStore:
    """Return the process-wide graph store, lazily initialised.

    On first access the store is backfilled from the labeled dataset
    (``VERIPAY_GRAPH_SEED_CSV``) so every customer's full merchant history is
    present, not just transactions that flowed through the analyst API. This
    means the graph axis has signal from the very first score instead of
    warming up transaction-by-transaction.
    """
    global _store
    if _store is None:
        _store = GraphStore()
        seed_csv = settings.GRAPH_SEED_CSV
        if seed_csv:
            # No dataset on disk yet (e.g. a fresh clone before
            # ``python ml/datasets/generate_synthetic.py`` ran) → the store
            # warms up from observed transactions instead of failing boot.
            with contextlib.suppress(FileNotFoundError, ValueError):
                backfill_from_csv(seed_csv, _store)
    return _store
