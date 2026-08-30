"""Test bootstrap for the graph engine.

The ``graph`` module (from ``ml/``, installed as ``veripay-ml``) is made
importable on sys.path so tests resolve ``graph.extract`` without a full
``make install``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))
