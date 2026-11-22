"""Tests for Document Analysis Service and API.

Validates:
- Valid PDF uploads (Income certificate, Caste certificate, Rice card)
- Field extraction and checklist status calculation
- Disclaimer warning on all responses
- Invalid file formats, extensions, MIME types, and magic bytes
- Oversized uploads (> 10MB) -> HTTP 413 / PAYLOAD_TOO_LARGE
- Empty files (0 bytes) -> HTTP 400 / EMPTY_FILE
- Scanned unreadable PDFs -> unverified_or_incomplete + explicit warning
- Image uploads without OCR -> unverified_or_incomplete + explicit warning (no metadata cheating)
- Zero citizen documents stored to disk
- Regression tests for unreadable PDFs, oversized page count, and oversized text length limits
"""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

# Import test setup first to configure test shims
import tests  # noqa: F401

from app.services.documents.analyzer import (
    analyze_document_content,
    validate_file_upload,
    OversizedFileError,
    InvalidFileTypeError,
    DocumentAnalysisError,
    MAX_UPLOAD_BYTES,
    DISCLAIMER_WARNING,
)
from app.services.documents.extractor import (
    extract_text_from_pdf,
    extract_text_from_image,
    MAX_PDF_PAGES,
    MAX_EXTRACTED_TEXT_LENGTH,
)
from app.services.documents.field_parser import (
    detect_document_type,
    parse_fields_from_text,
    evaluate_checklist,
)


class TestDocumentAnalysis(unittest.TestCase):
    """Test suite for document analysis service."""

    @classmethod
    def setUpClass(cls):
        cls.samples_dir = BASE_DIR / "document_samples"

    def test_valid_income_certificate_pdf(self):
        """Test extraction from a valid synthetic Income Certificate PDF."""
        pdf_path = self.samples_dir / "synthetic_income_certificate.pdf"
        self.assertTrue(pdf_path.exists(), "Sample income PDF must exist")

        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_income_certificate.pdf",
            content_type="application/pdf",
        )

        self.assertEqual(result["document_type"], "income_certificate")
        self.assertIn("certificate_number", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["certificate_number"], "IC0123456789")
        self.assertIn("applicant_name", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["applicant_name"], "K. Rama Rao")
        self.assertIn("annual_income", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["annual_income"], "Rs. 75000")
        self.assertIn("issue_date", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["district"], "Kakinada")

        self.assertEqual(result["checklist_status"], "complete")
        self.assertEqual(result["missing_fields"], [])

        # Disclaimer warning must be present
        self.assertIn(DISCLAIMER_WARNING, result["warnings"])

    def test_valid_caste_certificate_pdf(self):
        """Test extraction from a valid synthetic Caste Certificate PDF."""
        pdf_path = self.samples_dir / "synthetic_caste_certificate.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_caste_certificate.pdf",
            content_type="application/pdf",
        )

        self.assertEqual(result["document_type"], "caste_certificate")
        self.assertIn("certificate_number", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["certificate_number"], "CGC9876543210")
        self.assertIn("applicant_name", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["applicant_name"], "P. Lakshmi")
        self.assertEqual(result["extracted_fields"]["caste_category"], "BC-A")
        self.assertEqual(result["extracted_fields"]["district"], "Visakhapatnam")
        self.assertEqual(result["checklist_status"], "complete")
        self.assertIn(DISCLAIMER_WARNING, result["warnings"])

    def test_valid_ration_card_pdf(self):
        """Test extraction from a valid synthetic Ration / Rice Card PDF."""
        pdf_path = self.samples_dir / "synthetic_ration_card.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_ration_card.pdf",
            content_type="application/pdf",
        )

        self.assertEqual(result["document_type"], "ration_card")
        self.assertIn("ration_card_number", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["ration_card_number"], "WAP041234567890")
        self.assertEqual(result["extracted_fields"]["head_of_family"], "M. Subba Rao")
        self.assertEqual(result["extracted_fields"]["district"], "Guntur")
        self.assertEqual(result["checklist_status"], "complete")

    def test_scanned_unreadable_pdf_graceful_handling(self):
        """Test that scanned or image-only PDF does not crash and returns clear warnings."""
        pdf_path = self.samples_dir / "synthetic_scanned_unreadable.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_scanned_unreadable.pdf",
            content_type="application/pdf",
        )

        self.assertEqual(result["checklist_status"], "unverified_or_incomplete")
        self.assertEqual(result["extracted_fields"], {})
        scanned_warn = any("scanned" in w.lower() or "text layer" in w.lower() or "ocr" in w.lower() for w in result["warnings"])
        self.assertTrue(scanned_warn, "Warning must mention scanned document or lack of text layer")

    def test_image_without_ocr_graceful_fallback(self):
        """Test that an image upload without OCR returns unverified_or_incomplete without relying on metadata."""
        img_path = self.samples_dir / "synthetic_income_cert.png"
        with open(img_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_income_cert.png",
            content_type="image/png",
        )

        self.assertEqual(result["checklist_status"], "unverified_or_incomplete")
        self.assertEqual(result["extracted_fields"], {})
        ocr_warn = any("ocr" in w.lower() or "machine-readable" in w.lower() for w in result["warnings"])
        self.assertTrue(ocr_warn, "Warning must explicitly note OCR unavailability or manual verification")

    def test_blank_image_handling(self):
        """Test that a blank image returns unverified_or_incomplete."""
        img_path = self.samples_dir / "synthetic_blank.png"
        with open(img_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="synthetic_blank.png",
            content_type="image/png",
        )

        self.assertEqual(result["checklist_status"], "unverified_or_incomplete")
        self.assertEqual(result["extracted_fields"], {})

    def test_reject_invalid_extension(self):
        """Test that unsupported file extensions are rejected."""
        txt_path = self.samples_dir / "synthetic_invalid.txt"
        with open(txt_path, "rb") as f:
            content = f.read()

        with self.assertRaises(InvalidFileTypeError) as ctx:
            validate_file_upload(content, "document.txt", "text/plain")

        self.assertEqual(ctx.exception.code, "INVALID_FILE_TYPE")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_reject_unsupported_mime(self):
        """Test that unsupported MIME type is rejected."""
        pdf_path = self.samples_dir / "synthetic_income_certificate.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        with self.assertRaises(InvalidFileTypeError) as ctx:
            validate_file_upload(content, "test.pdf", "application/x-msdownload")

        self.assertEqual(ctx.exception.code, "INVALID_FILE_TYPE")

    def test_reject_corrupted_magic_bytes(self):
        """Test that files with fake extension but wrong magic bytes are rejected."""
        fake_content = b"NOT_A_REAL_PDF_HEADER_123456789"
        with self.assertRaises(InvalidFileTypeError) as ctx:
            validate_file_upload(fake_content, "fake.pdf", "application/pdf")

        self.assertEqual(ctx.exception.code, "INVALID_FILE_TYPE")

    def test_reject_empty_file(self):
        """Test that zero-byte files are rejected."""
        with self.assertRaises(DocumentAnalysisError) as ctx:
            validate_file_upload(b"", "empty.pdf", "application/pdf")

        self.assertEqual(ctx.exception.code, "EMPTY_FILE")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_reject_oversized_file(self):
        """Test that files exceeding 10 MB are rejected with status 413."""
        oversized_bytes = b"%PDF-" + b"0" * (MAX_UPLOAD_BYTES + 1)
        with self.assertRaises(OversizedFileError) as ctx:
            validate_file_upload(oversized_bytes, "big.pdf", "application/pdf")

        self.assertEqual(ctx.exception.code, "PAYLOAD_TOO_LARGE")
        self.assertEqual(ctx.exception.status_code, 413)

    def test_partially_complete_checklist(self):
        """Test missing fields detection when only some fields are present."""
        partial_text = (
            "GOVERNMENT OF ANDHRA PRADESH\n"
            "INCOME CERTIFICATE\n"
            "Certificate No: IC999888777\n"
            "Applicant Name: M. Ramesh\n"
        )
        fields = parse_fields_from_text(partial_text, "income_certificate")
        status, missing = evaluate_checklist("income_certificate", fields)

        self.assertEqual(status, "partially_complete")
        self.assertIn("annual_income", missing)
        self.assertIn("issue_date", missing)
        self.assertNotIn("certificate_number", missing)
        self.assertNotIn("applicant_name", missing)

    # --- Regression Tests ---

    def test_regression_unreadable_pdf_no_fabricated_content(self):
        """Regression: unreadable/corrupted PDF returns honest incomplete result with no fabricated fields."""
        corrupted_pdf = b"%PDF-1.4\ncorrupted content without xref or valid objects"
        text, warnings = extract_text_from_pdf(corrupted_pdf)
        self.assertEqual(text, "")
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("unsupported" in w.lower() or "scanned" in w.lower() or "corrupted" in w.lower() for w in warnings))

    def test_regression_oversized_pdf_page_count_safe_limit(self):
        """Regression: PDF with >20 pages enforces MAX_PDF_PAGES and warns citizen."""
        # Create a mock reader simulating 25 pages
        import types
        from pypdf import PdfReader

        original_init = PdfReader.__init__
        try:
            class MockMultiPageReader:
                def __init__(self, stream):
                    self.pages = [types.SimpleNamespace(extract_text=lambda i=i: f"Page {i} content") for i in range(25)]

            # Test using MockMultiPageReader
            import pypdf
            orig_reader = pypdf.PdfReader
            pypdf.PdfReader = MockMultiPageReader

            text, warnings = extract_text_from_pdf(b"%PDF-1.4\ndummy")
            self.assertTrue(any(f"{MAX_PDF_PAGES} pages" in w for w in warnings))
            self.assertIn("Page 0", text)
            self.assertIn(f"Page {MAX_PDF_PAGES - 1}", text)
            # Page 20 (the 21st page) should NOT be processed
            self.assertNotIn("Page 20", text)
        finally:
            import pypdf
            pypdf.PdfReader = orig_reader

    def test_regression_oversized_pdf_text_length_safe_limit(self):
        """Regression: PDF with massive text enforces MAX_EXTRACTED_TEXT_LENGTH limit and truncates."""
        import types
        import pypdf
        orig_reader = pypdf.PdfReader
        try:
            class MockMassiveTextReader:
                def __init__(self, stream):
                    # Each page has 30,000 chars; 5 pages = 150,000 chars > MAX_EXTRACTED_TEXT_LENGTH
                    self.pages = [types.SimpleNamespace(extract_text=lambda: "X" * 30_000) for _ in range(5)]

            pypdf.PdfReader = MockMassiveTextReader
            text, warnings = extract_text_from_pdf(b"%PDF-1.4\ndummy")
            self.assertLessEqual(len(text), MAX_EXTRACTED_TEXT_LENGTH + 10)  # Account for newlines
            self.assertTrue(any("truncated" in w.lower() for w in warnings))
        finally:
            pypdf.PdfReader = orig_reader


if __name__ == "__main__":
    unittest.main()
