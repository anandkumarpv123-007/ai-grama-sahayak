import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

QUERIES = [
    {
        "num": 1,
        "label": "English Agriculture (Annadata Sukhibhava)",
        "payload": {
            "message": "What is the financial assistance provided to farmers under Annadata Sukhibhava PM Kisan?",
            "assistant": "agriculture",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
        "expected_source": "annadathasukhibhava.ap.gov.in",
        "expected_term": "Annadata Sukhibhava",
    },
    {
        "num": 2,
        "label": "Telugu Agriculture (Annadata Sukhibhava)",
        "payload": {
            "message": "అన్నదాత సుఖీభవ పథకం కింద రైతులకు ఎంత మొత్తం సాయం అందుతుంది?",
            "assistant": "agriculture",
            "language": "te",
            "state": "Andhra Pradesh",
            "district": "Kakinada",
        },
        "expected_source": "annadathasukhibhava.ap.gov.in",
        "expected_term": "అన్నదాత సుఖీభవ",
    },
    {
        "num": 3,
        "label": "Healthcare (Dr. NTR Vaidya Seva)",
        "payload": {
            "message": "What is the annual coverage limit under Dr NTR Vaidya Seva Aarogyasri in AP hospitals?",
            "assistant": "healthcare",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Visakhapatnam",
        },
        "expected_source": "drntrvaidyaseva.ap.gov.in",
        "expected_term": "Vaidya Seva",
    },
    {
        "num": 4,
        "label": "Education (Thalliki Vandanam)",
        "payload": {
            "message": "What are the eligibility criteria and attendance requirements for Thalliki Vandanam?",
            "assistant": "education",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Guntur",
        },
        "expected_source": "schooledu.ap.gov.in",
        "expected_term": "Thalliki Vandanam",
    },
    {
        "num": 5,
        "label": "Government Schemes (NTR Bharosa Pension)",
        "payload": {
            "message": "What is the monthly pension amount under NTR Bharosa for senior citizens and disabled persons?",
            "assistant": "schemes",
            "language": "en",
            "state": "Andhra Pradesh",
            "district": "Krishna",
        },
        "expected_source": "sspensions.ap.gov.in",
        "expected_term": "NTR Bharosa",
    },
    {
        "num": 6,
        "label": "Unrelated Query (Must NOT fabricate government citations)",
        "payload": {
            "message": "How to mine Bitcoin cryptocurrency on a home computer?",
            "assistant": "schemes",
            "language": "en",
        },
        "expected_source": None,
        "expected_term": "Verified official information is currently unavailable",
    },
]


@pytest.mark.parametrize("query_case", QUERIES, ids=[q["label"] for q in QUERIES])
def test_real_rag_chat_verification(query_case):
    res = client.post("/api/chat", json=query_case["payload"])
    assert res.status_code == 200
    data = res.json()

    assert data["assistant"] == query_case["payload"]["assistant"]
    assert data["language"] == query_case["payload"]["language"]

    if query_case["expected_source"] is not None:
        assert len(data["sources"]) > 0, "Expected at least one verified source cited"
        assert any(query_case["expected_source"] in s["url"] for s in data["sources"])
        assert query_case["expected_term"].lower() in data["answer"].lower()
        assert not data["needs_follow_up"]
    else:
        assert len(data["sources"]) == 0, "Unrelated query must not cite fabricated sources"
        assert "Verified official information is currently unavailable" in data["answer"]
        assert data["needs_follow_up"]
