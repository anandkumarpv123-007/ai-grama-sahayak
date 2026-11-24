import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_telugu_annadata_application_actionable_and_no_english_paragraphs():
    """
    Physical defect fix: Query asking how to apply for Annadata Sukhibhava in Telugu
    must return direct actionable steps in Telugu without English paragraphs.
    """
    payload = {
        "message": "అన్నదాత సుఖీభవ పథకానికి ఎలా దరఖాస్తు చేసుకోవాలి?",
        "assistant": "agriculture",
        "language": "te",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    # Actionable Telugu guidance present
    assert "రైతు సేవా కేంద్రం" in answer or "రైతు భరోసా కేంద్రం" in answer
    assert "గ్రామ వ్యవసాయ సహాయకుడిని" in answer or "VAA" in answer
    assert "ఈ-పంట" in answer or "e-Crop" in answer
    assert "ఈ-కేవైసీ" in answer or "e-KYC" in answer
    assert "https://annadathasukhibhava.ap.gov.in" in answer
    assert "155251" in answer or "1902" in answer

    # No English paragraphs (English words should only be technical acronyms/URLs)
    for line in answer.split("\n"):
        l = line.strip()
        if not l or l.startswith("http") or l.startswith("-") or l.startswith("•"):
            continue
        # Non-bullet lines must not be long English sentences
        if len(l) > 40 and not any("\u0C00" <= c <= "\u0C7F" for c in l):
            pytest.fail(f"English sentence leaked in Telugu response: {l}")


def test_telugu_thalliki_vandanam_documents():
    """
    Query asking for required documents in Telugu must return structured documents list.
    """
    payload = {
        "message": "తల్లికి వందనం పథకానికి అవసరమైన పత్రాలు ఏమిటి?",
        "assistant": "education",
        "language": "te",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "ఆధార్" in answer
    assert "రేషన్ కార్డు" in answer or "రైస్ కార్డు" in answer
    assert "బ్యాంక్" in answer
    assert "75%" in answer


def test_telugu_crop_insurance_application():
    """
    Query asking how to apply for crop insurance in Telugu.
    """
    payload = {
        "message": "పంటల బీమాకు ఎలా దరఖాస్తు చేయాలి?",
        "assistant": "agriculture",
        "language": "te",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "ఈ-పంట" in answer or "e-Crop" in answer
    assert "రైతు సేవా కేంద్రం" in answer or "రైతు భరోసా కేంద్రం" in answer
    assert "https://pmfby.gov.in" in answer


def test_english_ammavodi_zero_telugu_characters():
    """
    English queries must have ZERO Telugu Unicode characters.
    """
    payload = {
        "message": "Explain about Ammavodi, Andhra Pradesh.",
        "assistant": "education",
        "language": "en",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "Thalliki Vandanam" in answer
    assert "Amma Vodi" in answer
    # Strict zero Telugu script check
    assert not any("\u0C00" <= c <= "\u0C7F" for c in answer)


def test_english_difference_amma_vodi_vs_thalliki():
    """
    Comparison between Amma Vodi and Thalliki Vandanam in English.
    """
    payload = {
        "message": "What is the difference between Amma Vodi and Thalliki Vandanam?",
        "assistant": "education",
        "language": "en",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "predecessor" in answer.lower() or "formerly" in answer.lower() or "transition" in answer.lower()
    assert "Thalliki Vandanam" in answer
    assert not any("\u0C00" <= c <= "\u0C7F" for c in answer)


def test_unsupported_scheme_pmxyz():
    """
    Unsupported scheme query must return honest unavailability response and official portal link.
    """
    payload = {
        "message": "Explain about PMXYZ scheme.",
        "assistant": "schemes",
        "language": "en",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "PMXYZ" in answer
    assert "unavailable" in answer.lower()
    assert "https://www.ap.gov.in" in answer
    assert data["sources"] == []


def test_unspecified_how_to_apply_prompts_user():
    """
    Query asking 'How do I apply for this scheme?' without previous context prompts the user.
    """
    payload = {
        "message": "How do I apply for this scheme?",
        "assistant": "schemes",
        "language": "en",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "specify which scheme" in answer.lower() or "scheme name" in answer.lower()
    assert data["needs_follow_up"] is True
    assert data["sources"] == []


def test_contextual_follow_up_resolves_previous_scheme():
    """
    Multi-turn conversation: Turn 1 names a scheme; Turn 2 asks contextual follow-up.
    """
    conv_id = "conv_test_multiturn_qa_99"
    # Turn 1
    r1 = client.post(
        "/api/chat",
        json={
            "message": "Explain about Ayushman Bharat PM-JAY.",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_id,
        },
    )
    assert r1.status_code == 200
    assert "Ayushman Bharat" in r1.json()["answer"]

    # Turn 2
    r2 = client.post(
        "/api/chat",
        json={
            "message": "What documents are required for this scheme?",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_id,
        },
    )
    assert r2.status_code == 200
    data = r2.json()
    assert "Ayushman Bharat" in data["answer"]
    assert "Aadhaar" in data["answer"]


def test_clinical_emergency_bypasses_retrieval():
    """
    Emergency symptoms bypass standard retrieval and provide immediate 108 instructions.
    """
    payload = {
        "message": "నాకు తీవ్రమైన ఛాతి నొప్పి వస్తోంది.",
        "assistant": "healthcare",
        "language": "te",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "108" in data["answer"]
    assert "అత్యవసర" in data["answer"]
    assert data["sources"] == []


def test_nearby_rbk_asks_for_location():
    """
    Nearby RBK query without location asks for district, mandal, or village.
    """
    payload = {
        "message": "నాకు సమీపంలోని రైతు భరోసా కేంద్రం ఎక్కడ ఉంది?",
        "assistant": "agriculture",
        "language": "te",
        "state": "Andhra Pradesh",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"]

    assert "జిల్లా" in answer or "మండలం" in answer or "గ్రామం" in answer
    assert "https://gramawardsachivalayam.ap.gov.in" in answer
    assert "https://karshak.ap.gov.in" in answer
