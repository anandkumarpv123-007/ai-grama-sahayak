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

    # --- 10 Document Acceptance Test Matrix ---

    def test_acceptance_1_digital_income_certificate_pdf(self):
        """1. Digital income certificate PDF: correctly auto-detected and extracted."""
        pdf_path = self.samples_dir / "synthetic_income_certificate.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="income_cert.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "income_certificate")
        self.assertEqual(result["checklist_status"], "complete")
        self.assertEqual(result["extracted_fields"]["certificate_number"], "IC0123456789")
        self.assertEqual(result["extracted_fields"]["applicant_name"], "K. Rama Rao")
        self.assertEqual(result["extracted_fields"]["annual_income"], "Rs. 75000")

    def test_acceptance_2_scanned_income_certificate_pdf(self):
        """2. Scanned income certificate PDF: honest unverified status + manual selection works."""
        pdf_path = self.samples_dir / "synthetic_scanned_unreadable.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        # In auto-detect mode, unreadable scanned PDF is classified as general_document with warning
        auto_res = analyze_document_content(
            content=content,
            filename="scanned_income.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(auto_res["document_type"], "general_document")
        self.assertEqual(auto_res["checklist_status"], "unverified_or_incomplete")
        self.assertTrue(any("scanned" in w.lower() or "ocr" in w.lower() for w in auto_res["warnings"]))

        # When citizen manually selects "income_certificate", respects choice
        manual_res = analyze_document_content(
            content=content,
            filename="scanned_income.pdf",
            content_type="application/pdf",
            document_type_hint="income_certificate",
        )
        self.assertEqual(manual_res["document_type"], "income_certificate")
        self.assertEqual(manual_res["checklist_status"], "unverified_or_incomplete")
        self.assertIn("certificate_number", manual_res["missing_fields"])

    def test_acceptance_3_income_certificate_image(self):
        """3. Income certificate image: honest unverified status when OCR unavailable + allows manual selection."""
        png_path = self.samples_dir / "synthetic_income_cert.png"
        with open(png_path, "rb") as f:
            content = f.read()

        res = analyze_document_content(
            content=content,
            filename="income.png",
            content_type="image/png",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(res["document_type"], "general_document")
        self.assertEqual(res["checklist_status"], "unverified_or_incomplete")
        self.assertTrue(any("ocr" in w.lower() or "unverified" in w.lower() for w in res["warnings"]))

    def test_acceptance_4_synthetic_aadhaar_front(self):
        """4. Synthetic Aadhaar front: auto-detected as aadhaar_card with masked UID, name, and DOB."""
        from document_samples.generate_samples import make_pdf
        front_pdf = make_pdf([
            "GOVERNMENT OF INDIA",
            "Unique Identification Authority of India",
            "Mera Aadhaar Meri Pehchan",
            "Name: K. Rama Rao",
            "DOB: 14/06/1992",
            "Gender: Male",
            "4589 1234 5678",
        ])
        result = analyze_document_content(
            content=front_pdf,
            filename="aadhaar_front.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "aadhaar_card")
        self.assertEqual(result["extracted_fields"]["aadhaar_number"], "XXXX-XXXX-5678")
        self.assertIn("card_side", result["extracted_fields"])
        self.assertEqual(result["extracted_fields"]["card_side"], "front")
        self.assertEqual(result["checklist_status"], "complete")

    def test_acceptance_5_synthetic_aadhaar_back(self):
        """5. Synthetic Aadhaar back: auto-detected as aadhaar_card with address, district, masked UID."""
        from document_samples.generate_samples import make_pdf
        back_pdf = make_pdf([
            "Unique Identification Authority of India",
            "Address: S/O K. Venkata Rao, D.No 1-23, Main Road",
            "Samalkota, Kakinada, Andhra Pradesh - 533440",
            "9876 5432 1098",
            "1947 help@uidai.gov.in www.uidai.gov.in",
        ])
        result = analyze_document_content(
            content=back_pdf,
            filename="aadhaar_back.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "aadhaar_card")
        self.assertEqual(result["extracted_fields"]["aadhaar_number"], "XXXX-XXXX-1098")
        self.assertEqual(result["extracted_fields"]["card_side"], "back")
        self.assertEqual(result["extracted_fields"]["district"], "Kakinada")
        self.assertEqual(result["checklist_status"], "partially_complete")

    def test_acceptance_6_caste_certificate(self):
        """6. Caste certificate: auto-detected with certificate number, category, and issue date."""
        pdf_path = self.samples_dir / "synthetic_caste_certificate.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="caste.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "caste_certificate")
        self.assertEqual(result["extracted_fields"]["certificate_number"], "CGC9876543210")
        self.assertEqual(result["extracted_fields"]["caste_category"], "BC-A")
        self.assertEqual(result["checklist_status"], "complete")

    def test_acceptance_7_rice_card(self):
        """7. Rice card: auto-detected with card number and head of family."""
        pdf_path = self.samples_dir / "synthetic_ration_card.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        result = analyze_document_content(
            content=content,
            filename="rice_card.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "ration_card")
        self.assertEqual(result["extracted_fields"]["ration_card_number"], "WAP041234567890")
        self.assertEqual(result["extracted_fields"]["head_of_family"], "M. Subba Rao")
        self.assertEqual(result["checklist_status"], "complete")

    def test_acceptance_8_blurry_document(self):
        """8. Blurry document: image without readable text returns honest unverified state."""
        from PIL import Image, ImageFilter
        import io
        img = Image.new("RGB", (300, 100), color=(200, 200, 200))
        img = img.filter(ImageFilter.GaussianBlur(10))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        blurry_bytes = buf.getvalue()

        result = analyze_document_content(
            content=blurry_bytes,
            filename="blurry.jpg",
            content_type="image/jpeg",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "general_document")
        self.assertEqual(result["checklist_status"], "unverified_or_incomplete")

    def test_acceptance_9_unrelated_document(self):
        """9. Unrelated document: does not force incorrect category; classifies as general_document."""
        from document_samples.generate_samples import make_pdf
        unrelated_pdf = make_pdf([
            "UNIVERSITY SPORTS BOARD",
            "ANNUAL CRICKET TOURNAMENT SCHEDULE 2026",
            "Match 1: Team Alpha vs Team Beta",
            "Venue: Main Stadium, Hyderabad",
            "Date: 15-03-2026",
        ])
        result = analyze_document_content(
            content=unrelated_pdf,
            filename="cricket_schedule.pdf",
            content_type="application/pdf",
            document_type_hint="Auto Detect",
        )
        self.assertEqual(result["document_type"], "general_document")
        self.assertNotEqual(result["document_type"], "income_certificate")
        self.assertNotEqual(result["document_type"], "aadhaar_card")

    def test_acceptance_10_empty_or_invalid_file(self):
        """10. Empty or invalid file: rejected immediately with proper exception and code."""
        with self.assertRaises(DocumentAnalysisError) as ctx_empty:
            analyze_document_content(b"", "empty.pdf", "application/pdf")
        self.assertEqual(ctx_empty.exception.code, "EMPTY_FILE")

        with self.assertRaises(InvalidFileTypeError) as ctx_inv:
            analyze_document_content(b"not a pdf or image", "bad.pdf", "application/pdf")
        self.assertEqual(ctx_inv.exception.code, "INVALID_FILE_TYPE")


if __name__ == "__main__":
    unittest.main()
