import importlib.util
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

has_voice = importlib.util.find_spec("app.api.voice") is not None
has_documents = importlib.util.find_spec("app.api.documents") is not None
has_services = importlib.util.find_spec("app.api.services") is not None
has_grievances = importlib.util.find_spec("app.api.grievances") is not None

AGREED_ENDPOINTS = [
    "/api/health",
    "/api/chat",
    "/api/eligibility/check",
    "/api/voice/transcribe",
    "/api/voice/speak",
    "/api/documents/analyze",
    "/api/services/nearby",
    "/api/grievances/draft",
]


def test_swagger_ui_loads():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower() or "html" in response.headers.get("content-type", "").lower()


def test_redoc_loads():
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower() or "html" in response.headers.get("content-type", "").lower()


def test_openapi_schema_contains_all_eight_agreed_endpoints():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "AI Grama Sahayak"
    paths = data["paths"]

    for endpoint in AGREED_ENDPOINTS:
        assert endpoint in paths, f"Endpoint {endpoint} missing from registered OpenAPI paths"


@pytest.mark.skipif(has_voice, reason="Member 3 voice router is integrated; placeholder not active")
def test_voice_transcribe_placeholder_returns_503():
    """Placeholder must return 503 Service Unavailable, never fabricate transcriptions."""
    import io
    file_content = io.BytesIO(b"fake audio data")
    response = client.post(
        "/api/voice/transcribe",
        files={"file": ("sample.wav", file_content, "audio/wav")},
        data={"language": "te"},
    )
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "unavailable" in data["error"]["message"].lower()


@pytest.mark.skipif(has_voice, reason="Member 3 voice router is integrated; placeholder not active")
def test_voice_speak_placeholder_returns_503():
    """Placeholder must return 503 Service Unavailable, never fabricate audio."""
    payload = {"text": "నమస్కారం", "language": "te"}
    response = client.post("/api/voice/speak", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "unavailable" in data["error"]["message"].lower()


@pytest.mark.skipif(has_documents, reason="Member 4 documents router is integrated; placeholder not active")
def test_documents_analyze_placeholder_returns_503():
    """Placeholder must return 503 Service Unavailable, never fabricate document analysis."""
    import io
    file_content = io.BytesIO(b"%PDF-1.4 mock pdf content")
    response = client.post(
        "/api/documents/analyze",
        files={"file": ("doc.pdf", file_content, "application/pdf")},
        data={"document_type": "aadhaar"},
    )
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "unavailable" in data["error"]["message"].lower()


@pytest.mark.skipif(has_services, reason="Member 4 services router is integrated; placeholder not active")
def test_services_nearby_placeholder_returns_503():
    """Placeholder must return 503 Service Unavailable, never fabricate nearby services."""
    response = client.get("/api/services/nearby?district=Kakinada&service_type=csc")
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "unavailable" in data["error"]["message"].lower()


@pytest.mark.skipif(has_grievances, reason="Member 4 grievances router is integrated; placeholder not active")
def test_grievances_draft_placeholder_returns_503():
    """Placeholder must return 503 Service Unavailable, never fabricate grievances."""
    payload = {
        "category": "water_supply",
        "description": "Drinking water pipeline leak in village main street",
        "district": "Kakinada",
        "mandal": "Samalkota",
        "language": "en",
    }
    response = client.post("/api/grievances/draft", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "unavailable" in data["error"]["message"].lower()
