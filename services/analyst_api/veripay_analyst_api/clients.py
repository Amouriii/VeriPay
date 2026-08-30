"""HTTP client boundary for the downstream scoring/decision services.

Uses only the standard library (``urllib``) so the analyst API stays dependency
light and mirrors how the model monitor, demo driver, and Compose healthchecks
already talk to services. Consumers inject their own ``PipelineClient`` in
tests.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

from veripay_analyst_api.config import Settings


class PipelineClient(Protocol):
    """The subset of downstream endpoints the analyst pipeline depends on."""

    def supervised_score(
        self, transaction_id: str, features: dict[str, float]
    ) -> dict[str, Any]: ...

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]: ...

    def fuse_risk(
        self, transaction_id: str, components: list[dict[str, Any]]
    ) -> dict[str, Any]: ...

    def decide(self, request: dict[str, Any]) -> dict[str, Any]: ...

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]: ...

    def retrain(self, version: str | None = None) -> dict[str, Any]: ...

    def append_feedback(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def record_monitor_label(self, transaction_id: str, label: str) -> dict[str, Any]: ...

    def graph_score(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def graph_observe(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def graph_ego(self, cc_num: int) -> dict[str, Any]: ...

    def graph_community(self, cc_num: int) -> dict[str, Any]: ...

    def health(self) -> dict[str, dict[str, Any]]: ...


class HttpPipelineClient:
    """Concrete client that calls each service over REST."""

    def __init__(self, settings: Settings | None = None) -> None:
        conf = settings or Settings()
        self._urls = {
            "supervised": conf.SUPERVISED_URL,
            "anomaly": conf.ANOMALY_URL,
            "risk_fusion": conf.RISK_FUSION_URL,
            "decision": conf.DECISION_URL,
            "investigation": conf.INVESTIGATION_URL,
            "feedback": conf.FEEDBACK_URL,
            "model_monitor": conf.MODEL_MONITOR_URL,
            "graph": conf.GRAPH_URL,
        }

    def _post(
        self,
        name: str,
        path: str,
        payload: dict[str, Any],
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        base = self._urls[name]
        request = urllib.request.Request(
            f"{base}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def _get(self, name: str, path: str, *, timeout: float = 10.0) -> dict[str, Any]:
        base = self._urls[name]
        with urllib.request.urlopen(f"{base}{path}", timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def append_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("feedback", "/api/v1/feedback", payload)

    def record_monitor_label(self, transaction_id: str, label: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"transaction_id": transaction_id, "label": label})
        return self._post("model_monitor", f"/api/v1/monitor/feedback?{query}", {})

    def graph_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("graph", "/api/v1/graph/score", payload)

    def graph_observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("graph", "/api/v1/graph/observe", payload)

    def graph_community(self, cc_num: int) -> dict[str, Any]:
        return self._get("graph", f"/api/v1/graph/community/{cc_num}")

    def graph_ego(self, cc_num: int) -> dict[str, Any]:
        return self._get("graph", f"/api/v1/graph/ego/{cc_num}")

    def supervised_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        return self._post(
            "supervised", "/api/v1/score", {"transaction_id": transaction_id, "features": features}
        )

    def anomaly_score(self, transaction_id: str, features: dict[str, float]) -> dict[str, Any]:
        return self._post(
            "anomaly", "/api/v1/score", {"transaction_id": transaction_id, "features": features}
        )

    def fuse_risk(self, transaction_id: str, components: list[dict[str, Any]]) -> dict[str, Any]:
        return self._post(
            "risk_fusion",
            "/api/v1/risk/fuse",
            {"transaction_id": transaction_id, "components": components},
        )

    def decide(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._post("decision", "/api/v1/decision/evaluate", request)

    def investigate(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._post("investigation", "/api/v1/investigate", request)

    def retrain(self, version: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if version is not None:
            body["version"] = version
        return self._post("model_monitor", "/api/v1/monitor/retrain", body)

    def health(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name in ("supervised", "anomaly", "investigation", "feedback"):
            try:
                result[name] = self._get(name, "/health")
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                json.JSONDecodeError,
            ):
                result[name] = {"status": "unavailable"}
        return result
