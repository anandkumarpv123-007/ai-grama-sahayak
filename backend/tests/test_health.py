import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_status_code_and_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-grama-sahayak"
    assert data["version"] == "1.0.0"
