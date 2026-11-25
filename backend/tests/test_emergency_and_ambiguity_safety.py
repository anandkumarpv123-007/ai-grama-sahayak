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


def test_chat_ambiguous_scheme_required_documents_reproduction():
    """
    Exact reproduction query: 'What are the required documents for the scheme?'
    Must trigger clarification rather than returning unrelated NTR Bharosa retrieval.
    """
    payload = {
        "message": "What are the required documents for the scheme?",
        "assistant": "schemes",
        "language": "en",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "specify which scheme" in data["answer"].lower() or "which scheme or sector" in data["answer"].lower()
    assert data["sources"] == []
    assert data["needs_follow_up"] is True
    assert "NTR Bharosa" in data["answer"]
    assert "Annadata Sukhibhava – PM KISAN" in data["answer"]
    assert "Dr. NTR Vaidya Seva" in data["answer"]
    assert "Thalliki Vandanam" in data["answer"]
    # Must NOT have returned chunks or retrieval from NTR Bharosa
    assert "[1. Overview and Scheme Purpose (పథక నేపథ్యం మరియు లక్ష్యం)]" not in data["answer"]


def test_chat_ambiguous_scheme_telugu_required_documents():
    """
    Telugu required documents query for unspecified scheme:
    'ఆ పథకానికి అవసరమైన పత్రాలు ఏమిటి?'
    """
    payload = {
        "message": "ఆ పథకానికి అవసరమైన పత్రాలు ఏమిటి?",
        "assistant": "schemes",
        "language": "te",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "స్పష్టం చేయగలరా" in data["answer"] or "ఏ పథకం గురించి" in data["answer"]
    assert data["sources"] == []
    assert data["needs_follow_up"] is True
    assert "ఎన్టీఆర్ భరోసా" in data["answer"]
    assert "అన్నదాత సుఖీభవ" in data["answer"]
    assert "డా. ఎన్టీఆర్ వైద్య సేవ" in data["answer"]
    assert "తల్లికి వందనం" in data["answer"]


def test_chat_ambiguous_scheme_long_queries_en_and_te():
    """
    Long queries (well over 6-8 words) must trigger clarification without getting
    blocked by arbitrary word-count ceilings.
    """
    # English long query (17 words)
    payload_en = {
        "message": "Can you please explain all the eligibility criteria, documentation, and application steps for the government scheme?",
        "assistant": "schemes",
        "language": "en",
    }
    res_en = client.post("/api/chat", json=payload_en)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "specify which scheme" in data_en["answer"].lower()
    assert data_en["sources"] == []
    assert data_en["needs_follow_up"] is True

    # Telugu long query (13 words)
    payload_te = {
        "message": "ఆంధ్రప్రదేశ్ ప్రభుత్వ సంక్షేమ పథకానికి దరఖాస్తు చేసుకోవడానికి కావలసిన ముఖ్యమైన పత్రాలు మరియు అర్హతలు ఏమిటి?",
        "assistant": "schemes",
        "language": "te",
    }
    res_te = client.post("/api/chat", json=payload_te)
    assert res_te.status_code == 200
    data_te = res_te.json()
    assert "స్పష్టం చేయగలరా" in data_te["answer"]
    assert data_te["sources"] == []
    assert data_te["needs_follow_up"] is True


def test_chat_ambiguous_scheme_short_phrases_en_and_te():
    """
    Short queries (1-3 words) must trigger clarification.
    """
    for phrase in ["scheme documents", "the scheme", "government schemes", "welfare schemes"]:
        res = client.post("/api/chat", json={"message": phrase, "assistant": "schemes", "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert "specify which scheme" in data["answer"].lower()
        assert data["sources"] == []

    for phrase in ["పథకం పత్రాలు", "పథకం", "ప్రభుత్వ పథకాలు", "సంక్షేమ పథకాలు"]:
        res = client.post("/api/chat", json={"message": phrase, "assistant": "schemes", "language": "te"})
        assert res.status_code == 200
        data = res.json()
        assert "స్పష్టం చేయగలరా" in data["answer"]
        assert data["sources"] == []


def test_chat_specific_named_schemes_not_treated_as_ambiguous():
    """
    Specific named schemes (even if phrased with 'documents', 'scheme', or 'eligibility')
    must proceed to retrieval and NOT return clarification.
    """
    # 1. Annadata Sukhibhava
    res1 = client.post(
        "/api/chat",
        json={
            "message": "What are the required documents for Annadata Sukhibhava?",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "specify which scheme" not in data1["answer"].lower()
    assert data1["assistant"] == "agriculture"

    # 2. Dr NTR Vaidya Seva
    res2 = client.post(
        "/api/chat",
        json={
            "message": "What are the required documents for Dr NTR Vaidya Seva scheme?",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Visakhapatnam",
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "specify which scheme" not in data2["answer"].lower()
    assert data2["assistant"] == "healthcare"

    # 3. Thalliki Vandanam
    res3 = client.post(
        "/api/chat",
        json={
            "message": "What are the required documents for Thalliki Vandanam?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Guntur",
        },
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert "specify which scheme" not in data3["answer"].lower()
    assert data3["assistant"] == "education"

    # 4. NTR Bharosa Pension (Telugu)
    res4 = client.post(
        "/api/chat",
        json={
            "message": "ఎన్టీఆర్ భరోసా పింఛను పథకానికి ఏ పత్రాలు కావాలి?",
            "assistant": "schemes",
            "language": "te",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res4.status_code == 200
    data4 = res4.json()
    assert "స్పష్టం చేయగలరా" not in data4["answer"]
    assert data4["assistant"] == "schemes"

    # 5. Grama Sachivalayam
    res5 = client.post(
        "/api/chat",
        json={
            "message": "What citizen services are delivered at Grama Ward Sachivalayam within 72 hours?",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res5.status_code == 200
    data5 = res5.json()
    assert "specify which scheme" not in data5["answer"].lower()
    assert data5["assistant"] == "schemes"


def test_chat_ordinary_domain_queries_not_treated_as_ambiguous():
    """
    Ordinary agriculture, education, and healthcare questions must never be treated
    as ambiguous scheme questions.
    """
    # Agriculture
    res_agri = client.post(
        "/api/chat",
        json={
            "message": "How do I manage stem borer pest in paddy crop during kharif season?",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
    )
    assert res_agri.status_code == 200
    assert "specify which scheme" not in res_agri.json()["answer"].lower()

    # Healthcare
    res_health = client.post(
        "/api/chat",
        json={
            "message": "What are the symptoms and home precautions for seasonal dengue fever?",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Visakhapatnam",
        },
    )
    assert res_health.status_code == 200
    assert "specify which scheme" not in res_health.json()["answer"].lower()

    # Education
    res_edu = client.post(
        "/api/chat",
        json={
            "message": "When do government high school admissions begin in Andhra Pradesh?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Guntur",
        },
    )
    assert res_edu.status_code == 200
    assert "specify which scheme" not in res_edu.json()["answer"].lower()

    # Telugu Agriculture
    res_te_agri = client.post(
        "/api/chat",
        json={
            "message": "వరి పంటలో తెగుళ్ళ నివారణకు ఎలాంటి మందులు వాడాలి?",
            "assistant": "agriculture",
            "language": "te",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
    )
    assert res_te_agri.status_code == 200
    assert "స్పష్టం చేయగలరా" not in res_te_agri.json()["answer"]


def test_chat_emergency_priority_over_ambiguity():
    """
    Clinical emergencies must ALWAYS take priority over scheme ambiguity detection,
    even if the user query contains words like 'scheme' or 'assistance'.
    """
    payload = {
        "message": "I have severe chest pain and difficulty breathing, which government scheme covers emergency ambulance?",
        "assistant": "healthcare",
        "language": "en",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Must be emergency advisory, NOT scheme clarification
    assert "108" in data["answer"]
    assert "EMERGENCY MEDICAL ADVISORY" in data["answer"]
    assert "specify which scheme" not in data["answer"].lower()
    assert "Sachivalayam" not in data["answer"]
    assert data["sources"] == []


def test_chat_broad_category_unnamed_singular_insurance_scheme():
    """
    Case 2: 'What documents are required for the insurance scheme?'
    'insurance' is a broad category spanning multiple sectors (crop insurance, health insurance,
    life insurance). Asking about 'the insurance scheme' without naming one is an unnamed
    singular scheme that MUST NOT be assigned an arbitrary scheme like NTR Bharosa Pension.
    """
    payload = {
        "message": "What documents are required for the insurance scheme?",
        "assistant": "schemes",
        "language": "en",
        "state": "Andhra Pradesh",
        "district": "Krishna",
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "specify which scheme" in data["answer"].lower()
    assert data["sources"] == []
    assert data["needs_follow_up"] is True
    # Must NOT return NTR Bharosa Pension
    assert "NTR Bharosa Pension Scheme" not in data["answer"] or "specify which scheme" in data["answer"].lower()


def test_chat_broad_category_scheme_discovery_housing_and_scholarships():
    """
    Scheme discovery questions may list relevant options with supporting evidence
    rather than always asking for clarification.
    Case 1: 'Which government housing scheme am I eligible for?'
    Case 3: 'Which scholarship schemes are available for students?'
    Case 7: 'నాకు ఏ గృహ నిర్మాణ పథకం వర్తిస్తుంది?'
    Case 8: 'ఏ విద్యార్థి స్కాలర్షిప్ పథకాలు అందుబాటులో ఉన్నాయి?'
    """
    # Case 1: Housing discovery in English
    res1 = client.post(
        "/api/chat",
        json={
            "message": "Which government housing scheme am I eligible for?",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "specify which scheme" not in data1["answer"].lower()
    assert len(data1["sources"]) > 0
    assert any("Pedalandariki Illu" in s["title"] for s in data1["sources"])

    # Case 3: Scholarship discovery in English
    res3 = client.post(
        "/api/chat",
        json={
            "message": "Which scholarship schemes are available for students?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Guntur",
        },
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert "specify which scheme" not in data3["answer"].lower()
    assert len(data3["sources"]) > 0

    # Case 7: Housing discovery in Telugu
    res7 = client.post(
        "/api/chat",
        json={
            "message": "నాకు ఏ గృహ నిర్మాణ పథకం వర్తిస్తుంది?",
            "assistant": "schemes",
            "language": "te",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res7.status_code == 200
    data7 = res7.json()
    assert "స్పష్టం చేయగలరా" not in data7["answer"]
    assert len(data7["sources"]) > 0

    # Case 8: Scholarship discovery in Telugu
    res8 = client.post(
        "/api/chat",
        json={
            "message": "ఏ విద్యార్థి స్కాలర్షిప్ పథకాలు అందుబాటులో ఉన్నాయి?",
            "assistant": "education",
            "language": "te",
            "state": "Andhra Pradesh",
            "district": "Guntur",
        },
    )
    assert res8.status_code == 200
    data8 = res8.json()
    assert "స్పష్టం చేయగలరా" not in data8["answer"]
    assert len(data8["sources"]) > 0


def test_chat_broad_category_pension_and_named_schemes():
    """
    Case 4: 'Tell me about the pension scheme.'
    Case 5: 'What documents are required for NTR Bharosa Pension Scheme?'
    Case 6: 'What are the benefits of Annadata Sukhibhava?'
    """
    # Case 4: Pension scheme inquiry (NTR Bharosa is the verified AP state pension scheme)
    res4 = client.post(
        "/api/chat",
        json={
            "message": "Tell me about the pension scheme.",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res4.status_code == 200
    data4 = res4.json()
    assert "specify which scheme" not in data4["answer"].lower()
    assert len(data4["sources"]) > 0
    assert any("NTR Bharosa" in s["title"] for s in data4["sources"])

    # Case 5: Named NTR Bharosa Pension Scheme
    res5 = client.post(
        "/api/chat",
        json={
            "message": "What documents are required for NTR Bharosa Pension Scheme?",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
    )
    assert res5.status_code == 200
    data5 = res5.json()
    assert "specify which scheme" not in data5["answer"].lower()
    assert len(data5["sources"]) > 0
    assert any("NTR Bharosa" in s["title"] for s in data5["sources"])

    # Case 6: Named Annadata Sukhibhava
    res6 = client.post(
        "/api/chat",
        json={
            "message": "What are the benefits of Annadata Sukhibhava?",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
    )
    assert res6.status_code == 200
    data6 = res6.json()
    assert "specify which scheme" not in data6["answer"].lower()
    assert len(data6["sources"]) > 0
    assert any("Annadata Sukhibhava" in s["title"] for s in data6["sources"])
