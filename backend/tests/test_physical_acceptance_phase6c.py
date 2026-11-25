"""Phase 6C.1: Physical Acceptance Verification Tests.

Validates:
1. Educational Assistant & Generic Scheme Discovery:
   - APSSDC query handling (English and Telugu) with official referral and no invented courses
   - Generic scholarship discovery with typo tolerance (availble schoalrship, available scholarships,
     What scholarships can I apply for?, నాకు అందుబాటులో ఉన్న స్కాలర్‌షిప్‌లు ఏమిటి?)
   - Structured tiered scholarship guidance across school and higher education + prompt for level
2. Conversational Assistant to Nearby Services Integration:
   - Intent detection for RBK (agriculture), Grama Sachivalayam (secretariat), PHC/CHC (community_health_centre),
     and general hospital (hospital) in English and Telugu
   - Inclusion of actionable service_action in API response
   - Honest explanation of RBK and Grama Sachivalayam village-level directory scope
   - Preservation of clinical emergency safety routing (108/104)
3. Local Image OCR & WebP Document Handling:
   - Text and field extraction from synthetic PNG, JPG, and WebP certificates
   - Scanned PDF text extraction via embedded OCR
   - Graceful fallback on unreadable/blurry images
   - Strict Aadhaar masking (XXXX-XXXX-1234)
   - WebP MIME and magic bytes validation
"""

import io
import os
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import LanguageCode, AssistantIdentifier
from app.api.chat import (
    _detect_apssdc_query,
    _handle_apssdc_query,
    _detect_generic_scholarship_query,
    _handle_generic_scholarship_query,
    _handle_nearby_service_query,
)
from app.services.documents.analyzer import (
    analyze_document_content,
    validate_file_upload,
    InvalidFileTypeError,
)
from app.services.documents.extractor import (
    extract_text_from_image,
    extract_text_from_pdf,
)

client = TestClient(app)


class TestPhysicalAcceptancePhase6C(unittest.TestCase):
    """Test suite for Phase 6C.1 physical acceptance corrections."""

    # -------------------------------------------------------------
    # TASK 1: APSSDC and Generic Scholarship Discovery Tests
    # -------------------------------------------------------------

    def test_apssdc_technical_training_query_en(self):
        """Query: What free technical skill training programs are offered by APSSDC?"""
        query = "What free technical skill training programs are offered by APSSDC?"
        self.assertTrue(_detect_apssdc_query(query))

        res = client.post(
            "/api/chat",
            json={
                "message": query,
                "language": "en",
                "assistant": "education",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Must not fabricate active course batches or empanelled centers
        self.assertIn("https://www.apssdc.in", data["answer"])
        self.assertIn("https://www.ap.gov.in", data["answer"])
        self.assertIn("Grama / Ward Sachivalayam", data["answer"])
        # Distinguishes skill training from financial scholarships
        self.assertIn("Scholarships", data["answer"])
        self.assertTrue(data["needs_follow_up"])
        self.assertTrue(len(data["follow_up_questions"]) >= 2)

    def test_apssdc_technical_training_query_te(self):
        """Telugu APSSDC query handling."""
        query = "APSSDC ఉచిత సాంకేతిక నైపుణ్య శిక్షణ కార్యక్రమాలు ఏమిటి?"
        self.assertTrue(_detect_apssdc_query(query))

        res = client.post(
            "/api/chat",
            json={
                "message": query,
                "language": "te",
                "assistant": "education",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("https://www.apssdc.in", data["answer"])
        self.assertIn("సచివాలయం", data["answer"])
        self.assertIn("స్కిల్ సెన్సస్", data["answer"])

    def test_scholarship_discovery_typo_availble(self):
        """Query with typo: availble schoalrship"""
        query = "availble schoalrship"
        self.assertTrue(_detect_generic_scholarship_query(query))

        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "schemes"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Must present verified education schemes across tiers
        self.assertIn("Thalliki Vandanam", data["answer"])
        self.assertIn("Vidya Deevena", data["answer"])
        self.assertIn("Vasathi Deevena", data["answer"])
        self.assertIn("Samagra Shiksha", data["answer"])
        # Must prompt for education level
        self.assertIn("level of education", data["answer"].lower())

        # Factual safety: must NOT assert flat unverified amounts or unconditional guarantees
        self.assertNotIn("Rs 15,000", data["answer"])
        self.assertNotIn("Rs. 15,000", data["answer"])
        self.assertNotIn("Rs 20,000", data["answer"])
        self.assertNotIn("Rs. 20,000", data["answer"])
        self.assertNotIn("full tuition fee reimbursement for eligible", data["answer"].lower())

    def test_scholarship_discovery_available_scholarships(self):
        """Query: available scholarships"""
        query = "available scholarships"
        self.assertTrue(_detect_generic_scholarship_query(query))

        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "schemes"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Thalliki Vandanam", data["answer"])
        self.assertIn("Vidya Deevena", data["answer"])

    def test_scholarship_discovery_what_scholarships_can_i_apply_for(self):
        """Query: What scholarships can I apply for?"""
        query = "What scholarships can I apply for?"
        self.assertTrue(_detect_generic_scholarship_query(query))

        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "schemes"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Thalliki Vandanam", data["answer"])
        self.assertIn("Vidya Deevena", data["answer"])
        self.assertIn("Vasathi Deevena", data["answer"])

    def test_scholarship_discovery_telugu(self):
        """Query: నాకు అందుబాటులో ఉన్న స్కాలర్‌షిప్‌లు ఏమిటి?"""
        query = "నాకు అందుబాటులో ఉన్న స్కాలర్‌షిప్‌లు ఏమిటి?"
        self.assertTrue(_detect_generic_scholarship_query(query))

        res = client.post(
            "/api/chat",
            json={"message": query, "language": "te", "assistant": "schemes"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("తల్లికి వందనం", data["answer"])
        self.assertIn("విద్యా దీవెన", data["answer"])
        self.assertIn("వసతి దీవెన", data["answer"])
        self.assertIn("సమగ్ర శిక్ష", data["answer"])
        # Asks for education level in Telugu
        self.assertIn("ఏ చదువు చదువుతున్నారు", data["answer"])

        # Factual safety: must NOT assert flat unverified amounts in Telugu
        self.assertNotIn("రూ. 15,000", data["answer"])
        self.assertNotIn("రూ. 20,000", data["answer"])

    # -------------------------------------------------------------
    # TASK 2: Nearby Services Integration Tests
    # -------------------------------------------------------------

    def test_nearby_rythu_bharosa_kendra_en(self):
        """Query: Where is the nearby Rythu Bharosa Kendra?"""
        query = "Where is the nearby Rythu Bharosa Kendra?"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "agriculture"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Actionable frontend action object
        self.assertIsNotNone(data.get("service_action"))
        self.assertEqual(data["service_action"]["action"], "open_nearby")
        self.assertEqual(data["service_action"]["service_type"], "agriculture")

        # Honestly explains village-level directory limitation
        self.assertIn("https://karshak.ap.gov.in", data["answer"])
        self.assertIn("Village Agriculture Assistant", data["answer"])
        self.assertIn("village level", data["answer"].lower())
        # Factual safety: no blanket claim of every revenue village
        self.assertNotIn("every revenue village", data["answer"].lower())

    def test_nearby_rythu_bharosa_kendra_te(self):
        """Query: నాకు దగ్గరలో రైతు భరోసా కేంద్రం ఎక్కడ ఉంది?"""
        query = "నాకు దగ్గరలో రైతు భరోసా కేంద్రం ఎక్కడ ఉంది?"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "te", "assistant": "agriculture"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNotNone(data.get("service_action"))
        self.assertEqual(data["service_action"]["action"], "open_nearby")
        self.assertEqual(data["service_action"]["service_type"], "agriculture")
        self.assertIn("https://karshak.ap.gov.in", data["answer"])
        self.assertIn("వ్యవసాయ సహాయకుడిని", data["answer"])
        # Factual safety: no blanket claim in Telugu
        self.assertNotIn("ప్రతి రెవెన్యూ గ్రామంలోనూ", data["answer"])

    def test_nearby_hospital_en(self):
        """Query: Nearby hospital (with and without district)."""
        # Without district: prompts for district and provides service action
        query = "Nearby hospital"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "healthcare"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNotNone(data.get("service_action"))
        self.assertEqual(data["service_action"]["action"], "open_nearby")
        self.assertEqual(data["service_action"]["service_type"], "hospital")
        self.assertIn("108", data["answer"])

        # With district in request
        res2 = client.post(
            "/api/chat",
            json={
                "message": "Nearby hospital in Kakinada",
                "language": "en",
                "assistant": "healthcare",
                "district": "Kakinada",
            },
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertIn("Government General Hospital (GGH) Kakinada", data2["answer"])
        self.assertEqual(data2["service_action"]["district"], "Kakinada")

    def test_nearby_phc_en(self):
        """Query: Nearby PHC"""
        query = "Nearby PHC"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "healthcare"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNotNone(data.get("service_action"))
        self.assertEqual(data["service_action"]["action"], "open_nearby")
        self.assertEqual(data["service_action"]["service_type"], "community_health_centre")

    def test_nearby_grama_sachivalayam_en(self):
        """Query: Nearby Grama Sachivalayam"""
        query = "Nearby Grama Sachivalayam"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "schemes"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNotNone(data.get("service_action"))
        self.assertEqual(data["service_action"]["action"], "open_nearby")
        self.assertEqual(data["service_action"]["service_type"], "secretariat")
        self.assertIn("https://gramawardsachivalayam.ap.gov.in", data["answer"])

    def test_emergency_takes_priority_over_nearby(self):
        """Clinical emergency (chest pain) must NOT divert to ordinary nearby lookup."""
        query = "I have severe chest pain and breathlessness near hospital"
        res = client.post(
            "/api/chat",
            json={"message": query, "language": "en", "assistant": "healthcare"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("108", data["answer"])
        # Emergency response must have safety notice and immediate dispatch instructions
        self.assertIsNotNone(data["safety_notice"])
        self.assertIn("EMERGENCY", data["safety_notice"].upper())

    # -------------------------------------------------------------
    # TASK 3: Local Image OCR and WebP Handling Tests
    # -------------------------------------------------------------

    def _generate_synthetic_image(self, format_name="PNG") -> bytes:
        """Helper to create a synthetic image certificate with rendered text."""
        img = Image.new("RGB", (900, 300), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((20, 20), "GOVERNMENT OF ANDHRA PRADESH", fill=(0, 0, 0))
        d.text((20, 60), "REVENUE DEPARTMENT - INCOME CERTIFICATE", fill=(0, 0, 0))
        d.text((20, 100), "Certificate Number: IC1234567890", fill=(0, 0, 0))
        d.text((20, 140), "Applicant Name: M. Venkata Raman", fill=(0, 0, 0))
        d.text((20, 180), "Annual Income: Rs. 65,000/-", fill=(0, 0, 0))
        d.text((20, 220), "District: Kakinada", fill=(0, 0, 0))
        d.text((20, 260), "Aadhaar: 1234 5678 9012", fill=(0, 0, 0))

        buf = io.BytesIO()
        img.save(buf, format=format_name)
        return buf.getvalue()

    def test_image_ocr_png(self):
        """Extract text and parse fields from synthetic PNG certificate."""
        content = self._generate_synthetic_image("PNG")
        text, warnings = extract_text_from_image(content, "income.png")
        self.assertTrue(len(text) > 0, "OCR must extract text from PNG")
        self.assertIn("INCOME", text.upper())

        res = analyze_document_content(content, "income.png", "image/png")
        self.assertEqual(res["document_type"], "income_certificate")
        self.assertIn("IC1234567890", res["extracted_fields"].get("certificate_number", ""))
        # Aadhaar must be masked
        if "aadhaar_number" in res["extracted_fields"]:
            self.assertTrue(res["extracted_fields"]["aadhaar_number"].startswith("XXXX-XXXX-"))

    def test_image_ocr_jpeg(self):
        """Extract text and parse fields from synthetic JPEG certificate."""
        content = self._generate_synthetic_image("JPEG")
        text, warnings = extract_text_from_image(content, "income.jpg")
        self.assertTrue(len(text) > 0, "OCR must extract text from JPEG")
        self.assertIn("INCOME", text.upper())

    def test_image_ocr_webp(self):
        """Extract text and parse fields from synthetic WebP certificate."""
        content = self._generate_synthetic_image("WEBP")

        # Validate file upload validator accepts WebP
        norm = validate_file_upload(content, "income.webp", "image/webp")
        self.assertEqual(norm, "webp")

        res = analyze_document_content(content, "income.webp", "image/webp")
        self.assertEqual(res["document_type"], "income_certificate")
        self.assertIn("IC1234567890", res["extracted_fields"].get("certificate_number", ""))

    def test_webp_mime_and_magic_validation(self):
        """Validate WebP file format checking."""
        valid_webp = self._generate_synthetic_image("WEBP")
        self.assertEqual(validate_file_upload(valid_webp, "test.webp", "image/webp"), "webp")

        # Invalid extension for WebP content
        with self.assertRaises(InvalidFileTypeError):
            validate_file_upload(valid_webp, "test.jpg", "image/jpeg")

        # Invalid content for WebP extension
        with self.assertRaises(InvalidFileTypeError):
            validate_file_upload(b"NOT A WEBP FILE", "test.webp", "image/webp")

    def test_blurry_image_fallback(self):
        """Blurry image without readable text returns unverified_or_incomplete."""
        img = Image.new("RGB", (300, 100), color=(200, 200, 200))
        img = img.filter(ImageFilter.GaussianBlur(15))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        blurry_bytes = buf.getvalue()

        result = analyze_document_content(blurry_bytes, "blurry.png", "image/png")
        self.assertEqual(result["checklist_status"], "unverified_or_incomplete")
        self.assertEqual(result["extracted_fields"], {})

    def test_scanned_pdf_ocr_extraction(self):
        """Scanned PDF (embedded image without text layer) is processed via OCR."""
        import pymupdf
        img_bytes = self._generate_synthetic_image("PNG")

        pdf_doc = pymupdf.open()
        page = pdf_doc.new_page(width=900, height=300)
        page.insert_image(pymupdf.Rect(0, 0, 900, 300), stream=img_bytes)
        scanned_pdf_bytes = pdf_doc.tobytes()

        text, warnings = extract_text_from_pdf(scanned_pdf_bytes)
        self.assertTrue(len(text) > 0, "Scanned PDF OCR must extract text")
        self.assertIn("INCOME", text.upper())

        res = analyze_document_content(scanned_pdf_bytes, "scanned.pdf", "application/pdf")
        self.assertEqual(res["document_type"], "income_certificate")

    def test_actual_telugu_ocr_extraction(self):
        """Verify actual Telugu OCR character extraction using PyMuPDF and tel.traineddata."""
        from PIL import ImageFont
        from app.services.documents.extractor import _get_tessdata_path

        td_path = _get_tessdata_path()
        self.assertIsNotNone(td_path, "Tessdata directory must be located")
        tel_data = os.path.join(td_path, "tel.traineddata")
        self.assertTrue(os.path.isfile(tel_data), "tel.traineddata must exist in tessdata directory")
        self.assertGreater(os.path.getsize(tel_data), 1_000_000, "tel.traineddata must be complete")

        # Locate a font supporting Telugu Unicode characters
        font = None
        for font_path in [
            "C:/Windows/Fonts/Nirmala.ttc",
            "C:/Windows/Fonts/NirmalaB.ttc",
            "C:/Windows/Fonts/gautami.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf",
        ]:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, 40)
                    break
                except Exception:
                    continue

        if font is None:
            self.skipTest("No Telugu Unicode font available on host system to render synthetic Telugu image")

        img = Image.new("RGB", (800, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((40, 60), "ఆదాయ ధృవీకరణ పత్రము", fill=(0, 0, 0), font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        extracted, warnings = extract_text_from_image(buf.getvalue(), "telugu_doc.png")

        self.assertTrue(len(extracted) > 0, "OCR should extract text from Telugu image")
        has_telugu_chars = any(0x0C00 <= ord(c) <= 0x0C7F for c in extracted)
        self.assertTrue(has_telugu_chars, f"Extracted text must contain authentic Telugu Unicode characters: {extracted!r}")


if __name__ == "__main__":
    unittest.main()
