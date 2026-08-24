"""gRPC clients to downstream services. PLAN §13.

Typed, lazy-imported clients so a service can depend on another's contract
without coupling to its implementation. Generated stubs live in proto/gen/.
"""
from __future__ import annotations


def get_downstream_stub(service_name: str):  # type: ignore[no-untyped-def]
    """Return a gRPC stub for a downstream service. Stubbed."""
    raise NotImplementedError
