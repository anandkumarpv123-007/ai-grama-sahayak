import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from app.main import app
from app.core.retrieval_client import RetrievalOutcome

client = TestClient(app)


def test_chat_valid_contract_without_conv_id():
    payload = {
        "message": "What government schemes are available for farmers?",
        "assistant": "agriculture",
        "language": "te",
        "state": "Andhra Pradesh",
        "district": "Kakinada",
        "conversation_id": None,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Exact field names matching docs/api_contracts.md
    assert "conversation_id" in data
    assert data["conversation_id"].startswith("conv_")
    assert "answer" in data
    assert data["assistant"] == "agriculture"
    assert data["language"] == "te"
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert "needs_follow_up" in data
    assert "follow_up_questions" in data
    assert "safety_notice" in data
    assert data["safety_notice"] is not None

    # Check that Telugu text is uncorrupted and contains valid Telugu Unicode characters
    assert any("\u0c00" <= c <= "\u0c7f" for c in data["answer"])
    assert "\\u" not in data["answer"]


def test_chat_valid_contract_with_conv_id():
    custom_conv_id = "conv_test_custom_987"
    payload = {
        "message": "Tell me about crop loans.",
        "assistant": "agriculture",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Kakinada",
        "conversation_id": custom_conv_id,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == custom_conv_id


def test_chat_empty_retrieval_returns_unavailability_notice_and_no_sources():
    payload = {
        "message": "cryptocurrency stock trading blockchain mining",
        "assistant": "agriculture",
        "language": "en",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sources"] == []
    assert "Verified official information is currently unavailable" in data["answer"]


def test_chat_with_mocked_retrieval_chunks():
    mock_chunks = [
        {
            "text": "PM-Kisan provides Rs 6,000 annually to eligible landholder farmers.",
            "source": {
                "title": "PM Kisan Portal",
                "url": "https://pmkisan.gov.in",
                "publisher": "Govt of India",
                "verified_at": "2026-11-22",
            },
        }
    ]
    mock_outcome = RetrievalOutcome(chunks=mock_chunks, success=True, is_available=True)
    with patch("app.api.chat.fetch_retrieval_context", return_value=mock_outcome):
        payload = {
            "message": "What is PM Kisan benefit?",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 1
        assert data["sources"][0]["url"] == "https://pmkisan.gov.in"
        assert "6,000 annually" in data["answer"]


def test_chat_retrieval_service_failure_distinct_from_empty_results():
    """
    Requirement 4: Distinguish a genuine empty retrieval result from a retrieval failure.
    Do not silently make a broken retrieval service appear successful.
    """
    failure_outcome = RetrievalOutcome(
        chunks=[],
        success=False,
        is_available=True,
        error="Vector DB Connection Timeout",
    )
    with patch("app.api.chat.fetch_retrieval_context", return_value=failure_outcome):
        payload = {
            "message": "Where is the nearest primary health center?",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []
        # Notice clearly indicates technical issue, NOT "no official information exists"
        assert "technical issue" in data["answer"].lower() or "failure" in data["answer"].lower()
        assert data["needs_follow_up"] is True


def test_chat_blank_message_rejected():
    payload = {
        "message": "   ",
        "assistant": "healthcare",
        "language": "en",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data


def test_chat_invalid_assistant_rejected():
    payload = {
        "message": "Hello",
        "assistant": "astrology",
        "language": "en",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_chat_unsupported_language_rejected():
    payload = {
        "message": "Namaste",
        "assistant": "schemes",
        "language": "hi",  # Hindi excluded in frozen contract
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
