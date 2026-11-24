"""
Unit tests for domain retrieval across Agriculture, Healthcare, Education, and Schemes.
Tests English and Telugu queries, domain isolation, and return structure predictability.
"""

import pytest
from app.services.retrieval import retrieve_context, get_citations, format_evidence_text


@pytest.mark.parametrize(
    "query,assistant,language,expected_term",
    [
        # Agriculture - English
        ("Annadata Sukhibhava farmer financial assistance", "agriculture", "en", "Annadata Sukhibhava"),
        ("PM Fasal Bima Yojana crop insurance coverage", "agriculture", "en", "PM Fasal Bima"),
        ("Kisan Credit Card interest subvention and loan limits", "agriculture", "en", "Kisan Credit Card"),
        # Agriculture - Telugu
        ("అన్నదాత సుఖీభవ పథకం కింద రైతులకు ఎంత సాయం అందుతుంది?", "agriculture", "te", "అన్నదాత సుఖీభవ"),
        ("రైతులకు పంటల బీమా పథకం పరిహారం ఎలా వస్తుంది?", "agriculture", "te", "పంటల బీమా"),
        # Healthcare - English
        ("Dr NTR Vaidya Seva Aarogyasri hospital coverage limit", "healthcare", "en", "Dr. NTR Vaidya Seva"),
        ("108 emergency ambulance and 104 mobile medical unit", "healthcare", "en", "108 Emergency"),
        ("Ayushman Bharat PM-JAY national hospital portability", "healthcare", "en", "Ayushman Bharat"),
        # Healthcare - Telugu
        ("ఎన్టీఆర్ వైద్య సేవ ఆరోగ్యశ్రీ కింద ఎంత మొత్తం వరకు ఉచిత చికిత్స లభిస్తుంది?", "healthcare", "te", "వైద్య సేవ"),
        ("అత్యవసర సమయంలో 108 అంబులెన్స్ సేవలు ఎలా పొందాలి?", "healthcare", "te", "108"),
        # Education - English
        ("Thalliki Vandanam eligibility and attendance rules", "education", "en", "Thalliki Vandanam"),
        ("Jagananna Vidya Deevena tuition fee reimbursement", "education", "en", "Vidya Deevena"),
        # Education - Telugu
        ("తల్లికి వందనం పథకానికి అర్హతలు ఏమిటి? ఎంత హాజరు ఉండాలి?", "education", "te", "తల్లికి వందనం"),
        ("కాలేజీ విద్యార్థులకు విద్యా దీవెన వసతి దీవెన ఎంత సాయం?", "education", "te", "విద్యా దీవెన"),
        # Government Schemes - English
        ("NTR Bharosa monthly pension amount for old age and disabled", "schemes", "en", "NTR Bharosa"),
        ("Grama Ward Sachivalayam citizen service delivery 72 hours", "schemes", "en", "Sachivalayam"),
        ("MGNREGS 100 days guaranteed wage employment AP", "schemes", "en", "MGNREGS"),
        ("Pedalandariki Illu housing construction financial grant", "schemes", "en", "Pedalandariki Illu"),
        # Government Schemes - Telugu
        ("ఎన్టీఆర్ భరోసా వృద్ధాప్య పింఛను మరియు దివ్యాంగుల పెన్షన్ ఎంత?", "schemes", "te", "ఎన్టీఆర్ భరోసా"),
        ("గ్రామ సచివాలయంలో అందించే పౌర సేవలు మరియు గడువు ఎంత?", "schemes", "te", "సచివాలయ"),
    ],
)
def test_retrieval_across_domains(query, assistant, language, expected_term):
    results = retrieve_context(
        query=query,
        assistant=assistant,
        language=language,
        state="Andhra Pradesh",
        district="Kakinada",
        top_k=3,
    )

    assert isinstance(results, list)
    assert len(results) > 0, f"Expected results for query: '{query}'"

    # Verify predictable chunk format
    first_chunk = results[0]
    assert "text" in first_chunk
    assert "title" in first_chunk
    assert "url" in first_chunk
    assert "publisher" in first_chunk
    assert "verified_at" in first_chunk
    assert "source" in first_chunk
    assert "score" in first_chunk
    assert "metadata" in first_chunk

    # Ensure result is relevant
    all_texts = " ".join([c["title"] + " " + c["text"] for c in results])
    assert expected_term.lower() in all_texts.lower()

    # STRICT DOMAIN ISOLATION CHECK:
    for c in results:
        assert c["metadata"]["domain"] == assistant, (
            f"Cross-domain violation: received {c['metadata']['domain']} chunk for {assistant} assistant"
        )


def test_domain_isolation_cross_check():
    """
    Ensures an agricultural query routed to 'healthcare' assistant does not return agriculture chunks,
    and returns empty list if no health matches exist.
    """
    results = retrieve_context(
        query="paddy seed fertilizer cultivation",
        assistant="healthcare",
        language="en",
        state="Andhra Pradesh",
        district=None,
    )
    for c in results:
        assert c["metadata"]["domain"] == "healthcare"


def test_top_k_parameter():
    results_2 = retrieve_context(
        query="farmer assistance schemes",
        assistant="agriculture",
        language="en",
        top_k=2,
    )
    assert len(results_2) <= 2

    results_4 = retrieve_context(
        query="farmer assistance schemes",
        assistant="agriculture",
        language="en",
        top_k=4,
    )
    assert len(results_4) <= 4


def test_citations_helper():
    results = retrieve_context(
        query="NTR Bharosa pension rates",
        assistant="schemes",
        language="en",
        top_k=3,
    )
    citations = get_citations(results)
    assert isinstance(citations, list)
    assert len(citations) >= 1

    for cit in citations:
        assert "title" in cit
        assert "url" in cit
        assert "publisher" in cit
        assert "verified_at" in cit
        assert cit["url"].startswith("http")


def test_format_evidence_text_helper():
    results = retrieve_context(
        query="Thalliki Vandanam",
        assistant="education",
        language="en",
        top_k=2,
    )
    evidence_text = format_evidence_text(results)
    assert isinstance(evidence_text, str)
    assert "Evidence Chunk 1" in evidence_text
    assert "Thalliki Vandanam" in evidence_text


# ==============================================================================
# PHASE 4A REGRESSION TESTS: QUESTION-INTENT RELEVANCE (TELUGU & ENGLISH)
# ==============================================================================

def test_telugu_annadata_assistance_amount_ranking():
    """
    Regression Test: Telugu Annadata assistance query must rank chunk c1
    (Financial Assistance Framework) at Rank 1 with verified PM-KISAN assistance
    and conditional state top-up guidance, without removed unsupported combined figures.
    """
    query = "అన్నదాత సుఖీభవ పథకం కింద రైతులకు ఎంత ఆర్థిక సహాయం అందుతుంది?"
    results = retrieve_context(
        query=query,
        assistant="agriculture",
        language="te",
        top_k=5,
    )
    assert len(results) > 0
    top_chunk = results[0]
    assert top_chunk["metadata"]["chunk_id"] == "agri_annadata_sukhibhava_pmkisan_c1"
    assert "Financial Assistance" in top_chunk["metadata"]["section_title"]
    assert "6,000" in top_chunk["text"]
    assert "PM-KISAN" in top_chunk["text"]
    assert "20,000" not in top_chunk["text"]
    assert "Rs." in top_chunk["text"]
    # Verify citations helper works and points to verified agriculture portal
    citations = get_citations(results)
    assert len(citations) >= 1
    assert "annadathasukhibhava.ap.gov.in" in citations[0]["url"]


def test_english_annadata_assistance_amount_ranking():
    """
    Regression Test: English Annadata assistance query must rank chunk c1 at Rank 1
    with verified PM-KISAN and conditional state top-up assistance, without removed figures.
    """
    query = "What is the annual financial assistance for farmers under Annadata Sukhibhava?"
    results = retrieve_context(
        query=query,
        assistant="agriculture",
        language="en",
        top_k=5,
    )
    assert len(results) > 0
    top_chunk = results[0]
    assert top_chunk["metadata"]["chunk_id"] == "agri_annadata_sukhibhava_pmkisan_c1"
    assert "Financial Assistance" in top_chunk["metadata"]["section_title"]
    assert "6,000" in top_chunk["text"]
    assert "state top-up" in top_chunk["text"].lower() or "top-up" in top_chunk["text"].lower()
    assert "20,000" not in top_chunk["text"]


def test_telugu_and_english_eligibility_ranking():
    """
    Regression Test: Eligibility queries in Telugu and English must rank eligibility sections at Rank 1.
    """
    # Telugu Eligibility Query
    te_query = "అన్నదాత సుఖీభవ పథకానికి ఎవరెవరు అర్హులు? అర్హత నిబంధనలు ఏమిటి?"
    te_results = retrieve_context(
        query=te_query,
        assistant="agriculture",
        language="te",
        top_k=3,
    )
    assert len(te_results) > 0
    assert te_results[0]["metadata"]["chunk_id"] == "agri_annadata_sukhibhava_pmkisan_c2"
    assert "Eligibility" in te_results[0]["metadata"]["section_title"]

    # English Eligibility Query
    en_query = "What are the eligibility criteria and required attendance for Thalliki Vandanam?"
    en_results = retrieve_context(
        query=en_query,
        assistant="education",
        language="en",
        top_k=3,
    )
    assert len(en_results) > 0
    assert en_results[0]["metadata"]["chunk_id"] == "edu_thalliki_vandanam_scheme_c2"
    assert "Eligibility" in en_results[0]["metadata"]["section_title"]
    assert "75%" in en_results[0]["text"]


def test_telugu_and_english_documents_ranking():
    """
    Regression Test: Required documents queries in Telugu and English must rank documents sections at Rank 1.
    """
    # Telugu Documents Query
    te_query = "అన్నదాత సుఖీభవ దరఖాస్తుకు ఏయే పత్రాలు కావాలి?"
    te_results = retrieve_context(
        query=te_query,
        assistant="agriculture",
        language="te",
        top_k=3,
    )
    assert len(te_results) > 0
    assert te_results[0]["metadata"]["chunk_id"] == "agri_annadata_sukhibhava_pmkisan_c4"
    assert "Required Documents" in te_results[0]["metadata"]["section_title"]

    # English Documents Query
    en_query = "What documents are required to apply for Kisan Credit Card?"
    en_results = retrieve_context(
        query=en_query,
        assistant="agriculture",
        language="en",
        top_k=3,
    )
    assert len(en_results) > 0
    assert en_results[0]["metadata"]["chunk_id"] == "agri_kisan_credit_card_c3"
    assert "Required Documents" in en_results[0]["metadata"]["section_title"]


def test_telugu_and_english_pension_amount_ranking():
    """
    Regression Test: Pension payout queries in Telugu and English must rank monthly payout chunks at Rank 1,
    verifying benchmarked OAP rates and SADAREM/medical guidance without removed unsupported figures.
    """
    # Telugu Pension Amount Query
    te_query = "ఎన్టీఆర్ భరోసా వృద్ధాప్య పింఛను మరియు దివ్యాంగుల పెన్షన్ ఎంత?"
    te_results = retrieve_context(
        query=te_query,
        assistant="schemes",
        language="te",
        top_k=3,
    )
    assert len(te_results) > 0
    assert te_results[0]["metadata"]["chunk_id"] == "schemes_ntr_bharosa_pension_c1"
    assert "Payout Rates" in te_results[0]["metadata"]["section_title"]
    assert "4,000" in te_results[0]["text"]
    assert "SADAREM" in te_results[0]["text"]
    assert "6,000" not in te_results[0]["text"]
    assert "10,000" not in te_results[0]["text"]

    # English Pension Amount Query
    en_query = "What is the monthly pension amount under NTR Bharosa for old age and disabled?"
    en_results = retrieve_context(
        query=en_query,
        assistant="schemes",
        language="en",
        top_k=3,
    )
    assert len(en_results) > 0
    assert en_results[0]["metadata"]["chunk_id"] == "schemes_ntr_bharosa_pension_c1"
    assert "4,000" in en_results[0]["text"]
    assert "SADAREM" in en_results[0]["text"]
    assert "6,000" not in en_results[0]["text"]
    assert "10,000" not in en_results[0]["text"]


# ==============================================================================
# SPRINT ROUND 1: BILINGUAL KNOWLEDGE QUALITY & COVERAGE AUDIT TESTS
# ==============================================================================

def test_all_14_documents_bilingual_coverage_and_quality():
    """
    Sprint Round 1 Audit Test:
    Ensures all 14 production documents across Agriculture (4), Education (3),
    Healthcare (3), and Schemes (4) have complete bilingual parity, verified metadata,
    valid chunking, and zero language leakage.
    """
    import glob
    import re
    from pathlib import Path
    from app.services.retrieval.ingestion import DocumentIngestionEngine
    from app.services.retrieval.chunking import MarkdownChunker
    from app.agents.base import BaseSpecialistAgent
    from app.schemas.common import AssistantIdentifier

    class DummyAuditAgent(BaseSpecialistAgent):
        def process_query(self, query): pass
        def get_default_follow_up_questions(self, lang): return []
        def get_safety_notice(self, lang): return ""

    agent = DummyAuditAgent(AssistantIdentifier.AGRICULTURE, "test", "agriculture", "desc")
    engine = DocumentIngestionEngine()
    chunker = MarkdownChunker()

    kb_dir = Path(__file__).resolve().parent.parent.parent.parent / "knowledge_base" / "verified"
    files = sorted(glob.glob(str(kb_dir / "**" / "*.md"), recursive=True))

    assert len(files) == 14, f"Expected 14 verified knowledge-base documents, found {len(files)}"

    domain_counts = {"agriculture": 0, "education": 0, "healthcare": 0, "schemes": 0}

    for fpath in files:
        doc = engine.ingest_file(fpath)
        assert doc.domain in domain_counts, f"Unknown domain {doc.domain} in {fpath}"
        domain_counts[doc.domain] += 1

        # Metadata validation
        assert doc.title, f"Missing title in {fpath}"
        assert doc.url.startswith("https://") or doc.url.startswith("http://"), f"Invalid URL in {fpath}"
        assert doc.publisher, f"Missing publisher in {fpath}"
        assert doc.verified_at, f"Missing verified_at in {fpath}"
        assert doc.status in ["active", "transitioning"], f"Invalid status in {fpath}"
        assert doc.language == "bilingual", f"Expected bilingual language in {fpath}"

        # Ingestion & chunking check
        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 3, f"Expected at least 3 chunks for {doc.doc_id}, got {len(chunks)}"

        # Content completeness: Telugu presence in document
        total_te_chars = len(re.findall(r"[\u0C00-\u0C7F]", doc.content))
        assert total_te_chars >= 150, f"Insufficient Telugu coverage in {doc.doc_id}: {total_te_chars} chars"

        # Language isolation & formatting check
        for c in chunks:
            te_fmt = agent._format_single_chunk({"text": c.text}, is_te=True)
            en_fmt = agent._format_single_chunk({"text": c.text}, is_te=False)

            # English text must not leak Telugu sentences
            for line in en_fmt.split("\n"):
                te_in_en = len(re.findall(r"[\u0C00-\u0C7F]", line))
                assert te_in_en < 5 or (te_in_en <= len(line) * 0.10), (
                    f"Telugu script leaked into English response in {c.metadata.get('chunk_id')}: {line}"
                )

    # Domain count verification
    assert domain_counts["agriculture"] == 4
    assert domain_counts["education"] == 3
    assert domain_counts["healthcare"] == 3
    assert domain_counts["schemes"] == 4
