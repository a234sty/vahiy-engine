"""Integration tests for the /health endpoint."""

from fastapi.testclient import TestClient

from vahiy_engine.main import app

client = TestClient(app)


def test_health_returns_ok_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
