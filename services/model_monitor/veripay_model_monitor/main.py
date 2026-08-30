"""HTTP entry point for the model monitor. PLAN §10, §21."""

from __future__ import annotations

from fastapi import FastAPI

from veripay_model_monitor.config import settings
from veripay_model_monitor.service import (
    MonitorLabel,
    Observation,
    ObservationStore,
    Retrainer,
    SubprocessRetrainer,
    WindowedObservationStore,
    drift_report,
    load_reference_profile,
    retrain_and_promote,
)


def create_app(
    store: ObservationStore | None = None,
    retrainer: Retrainer | None = None,
    feedback_labels: dict[str, str] | None = None,
) -> FastAPI:
    """Build the monitoring API with injectable boundaries for tests."""
    app = FastAPI(title="veripay-model_monitor", version="0.1.0")
    observation_store = store or WindowedObservationStore()
    active_retrainer = retrainer or SubprocessRetrainer(settings.REPO_ROOT, settings.PYTHON)
    local_labels: dict[str, str] = dict(feedback_labels or {})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veripay-model_monitor"}

    @app.post("/api/v1/monitor/observations", response_model=Observation)
    def record_observation(observation: Observation) -> Observation:
        return observation_store.add(observation)

    @app.get("/api/v1/monitor/observations", response_model=list[Observation])
    def list_observations() -> list[Observation]:
        return observation_store.list()

    @app.post("/api/v1/monitor/feedback", response_model=dict[str, str])
    def record_feedback(transaction_id: str, label: MonitorLabel) -> dict[str, str]:
        local_labels[transaction_id] = str(label)
        return {"transaction_id": transaction_id, "label": str(label)}

    @app.get("/api/v1/monitor/drift")
    def drift() -> dict:
        profile = load_reference_profile(
            settings.REGISTRY_PATH, settings.MODEL_NAME, model_dir=settings.MODEL_DIR
        )
        observations = observation_store.list()
        if profile is None:
            return {
                "verdict": "NO_REFERENCE_PROFILE",
                "model_name": settings.MODEL_NAME,
                "window_size": len(observations),
                "detail": "train the model first (ml/supervised/train.py) to create a profile",
            }
        report = drift_report(
            profile,
            observations,
            min_window=settings.MIN_DRIFT_WINDOW,
            psi_threshold=settings.PSI_THRESHOLD,
        )
        return {
            "model_name": settings.MODEL_NAME,
            "reference_version": profile.get("version"),
            **report,
        }

    @app.post("/api/v1/monitor/retrain")
    def retrain(version: str | None = None) -> dict:
        return retrain_and_promote(
            observations=observation_store.list(),
            feedback_labels=local_labels,
            retrainer=active_retrainer,
            base_dataset=settings.BASE_DATASET,
            model_name=settings.MODEL_NAME,
            model_dir=settings.MODEL_DIR,
            registry_path=settings.REGISTRY_PATH,
            min_labels=settings.MIN_LABELED_OBSERVATIONS,
            tolerance=settings.PROMOTION_TOLERANCE,
            version=version,
        )

    return app


app = create_app()


def main() -> None:
    """Run the HTTP service."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT)  # pragma: no cover


if __name__ == "__main__":
    main()
