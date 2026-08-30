from fastapi.testclient import TestClient
from veripay_external_context.main import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
