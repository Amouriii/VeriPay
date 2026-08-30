"""VeriPay Analyst API.

Composite, analyst-facing boundary that wires the existing scoring, fusion,
decision, investigation, feedback, and monitoring services behind the
single ergonomic surface described by the system architecture: ``/score``,
``/explain``, ``/customer/{cc_num}/profile``, ``/feedback``,
``/feedback/stats``, ``/retrain`` and ``/health``.

It also applies the live, per-transaction feedback and drift score adjustments
that the architecture document assigns to the score-adjustment stage.
"""

from veripay_analyst_api.config import settings
from veripay_analyst_api.service import create_orchestrator

__all__ = ["create_orchestrator", "settings"]
