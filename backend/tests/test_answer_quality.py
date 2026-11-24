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


def test_bounded_conversation_memory_lru_and_ttl():
    """
    Validates BoundedConversationMemory:
    - Enforces max capacity with LRU eviction.
    - Enforces TTL expiry.
    - Zero citizen PII is stored.
    """
    from app.api.chat import BoundedConversationMemory
    from app.schemas.common import AssistantIdentifier
    import time

    mem = BoundedConversationMemory(max_size=3, ttl_seconds=1)

    # Insert 3 conversations
    mem.set("conv_1", "agri_annadata", "Annadata Sukhibhava", AssistantIdentifier.AGRICULTURE)
    mem.set("conv_2", "edu_thalliki", "Thalliki Vandanam", AssistantIdentifier.EDUCATION)
    mem.set("conv_3", "schemes_pension", "NTR Bharosa", AssistantIdentifier.SCHEMES)

    assert len(mem) == 3
    assert mem.get("conv_1")["last_scheme_name"] == "Annadata Sukhibhava"

    # Access conv_1 to make it most recently used, so conv_2 becomes oldest
    _ = mem.get("conv_1")

    # Insert 4th item -> should evict conv_2
    mem.set("conv_4", "health_vaidya", "Dr NTR Vaidya Seva", AssistantIdentifier.HEALTHCARE)

    assert len(mem) == 3
    assert mem.get("conv_2") is None  # evicted!
    assert mem.get("conv_1") is not None
    assert mem.get("conv_3") is not None
    assert mem.get("conv_4") is not None

    # Zero PII: only scheme context keys present
    data = mem.get("conv_1")
    assert set(data.keys()) == {"last_scheme_id", "last_scheme_name", "last_assistant"}

    # Test TTL expiry
    time.sleep(1.1)
    assert mem.get("conv_1") is None
    assert mem.get("conv_3") is None
    assert len(mem) == 0


def test_conversation_isolation_and_explicit_scheme_override():
    """
    Multi-turn conversation isolation across distinct conv_ids:
    - Separate conv_ids do not share context.
    - Follow-up with explicit new scheme overrides previous context.
    """
    conv_a = "conv_test_isolation_a"
    conv_b = "conv_test_isolation_b"

    # Conv A asks about Annadata
    r1 = client.post(
        "/api/chat",
        json={
            "message": "Explain about Annadata Sukhibhava – PM Kisan.",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_a,
        },
    )
    assert r1.status_code == 200
    assert "Annadata Sukhibhava" in r1.json()["answer"]

    # Conv B asks contextual query "What are the required documents for this scheme?"
    # Should NOT know about Conv A's Annadata; should prompt user to specify scheme!
    r2 = client.post(
        "/api/chat",
        json={
            "message": "What are the required documents for this scheme?",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_b,
        },
    )
    assert r2.status_code == 200
    assert r2.json()["needs_follow_up"] is True
    assert "specify" in r2.json()["answer"].lower() or "scheme name" in r2.json()["answer"].lower()

    # In Conv A, user explicitly switches to Thalliki Vandanam
    r3 = client.post(
        "/api/chat",
        json={
            "message": "How to apply for Thalliki Vandanam Scheme?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_a,
        },
    )
    assert r3.status_code == 200
    assert "Thalliki Vandanam" in r3.json()["answer"]
    assert "Annadata" not in r3.json()["answer"]

    # In Conv A, follow-up "What are the eligibility criteria for this scheme?"
    # Must resolve to Thalliki Vandanam, NOT Annadata!
    r4 = client.post(
        "/api/chat",
        json={
            "message": "What are the eligibility criteria for this scheme?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "conversation_id": conv_a,
        },
    )
    assert r4.status_code == 200
    assert "Thalliki Vandanam" in r4.json()["answer"]
    assert "75%" in r4.json()["answer"]


def test_retrieved_evidence_takes_precedence_over_static():
    """
    When retrieved chunks contain verified bilingual evidence matching the intent,
    synthesis directly uses and formats the chunk evidence.
    """
    from app.services.answer_synthesizer import (
        synthesize_scheme_answer,
        INTENT_APPLICATION,
        LanguageCode,
    )

    mock_chunk = {
        "text": (
            "## 6. Application, Verification & Grievance Redressal (దరఖాస్తు మరియు సమస్యల పరిష్కారం)\n"
            "* Custom verified ground-truth step: Farmers must complete biometric verification directly at the local Mandal Agricultural Office.\n"
            "* Official portal: https://annadathasukhibhava.ap.gov.in\n"
            "* Toll-free helpline: 155251\n"
            "* **తెలుగు వివరణ:** ప్రత్యేక క్షేత్ర పరిశీలన వివరాలు: రైతులు విధిగా స్థానిక మండల వ్యవసాయ అధికారి కార్యాలయంలో బయోమెట్రిక్ నమోదు పూర్తి చేసుకోవాలి. అధికారిక పోర్టల్ annadathasukhibhava.ap.gov.in మరియు హెల్ప్‌లైన్ 155251 అందుబాటులో ఉన్నాయి."
        ),
        "metadata": {
            "doc_id": "agri_annadata_sukhibhava_pmkisan",
            "section_title": "## 6. Application, Verification & Grievance Redressal (దరఖాస్తు మరియు సమస్యల పరిష్కారం)",
        },
    }

    # In Telugu: chunk evidence must be preferred
    te_answer = synthesize_scheme_answer(
        query="అన్నదాత సుఖీభవ పథకానికి ఎలా దరఖాస్తు చేసుకోవాలి?",
        doc_id="agri_annadata_sukhibhava_pmkisan",
        intent=INTENT_APPLICATION,
        language=LanguageCode.TE,
        chunks=[mock_chunk],
    )
    assert "మండల వ్యవసాయ అధికారి కార్యాలయంలో బయోమెట్రిక్ నమోదు" in te_answer
    assert "155251" in te_answer

    # In English: chunk evidence must be preferred with zero Telugu
    en_answer = synthesize_scheme_answer(
        query="How to apply for Annadata Sukhibhava?",
        doc_id="agri_annadata_sukhibhava_pmkisan",
        intent=INTENT_APPLICATION,
        language=LanguageCode.EN,
        chunks=[mock_chunk],
    )
    assert "Mandal Agricultural Office" in en_answer
    assert not any("\u0C00" <= c <= "\u0C7F" for c in en_answer)


def test_scheme_benefit_reconciliation_and_conservative_qualifications():
    """
    Audits all key benefit statements across scheme profiles for conservative qualification:
    - Annadata: PM-KISAN Rs. 6,000, state top-up qualified.
    - Thalliki Vandanam: Class I to XII, 75% attendance, amount qualified.
    - NTR Bharosa: OAP/widow Rs. 4,000, disabled Rs. 6,000, severe disability up to Rs. 15,000.
    - Dr. NTR Vaidya Seva: Cashless secondary/tertiary up to Rs. 25 lakh, emergency 108 safeguard.
    - KCC: 7% interest, 3% PRI -> 4% effective interest.
    - Vidya Deevena & Vasathi Deevena: 100% tuition (RTF) and boarding (MTF), 75% attendance, Rs. 2.5L income.
    - MGNREGS: 100 days statutory wage employment guarantee.
    - Housing: Pedalandariki Illu female head of family, 4 construction milestones geo-tagging.
    """
    from app.services.answer_synthesizer import SCHEME_PROFILES

    # 1. Annadata
    annadata = SCHEME_PROFILES["agri_annadata_sukhibhava_pmkisan"]["benefits"]
    assert "6,000" in annadata["en"] and "2,000" in annadata["en"]
    assert "published state government operational guidelines" in annadata["en"]
    assert "రూ. 6,000" in annadata["te"] and "అధికారిక ఉత్తర్వులకు లోబడి" in annadata["te"]

    # 2. Thalliki Vandanam
    thalliki = SCHEME_PROFILES["edu_thalliki_vandanam_scheme"]["benefits"]
    assert "Class I through Intermediate" in thalliki["en"] or "Class I to XII" in thalliki["en"]
    assert "75%" in thalliki["en"]
    assert "published notifications" in thalliki["en"]
    assert "75%" in thalliki["te"]

    # 3. NTR Bharosa Pension
    pension = SCHEME_PROFILES["schemes_ntr_bharosa_pension"]["benefits"]
    assert "4,000" in pension["en"]
    assert "6,000" in pension["en"]
    assert "15,000" in pension["en"]
    assert "రూ. 4,000" in pension["te"]
    assert "రూ. 6,000" in pension["te"]
    assert "రూ. 15,000" in pension["te"]

    # 4. Dr. NTR Vaidya Seva
    vaidya = SCHEME_PROFILES["health_dr_ntr_vaidya_seva_aarogyasri"]["benefits"]
    assert "25,00,000" in vaidya["en"] or "25 lakh" in vaidya["en"]
    assert "108" in vaidya["en"]
    assert "Pre-Authorization" in vaidya["en"]
    assert "రూ. 25,00,000" in vaidya["te"]

    # 5. KCC
    kcc = SCHEME_PROFILES["agri_kisan_credit_card"]["benefits"]
    assert "7%" in kcc["en"] and "4%" in kcc["en"] and "3%" in kcc["en"]
    assert "3,00,000" in kcc["en"]

    # 6. Scholarships
    scholarship = SCHEME_PROFILES["edu_vidya_deevena_vasathi_deevena"]["benefits"]
    assert "tuition fee reimbursement" in scholarship["en"].lower()
    assert "10,000" in scholarship["en"] and "20,000" in scholarship["en"]

    # 7. MGNREGS
    nregs = SCHEME_PROFILES["schemes_mgnregs_andhra_pradesh"]["benefits"]
    assert "100 days" in nregs["en"]
    assert "100 రోజుల" in nregs["te"]

    # 8. Housing
    housing = SCHEME_PROFILES["schemes_pedalandariki_illu_housing"]["benefits"]
    assert "female head of the household" in housing["en"]
    assert "milestones" in housing["en"].lower()


def test_member2_commit_knowledge_compatibility():
    """
    Verifies that real documents from Member 2's commit (4d18a84cedb299fcd0a4833c22728efc2f75f655)
    are 100% compatible with evidence extraction without committing those files to this branch.
    Tests multiple core schemes across agriculture, education, healthcare, and pensions.
    """
    import subprocess
    from app.services.answer_synthesizer import (
        extract_bilingual_evidence_from_chunks,
        INTENT_APPLICATION,
        INTENT_BENEFITS,
        INTENT_ELIGIBILITY,
        LanguageCode,
    )
    from app.services.retrieval.chunking import MarkdownChunker
    from app.services.retrieval.models import IngestedDocument

    member2_commit = "4d18a84cedb299fcd0a4833c22728efc2f75f655"
    test_cases = [
        {
            "file": "knowledge_base/verified/agriculture/annadata_sukhibhava_pmkisan.md",
            "doc_id": "agri_annadata_sukhibhava_pmkisan",
            "domain": "agriculture",
            "intent": INTENT_APPLICATION,
            "te_expect": ["దరఖాస్తు", "155251"],
            "en_expect": ["Village Agriculture Assistants"],
        },
        {
            "file": "knowledge_base/verified/education/thalliki_vandanam_scheme.md",
            "doc_id": "edu_thalliki_vandanam_scheme",
            "domain": "education",
            "intent": INTENT_ELIGIBILITY,
            "te_expect": ["75%", "పాఠశాల"],
            "en_expect": ["75%"],
        },
        {
            "file": "knowledge_base/verified/healthcare/dr_ntr_vaidya_seva_aarogyasri.md",
            "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
            "domain": "healthcare",
            "intent": INTENT_BENEFITS,
            "te_expect": ["ఆరోగ్యమిత్ర", "ప్రీ-ఆథరైజేషన్"],
            "en_expect": ["25,00,000"],
        },
        {
            "file": "knowledge_base/verified/schemes/ntr_bharosa_pension.md",
            "doc_id": "schemes_ntr_bharosa_pension",
            "domain": "schemes",
            "intent": INTENT_BENEFITS,
            "te_expect": ["4,000", "పింఛను"],
            "en_expect": ["4,000", "SADAREM"],
        },
    ]

    chunker = MarkdownChunker()

    for tc in test_cases:
        proc = subprocess.run(
            ["git", "show", f"{member2_commit}:{tc['file']}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0, f"Failed to fetch {tc['file']}"
        doc_content = proc.stdout
        assert "తెలుగు వివరణ:" in doc_content

        doc = IngestedDocument(
            doc_id=tc["doc_id"],
            domain=tc["domain"],
            language="bilingual",
            title=tc["doc_id"],
            content=doc_content,
            url="https://example.gov.in",
            publisher="Government of Andhra Pradesh",
            verified_at="2026-11-21",
            metadata={"domain": tc["domain"], "state": "Andhra Pradesh"},
        )
        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 3, f"Insufficient chunks for {tc['doc_id']}"
        chunk_dicts = [c.to_dict() for c in chunks]

        # Test Telugu extraction
        extracted_te = extract_bilingual_evidence_from_chunks(
            chunks=chunk_dicts,
            intent=tc["intent"],
            language=LanguageCode.TE,
            doc_id=tc["doc_id"],
        )
        assert extracted_te is not None, f"Telugu extraction failed for {tc['doc_id']}"
        for exp in tc["te_expect"]:
            assert exp in extracted_te, f"Expected '{exp}' in Telugu extraction for {tc['doc_id']}"

        # Test English extraction
        extracted_en = extract_bilingual_evidence_from_chunks(
            chunks=chunk_dicts,
            intent=tc["intent"],
            language=LanguageCode.EN,
            doc_id=tc["doc_id"],
        )
        assert extracted_en is not None, f"English extraction failed for {tc['doc_id']}"
        for exp in tc["en_expect"]:
            assert exp in extracted_en, f"Expected '{exp}' in English extraction for {tc['doc_id']}"
        # Strict language isolation: no Telugu unicode in English extraction
        assert not any("\u0C00" <= c <= "\u0C7F" for c in extracted_en), (
            f"Telugu characters found in English extraction for {tc['doc_id']}: {extracted_en}"
        )
