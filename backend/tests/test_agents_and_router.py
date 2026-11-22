import pytest
from app.agents.router import agent_router
from app.agents.agriculture_agent import AgricultureAgent
from app.agents.healthcare_agent import HealthcareAgent
from app.agents.education_agent import EducationAgent
from app.agents.schemes_agent import SchemesAgent
from app.schemas.common import AssistantIdentifier, LanguageCode
from app.core.exceptions import BadRequestException


def test_router_retrieves_all_specialists():
    agri = agent_router.get_agent(AssistantIdentifier.AGRICULTURE)
    assert isinstance(agri, AgricultureAgent)
    assert agri.assistant_id == AssistantIdentifier.AGRICULTURE

    health = agent_router.get_agent(AssistantIdentifier.HEALTHCARE)
    assert isinstance(health, HealthcareAgent)
    assert health.assistant_id == AssistantIdentifier.HEALTHCARE

    edu = agent_router.get_agent(AssistantIdentifier.EDUCATION)
    assert isinstance(edu, EducationAgent)
    assert edu.assistant_id == AssistantIdentifier.EDUCATION

    schemes = agent_router.get_agent(AssistantIdentifier.SCHEMES)
    assert isinstance(schemes, SchemesAgent)
    assert schemes.assistant_id == AssistantIdentifier.SCHEMES


def test_router_invalid_assistant_raises_bad_request():
    with pytest.raises(BadRequestException):
        agent_router.get_agent("unknown_assistant")


def test_intent_classification():
    assert agent_router.classify_intent("How do I protect my paddy crop from pests?") == AssistantIdentifier.AGRICULTURE
    assert agent_router.classify_intent("పంటల బీమా నమోదు ఎలా చేసుకోవాలి?") == AssistantIdentifier.AGRICULTURE

    assert agent_router.classify_intent("What are the OPD timings at the government hospital?") == AssistantIdentifier.HEALTHCARE
    assert agent_router.classify_intent("ఆరోగ్యశ్రీ ఆసుపత్రి ఎక్కడ ఉంది?") == AssistantIdentifier.HEALTHCARE

    assert agent_router.classify_intent("When is the application deadline for college scholarship?") == AssistantIdentifier.EDUCATION
    assert agent_router.classify_intent("విద్యా దీవెన స్కాలర్‌షిప్ స్టేటస్") == AssistantIdentifier.EDUCATION

    assert agent_router.classify_intent("How do I apply for old age pension?") == AssistantIdentifier.SCHEMES
    assert agent_router.classify_intent("రేషన్ కార్డు మరియు పింఛన్ సచివాలయం") == AssistantIdentifier.SCHEMES


def test_agent_fallback_when_retrieval_empty():
    agri = AgricultureAgent()
    res = agri.process_query(
        query="What is the subsidy for drip irrigation?",
        language=LanguageCode.EN,
        state="Andhra Pradesh",
        district="Kakinada",
        retrieved_chunks=[],
    )
    assert "Verified official information is currently unavailable" in res["answer"]
    assert res["sources"] == []
    assert res["needs_follow_up"] is True
    assert res["safety_notice"] is not None
    assert len(res["follow_up_questions"]) > 0


def test_agent_telugu_fallback():
    health = HealthcareAgent()
    res = health.process_query(
        query="దగ్గరలోని ఆసుపత్రి ఎక్కడ ఉంది?",
        language=LanguageCode.TE,
        state="Andhra Pradesh",
        district="Kakinada",
        retrieved_chunks=[],
    )
    assert "ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం అందుబాటులో లేదు" in res["answer"]
    assert res["sources"] == []
    assert "108" in res["safety_notice"]


def test_grounded_evidence_synthesis_and_sources():
    agent = SchemesAgent()
    chunks = [
        {
            "text": "YSR Pension Kanuka provides Rs. 4,000 monthly pension for senior citizens above 60.",
            "source": {
                "title": "YSR Pension Kanuka Guidelines",
                "url": "https://sspensions.ap.gov.in",
                "publisher": "Panchayat Raj Dept, AP",
                "verified_at": "2026-11-21",
            },
        }
    ]
    res = agent.process_query(
        query="What is the pension amount?",
        language=LanguageCode.EN,
        state="Andhra Pradesh",
        district="Kakinada",
        retrieved_chunks=chunks,
    )
    assert "4,000 monthly pension" in res["answer"]
    assert len(res["sources"]) == 1
    assert res["sources"][0].url == "https://sspensions.ap.gov.in"
    assert res["sources"][0].publisher == "Panchayat Raj Dept, AP"
    assert res["needs_follow_up"] is False
