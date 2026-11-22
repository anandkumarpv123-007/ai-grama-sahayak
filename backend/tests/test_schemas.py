import pytest
from pydantic import ValidationError
from app.schemas.common import LanguageCode, AssistantIdentifier, Source, ErrorResponse, ErrorBody
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.eligibility import EligibilityRequest, EligibilityResponse, EligibilityStatus


def test_language_code_valid():
    assert LanguageCode.EN.value == "en"
    assert LanguageCode.TE.value == "te"


def test_language_code_invalid_hindi_excluded():
    with pytest.raises(ValueError):
        LanguageCode("hi")


def test_assistant_identifier_valid():
    assert AssistantIdentifier.AGRICULTURE.value == "agriculture"
    assert AssistantIdentifier.HEALTHCARE.value == "healthcare"
    assert AssistantIdentifier.EDUCATION.value == "education"
    assert AssistantIdentifier.SCHEMES.value == "schemes"


def test_assistant_identifier_invalid():
    with pytest.raises(ValueError):
        AssistantIdentifier("sports")


def test_source_model():
    source = Source(
        title="Official source title",
        url="https://verified-official-source.gov.in/page",
        publisher="Government department",
        verified_at="2026-11-21",
    )
    assert source.title == "Official source title"
    assert source.url == "https://verified-official-source.gov.in/page"
    assert source.publisher == "Government department"
    assert source.verified_at == "2026-11-21"


def test_error_response_model():
    err_body = ErrorBody(
        code="VALIDATION_ERROR",
        message="The request contains invalid information.",
        details=[{"loc": ["message"], "msg": "field required"}],
    )
    err_resp = ErrorResponse(error=err_body)
    data = err_resp.model_dump()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "The request contains invalid information."
    assert len(data["error"]["details"]) == 1


def test_chat_request_valid():
    req = ChatRequest(
        message="What government schemes are available for farmers?",
        assistant=AssistantIdentifier.AGRICULTURE,
        language=LanguageCode.TE,
        state="Andhra Pradesh",
        district="Kakinada",
        conversation_id=None,
    )
    assert req.message == "What government schemes are available for farmers?"
    assert req.assistant == AssistantIdentifier.AGRICULTURE
    assert req.language == LanguageCode.TE
    assert req.conversation_id is None


def test_chat_response_contract_fields():
    resp = ChatResponse(
        conversation_id="conv_123",
        answer="Here is verified information...",
        assistant=AssistantIdentifier.AGRICULTURE,
        language=LanguageCode.TE,
        sources=[],
        needs_follow_up=False,
        follow_up_questions=["Any more questions?"],
        safety_notice=None,
    )
    dumped = resp.model_dump()
    assert dumped["conversation_id"] == "conv_123"
    assert dumped["answer"] == "Here is verified information..."
    assert dumped["assistant"] == "agriculture"
    assert dumped["language"] == "te"
    assert dumped["sources"] == []
    assert dumped["needs_follow_up"] is False
    assert dumped["follow_up_questions"] == ["Any more questions?"]
    assert dumped["safety_notice"] is None


def test_eligibility_status_four_agreed_values_only():
    expected_statuses = {"eligible", "ineligible", "needs_more_information", "unable_to_verify"}
    actual_statuses = {s.value for s in EligibilityStatus}
    assert actual_statuses == expected_statuses
