from fastapi.testclient import TestClient
from veripay_risk_fusion.main import create_app
from veripay_risk_fusion.service import FusionRequest, RiskComponent, fuse_risk


def test_unavailable_component_weight_is_redistributed() -> None:
    result = fuse_risk(
        FusionRequest(
            transaction_id="tx_001",
            components=[
                RiskComponent(component="supervised", score=20, weight=0.75),
                RiskComponent(component="anomaly", score=100, weight=0.25, available=False),
            ],
        )
    )
    assert result.unified_score == 20
    assert result.band == "APPROVE"


def test_all_unavailable_components_fail_closed() -> None:
    result = fuse_risk(
        FusionRequest(
            transaction_id="tx_002",
            components=[RiskComponent(component="model", score=0, weight=1, available=False)],
        )
    )
    assert result.unified_score == 100
    assert result.band == "BLOCK"


def test_fusion_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/risk/fuse",
        json={
            "transaction_id": "tx_003",
            "components": [{"component": "model", "score": 75, "weight": 1}],
        },
    )
    assert response.status_code == 200
    assert response.json()["band"] == "BLOCK"
