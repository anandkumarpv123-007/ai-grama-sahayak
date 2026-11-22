"""
Unit tests for text chunking and metadata preservation.
Ensures source metadata (title, URL, publisher, verified_at, domain) is preserved
intact on every chunk without truncation or data loss.
"""

import pytest
from app.services.retrieval.chunking import MarkdownChunker
from app.services.retrieval.models import IngestedDocument


@pytest.fixture
def sample_document():
    content = """# Main Scheme Title

## 1. Overview
This is the overview paragraph describing the primary purpose of the public service scheme.
It provides critical financial assistance to eligible citizens.

## 2. Benefits and Assistance
Eligible beneficiaries receive Rs. 15,000 per year directly through DBT.
Installments are released in three stages throughout the academic year.

## 3. Eligibility Criteria
Applicants must reside in Andhra Pradesh and possess an active Rice Card.
Minimum attendance is 75%.
"""
    return IngestedDocument(
        doc_id="test_doc_001",
        title="Sample Scheme Title",
        content=content,
        domain="education",
        url="https://schooledu.ap.gov.in/sample",
        publisher="Department of School Education, GoAP",
        verified_at="2026-11-21",
        language="en",
        state="Andhra Pradesh",
        district="Kakinada",
        status="active",
        metadata={"category": "Scholarship"},
    )


def test_chunking_metadata_preservation(sample_document):
    chunker = MarkdownChunker(target_chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_document(sample_document)

    assert len(chunks) >= 3
    for idx, chunk in enumerate(chunks):
        # Metadata must be strictly preserved on every chunk
        assert chunk.title == "Sample Scheme Title"
        assert chunk.url == "https://schooledu.ap.gov.in/sample"
        assert chunk.publisher == "Department of School Education, GoAP"
        assert chunk.verified_at == "2026-11-21"
        assert chunk.metadata["domain"] == "education"
        assert chunk.metadata["state"] == "Andhra Pradesh"
        assert chunk.metadata["district"] == "Kakinada"
        assert chunk.metadata["status"] == "active"
        assert chunk.metadata["category"] == "Scholarship"
        assert chunk.metadata["chunk_id"] == f"test_doc_001_c{idx}"
        assert len(chunk.text) > 0


def test_section_splitting(sample_document):
    chunker = MarkdownChunker(target_chunk_size=1000)
    chunks = chunker.chunk_document(sample_document)

    section_titles = [c.metadata.get("section_title") for c in chunks]
    assert any("Overview" in t for t in section_titles)
    assert any("Benefits and Assistance" in t for t in section_titles)
    assert any("Eligibility Criteria" in t for t in section_titles)


def test_chunk_to_dict_format(sample_document):
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document(sample_document)
    chunk_dict = chunks[0].to_dict()

    # Must contain required keys for Member 1 compatibility
    assert "text" in chunk_dict
    assert "title" in chunk_dict
    assert "url" in chunk_dict
    assert "publisher" in chunk_dict
    assert "verified_at" in chunk_dict
    assert "score" in chunk_dict
    assert "source" in chunk_dict
    assert "metadata" in chunk_dict

    # Check nested source dictionary matching api_contracts.md Section 3
    source_obj = chunk_dict["source"]
    assert source_obj["title"] == "Sample Scheme Title"
    assert source_obj["url"] == "https://schooledu.ap.gov.in/sample"
    assert source_obj["publisher"] == "Department of School Education, GoAP"
    assert source_obj["verified_at"] == "2026-11-21"


def test_empty_document_chunking():
    doc = IngestedDocument(
        doc_id="empty_doc",
        title="Empty",
        content="   ",
        domain="agriculture",
        url="https://example.gov",
        publisher="Govt",
        verified_at="2026-11-21",
    )
    chunker = MarkdownChunker()
    chunks = chunker.chunk_document(doc)
    assert chunks == []
