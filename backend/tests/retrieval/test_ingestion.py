"""
Unit tests for document ingestion engine.
Tests parsing of Markdown, Plain Text, HTML, and PDF formats,
frontmatter extraction, manifest synchronization, and demo isolation.
"""

import os
import tempfile
import pytest
from pathlib import Path
from app.services.retrieval.ingestion import DocumentIngestionEngine


@pytest.fixture
def temp_kb():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        verified_dir = tmp_path / "verified" / "agriculture"
        demo_dir = tmp_path / "demo"
        verified_dir.mkdir(parents=True)
        demo_dir.mkdir(parents=True)

        # 1. Verified Markdown file
        md_file = verified_dir / "test_scheme.md"
        md_file.write_text(
            """---
id: test_agri_001
title: "Test Agri Scheme"
domain: agriculture
url: "https://agri.ap.gov.in/test"
publisher: "AP Agri Dept"
verified_at: "2026-11-21"
status: active
---

# Test Agri Scheme

This is a test scheme for verified farmers.
Eligibility requires resident status and rice card.
""",
            encoding="utf-8",
        )

        # 2. Text file
        txt_file = verified_dir / "sample.txt"
        txt_file.write_text(
            """---
id: test_txt_002
title: "Sample Text Policy"
domain: agriculture
url: "https://agri.ap.gov.in/policy"
publisher: "AP Agri Dept"
verified_at: "2026-11-21"
status: active
---

General agricultural guidelines for testing.
""",
            encoding="utf-8",
        )

        # 3. HTML file
        html_file = verified_dir / "page.html"
        html_file.write_text(
            """<!DOCTYPE html>
<html>
<head><title>Test HTML Scheme</title></head>
<body>
<p>Official guidelines published on HTML portal.</p>
</body>
</html>
""",
            encoding="utf-8",
        )

        # 4. Demo fixture file
        demo_file = demo_dir / "synthetic_fixture.md"
        demo_file.write_text(
            """---
id: demo_fixture_999
title: "Synthetic Demo Fixture"
domain: agriculture
url: "https://demo.example.gov"
publisher: "Synthetic Authority"
verified_at: "2026-11-21"
status: demo
---

This is a synthetic fixture that must never be loaded in production.
""",
            encoding="utf-8",
        )

        # 5. Manifest CSV
        manifest_file = tmp_path / "sources_manifest.csv"
        manifest_file.write_text(
            "domain,title,publisher,url,language,date_checked,status,notes\n"
            "agriculture,Test Agri Scheme,AP Agri Dept,https://agri.ap.gov.in/test,en,2026-11-21,active,Test note\n",
            encoding="utf-8",
        )

        yield tmp_path


def test_markdown_ingestion(temp_kb):
    engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))
    file_path = temp_kb / "verified" / "agriculture" / "test_scheme.md"
    doc = engine.ingest_file(file_path)

    assert doc is not None
    assert doc.doc_id == "test_agri_001"
    assert doc.title == "Test Agri Scheme"
    assert doc.domain == "agriculture"
    assert doc.url == "https://agri.ap.gov.in/test"
    assert doc.publisher == "AP Agri Dept"
    assert doc.verified_at == "2026-11-21"
    assert doc.status == "active"
    assert "This is a test scheme for verified farmers." in doc.content


def test_text_ingestion(temp_kb):
    engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))
    file_path = temp_kb / "verified" / "agriculture" / "sample.txt"
    doc = engine.ingest_file(file_path)

    assert doc is not None
    assert doc.doc_id == "test_txt_002"
    assert "General agricultural guidelines" in doc.content


def test_html_ingestion(temp_kb):
    engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))
    file_path = temp_kb / "verified" / "agriculture" / "page.html"
    doc = engine.ingest_file(file_path)

    assert doc is not None
    assert doc.title == "Test HTML Scheme"
    assert "Official guidelines published on HTML portal." in doc.content


def test_pdf_ingestion(temp_kb):
    # Create a simple synthetic PDF using PyMuPDF (fitz)
    pdf_path = temp_kb / "verified" / "agriculture" / "test_document.pdf"
    try:
        import fitz
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        page.insert_text((50, 72), "Official PDF Guidelines for Farmer Assistance 2026.")
        pdf_doc.save(str(pdf_path))
        pdf_doc.close()

        engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))
        doc = engine.ingest_file(pdf_path)

        assert doc is not None
        assert "Official PDF Guidelines" in doc.content
    except ImportError:
        pytest.skip("PyMuPDF / fitz not available for PDF generation")


def test_manifest_loading(temp_kb):
    engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))
    manifest = engine.load_manifest()

    assert "https://agri.ap.gov.in/test" in manifest
    row = manifest["https://agri.ap.gov.in/test"]
    assert row["title"] == "Test Agri Scheme"
    assert row["status"] == "active"


def test_demo_isolation_strict(temp_kb):
    engine = DocumentIngestionEngine(kb_base_dir=str(temp_kb))

    # Production ingestion: verified only, exclude demo
    prod_docs = engine.ingest_directory(subdir="verified", include_demo=False)
    prod_ids = [d.doc_id for d in prod_docs]
    assert "test_agri_001" in prod_ids
    assert "demo_fixture_999" not in prod_ids

    # Explicit demo ingestion
    demo_docs = engine.ingest_directory(subdir="demo", include_demo=True)
    demo_ids = [d.doc_id for d in demo_docs]
    assert "demo_fixture_999" in demo_ids
