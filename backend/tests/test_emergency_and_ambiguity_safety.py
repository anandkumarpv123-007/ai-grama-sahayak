import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.emergency_detector import check_clinical_emergency
from app.core.scheme_ambiguity_detector import is_ambiguous_scheme_query
from app.schemas.common import LanguageCode

client = TestClient(app)


# ---------------------------------------------------------------------------
# Task 1: Clinical Emergency Interception Tests via POST /api/chat
# ---------------------------------------------------------------------------


def test_chat_emergency_telugu_severe_chest_pain():
    """
    Telugu severe chest pain must trigger immediate emergency response directing to 108.
    Must never direct the citizen to a Grama Sachivalayam.
    """
    payload = {
        "message": "నాకు తీవ్రమైన ఛాతి నొప్పిగా ఉంది, వెంటనే సహాయం కావాలి",
        "assistant": "healthcare",
        "language": "te",
        "state": "Andhra Pradesh",
        "district": "Kakinada",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "108" in data["answer"]
    assert "సచివాలయం" not in data["answer"]
    assert "Sachivalayam" not in data["answer"]
    assert data["sources"] == []
    assert data["needs_follow_up"] is False
    assert len(data["follow_up_questions"]) > 0
    assert "108" in data["safety_notice"]


def test_chat_emergency_english_severe_chest_pain():
    """
    English severe chest pain must trigger immediate emergency response directing to 108.
    Must never direct the citizen to a Grama Sachivalayam.
    """
    payload = {
        "message": "I am experiencing severe chest pain and crushing pressure radiating to my left arm",
        "assistant": "healthcare",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "108" in data["answer"]
    assert "Sachivalayam" not in data["answer"]
    assert "sachivalayam" not in data["answer"].lower()
    assert data["sources"] == []
    assert data["needs_follow_up"] is False
    assert any("108" in q for q in data["follow_up_questions"])
    assert "108" in data["safety_notice"]


def test_chat_emergency_intercepts_when_assistant_is_not_healthcare():
    """
    Task 2 requirement: Confirm that the emergency detector runs before normal retrieval
    even when the selected assistant is not healthcare (e.g. agriculture or schemes).
    """
    # Sent to agriculture assistant by mistake during emergency
    payload_agri = {
        "message": "severe chest pain",
        "assistant": "agriculture",
        "language": "en",
    }
    res_agri = client.post("/api/chat", json=payload_agri)
    assert res_agri.status_code == 200
    data_agri = res_agri.json()
    assert "108" in data_agri["answer"]
    assert "Sachivalayam" not in data_agri["answer"]
    assert data_agri["sources"] == []
    assert data_agri["needs_follow_up"] is False

    # Sent to schemes assistant by mistake during emergency
    payload_schemes = {
        "message": "తీవ్రమైన ఛాతి నొప్పి",
        "assistant": "schemes",
        "language": "te",
    }
    res_schemes = client.post("/api/chat", json=payload_schemes)
    assert res_schemes.status_code == 200
    data_schemes = res_schemes.json()
    assert "108" in data_schemes["answer"]
    assert "సచివాలయం" not in data_schemes["answer"]
    assert data_schemes["sources"] == []
    assert data_schemes["needs_follow_up"] is False


def test_chat_emergency_severe_breathing_difficulty():
    """
    Severe breathing difficulty in English and Telugu must intercept before retrieval.
    """
    # English
    payload_en = {
        "message": "Patient is gasping for air and having severe difficulty breathing, cannot breathe",
        "assistant": "healthcare",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "108" in data_en["answer"]
    assert "Sachivalayam" not in data_en["answer"]
    assert data_en["sources"] == []

    # Telugu
    payload_te = {
        "message": "శ్వాస తీసుకోవడంలో తీవ్రమైన ఇబ్బందిగా ఉంది, ఊపిరి ఆడటం లేదు",
        "assistant": "healthcare",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "108" in data_te["answer"]
    assert "సచివాలయం" not in data_te["answer"]
    assert data_te["sources"] == []


def test_chat_emergency_stroke_symptoms():
    """
    Stroke symptoms (facial drooping, slurred speech, sudden paralysis) must trigger 108.
    """
    # English
    payload_en = {
        "message": "Sudden facial drooping, arm weakness, and slurred speech",
        "assistant": "healthcare",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "108" in data_en["answer"]
    assert "Sachivalayam" not in data_en["answer"]

    # Telugu
    payload_te = {
        "message": "పక్షవాతం లక్షణాలు కనిపిస్తున్నాయి, ముఖం వంకరపోయింది, మాట పడిపోయింది",
        "assistant": "healthcare",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "108" in data_te["answer"]
    assert "సచివాలయం" not in data_te["answer"]


def test_chat_emergency_unconsciousness():
    """
    Sudden collapse, unresponsive patient, or unconsciousness must trigger 108 immediately.
    """
    # English
    payload_en = {
        "message": "He suddenly collapsed, passed out and is completely unconscious and unresponsive",
        "assistant": "healthcare",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "108" in data_en["answer"]
    assert "Sachivalayam" not in data_en["answer"]

    # Telugu
    payload_te = {
        "message": "వ్యక్తి స్పృహ తప్పి పడిపోయారు, స్పృహ లేదు",
        "assistant": "healthcare",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "108" in data_te["answer"]
    assert "సచివాలయం" not in data_te["answer"]


def test_chat_emergency_poisoning_and_bleeding():
    """
    Pesticide poisoning and massive bleeding must be intercepted as emergencies.
    """
    # Poisoning (English)
    payload_poison = {
        "message": "Accidental chemical poisoning, drank pesticide and is in critical condition",
        "assistant": "healthcare",
        "language": "en",
    }
    res_poison = client.post("/api/chat", json=payload_poison)
    assert res_poison.status_code == 200
    assert "108" in res_poison.json()["answer"]
    assert "Sachivalayam" not in res_poison.json()["answer"]

    # Poisoning (Telugu)
    payload_poison_te = {
        "message": "పురుగుల మందు తాగడం జరిగింది",
        "assistant": "healthcare",
        "language": "te",
    }
    res_poison_te = client.post("/api/chat", json=payload_poison_te)
    assert res_poison_te.status_code == 200
    assert "108" in res_poison_te.json()["answer"]
    assert "సచివాలయం" not in res_poison_te.json()["answer"]


# ---------------------------------------------------------------------------
# Negation & Historical mentions: Must NOT trigger emergency response
# ---------------------------------------------------------------------------


def test_chat_negated_symptoms_not_treated_as_emergencies():
    """
    Negated symptom expressions (e.g. 'no chest pain', 'without breathing difficulty')
    must not trigger emergency overrides.
    """
    # English
    payload_en = {
        "message": "Patient has common seasonal flu and high fever, no chest pain and no shortness of breath",
        "assistant": "healthcare",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "EMERGENCY MEDICAL ADVISORY" not in data_en["answer"]

    # Telugu
    payload_te = {
        "message": "నాకు జ్వరం ఉంది, ఛాతి నొప్పి లేదు, శ్వాస ఇబ్బంది లేదు",
        "assistant": "healthcare",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "అత్యవసర వైద్య హెచ్చరిక: మీరు పేర్కొన్న లక్షణాలు ప్రాణాంతకమైన" not in data_te["answer"]


def test_chat_historical_symptom_mentions_not_treated_as_emergencies():
    """
    Past/historical symptom mentions (e.g. 'had a heart attack 5 years ago')
    must not trigger active emergency overrides.
    """
    # English
    payload_en = {
        "message": "I had a heart attack 5 years ago in 2019, now asking about general healthy diet options",
        "assistant": "healthcare",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "EMERGENCY MEDICAL ADVISORY" not in data_en["answer"]

    # Telugu
    payload_te = {
        "message": "గతంలో ఛాతీ నొప్పి వచ్చింది, ఇప్పుడు ఏమీ లేదు. ఆహార నియమాలు చెప్పండి",
        "assistant": "healthcare",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "అత్యవసర వైద్య హెచ్చరిక: మీరు పేర్కొన్న లక్షణాలు ప్రాణాంతకమైన" not in data_te["answer"]


# ---------------------------------------------------------------------------
# Task 2: Ambiguous Scheme Query Clarification Tests
# ---------------------------------------------------------------------------


def test_chat_ambiguous_scheme_query_returns_clarification():
    """
    When a citizen asks about 'the scheme' vaguely, return a clear clarification
    rather than concatenating unrelated schemes.
    Must use current project-supported scheme names and omit legacy names.
    """
    # English
    payload_en = {
        "message": "tell me about the scheme",
        "assistant": "schemes",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()

    assert "specify which scheme" in data_en["answer"].lower() or "which scheme or sector" in data_en["answer"].lower()
    assert data_en["sources"] == []
    assert data_en["needs_follow_up"] is True
    assert len(data_en["follow_up_questions"]) > 0

    # Verify current project-supported schemes
    assert "NTR Bharosa" in data_en["answer"]
    assert "Annadata Sukhibhava – PM KISAN" in data_en["answer"]
    assert "Dr. NTR Vaidya Seva" in data_en["answer"]
    assert "Thalliki Vandanam" in data_en["answer"]

    # Verify absence of legacy names
    assert "YSR Pension Kanuka" not in data_en["answer"]
    assert "YSR Rythu Bharosa" not in data_en["answer"]
    assert "Dr. YSR Aarogyasri" not in data_en["answer"]
    assert "Jagananna Amma Vodi" not in data_en["answer"]

    # Verify follow-up questions use current names
    assert any("NTR Bharosa" in q for q in data_en["follow_up_questions"])
    assert any("Annadata Sukhibhava" in q for q in data_en["follow_up_questions"])
    assert any("Dr. NTR Vaidya Seva" in q for q in data_en["follow_up_questions"])

    # Telugu
    payload_te = {
        "message": "పథకం గురించి చెప్పండి",
        "assistant": "schemes",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()

    assert "స్పష్టం చేయగలరా" in data_te["answer"] or "ఏ పథకం గురించి" in data_te["answer"]
    assert data_te["sources"] == []
    assert data_te["needs_follow_up"] is True
    assert len(data_te["follow_up_questions"]) > 0

    # Verify Telugu current scheme names
    assert "ఎన్టీఆర్ భరోసా" in data_te["answer"]
    assert "అన్నదాత సుఖీభవ" in data_te["answer"]
    assert "డా. ఎన్టీఆర్ వైద్య సేవ" in data_te["answer"]
    assert "తల్లికి వందనం" in data_te["answer"]

    # Verify absence of legacy names
    assert "వైఎస్సార్ పింఛన్ కానుక" not in data_te["answer"]
    assert "వైఎస్సార్ రైతు భరోసా" not in data_te["answer"]
    assert "డా. వైఎస్సార్ ఆరోగ్యశ్రీ" not in data_te["answer"]
    assert "జగనన్న అమ్మ ఒడి" not in data_te["answer"]


def test_chat_specific_pension_query_continues_to_work():
    """
    Specific scheme questions (e.g. about YSR Pension Kanuka) must NOT trigger ambiguity clarification;
    normal retrieval and answer synthesis must proceed.
    """
    payload = {
        "message": "What is the monthly pension amount under YSR Pension Kanuka for old age beneficiaries?",
        "assistant": "schemes",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Krishna",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Must NOT be the ambiguous clarification text
    assert "specify which scheme" not in data["answer"].lower()
    # If chunks exist in retrieval index, they are returned; otherwise genuine unavailability
    assert data["assistant"] == "schemes"


def test_chat_existing_normal_agriculture_and_education_queries():
    """
    Verify existing domain queries in Agriculture and Education proceed smoothly without
    triggering emergency or scheme ambiguity guards.
    """
    # Agriculture
    payload_agri = {
        "message": "What is the financial assistance provided to farmers under Annadata Sukhibhava PM Kisan?",
        "assistant": "agriculture",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Kakinada",
    }
    res_agri = client.post("/api/chat", json=payload_agri)
    assert res_agri.status_code == 200
    data_agri = res_agri.json()
    assert "EMERGENCY MEDICAL ADVISORY" not in data_agri["answer"]
    assert "specify which scheme" not in data_agri["answer"].lower()
    assert data_agri["assistant"] == "agriculture"

    # Education
    payload_edu = {
        "message": "What are the eligibility criteria and attendance requirements for Thalliki Vandanam?",
        "assistant": "education",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Guntur",
    }
    res_edu = client.post("/api/chat", json=payload_edu)
    assert res_edu.status_code == 200
    data_edu = res_edu.json()
    assert "EMERGENCY MEDICAL ADVISORY" not in data_edu["answer"]
    assert "specify which scheme" not in data_edu["answer"].lower()
    assert data_edu["assistant"] == "education"
