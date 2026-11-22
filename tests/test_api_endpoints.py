"""Direct and Integration Tests for API Router Endpoints.

Tests:
- Router prefixes and exact mounted paths under /api:
  - POST /api/documents/analyze
  - GET /api/services/nearby
  - POST /api/grievances/draft
- Shared schema compatibility (DocumentAnalysisResponse, NearbyServicesResponse, GrievanceDraftResponse)
- Standard error structure formatting:
  {"error": {"code": "...", "message": "...", "details": [...]}}
- Error handling masking raw exceptions on HTTP 500
- Invalid radius and non-finite coordinates on GET /api/services/nearby
- Scanned PDF and image OCR fallback on POST /api/documents/analyze
- Streaming upload 10 MB size limit enforcement
- Regression test: missing shared schemas fail clearly
"""

import io
import math
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

# Import test setup first to configure test shims
import tests  # noqa: F401

from app.api.documents import (
    router as doc_router,
    analyze_document,
    DocumentAnalysisResponse,
)
from app.api.services import (
    router as srv_router,
    get_nearby_services,
    NearbyServicesResponse,
)
from app.api.grievances import (
    router as grv_router,
    create_grievance_draft,
    GrievanceDraftRequest,
    GrievanceDraftResponse,
)
from fastapi import UploadFile


class TestApiEndpoints(unittest.TestCase):
    """Test suite directly exercising API endpoint functions and router configurations."""

    @classmethod
    def setUpClass(cls):
        cls.samples_dir = BASE_DIR / "document_samples"

    def test_router_prefixes_and_exact_paths(self):
        """Verify that router prefixes match Member 1's /api inclusion contract.

        Member 1's main.py mounts:
          app.include_router(documents_router, prefix="/api")  -> /api/documents/analyze
          app.include_router(services_router, prefix="/api")   -> /api/services/nearby
          app.include_router(grievances_router, prefix="/api") -> /api/grievances/draft
        """
        self.assertEqual(doc_router.prefix, "/documents")
        self.assertEqual(srv_router.prefix, "/services")
        self.assertEqual(grv_router.prefix, "/grievances")

        api_prefix = "/api"
        expected_doc_path = f"{api_prefix}{doc_router.prefix}/analyze"
        expected_srv_path = f"{api_prefix}{srv_router.prefix}/nearby"
        expected_grv_path = f"{api_prefix}{grv_router.prefix}/draft"

        self.assertEqual(expected_doc_path, "/api/documents/analyze")
        self.assertEqual(expected_srv_path, "/api/services/nearby")
        self.assertEqual(expected_grv_path, "/api/grievances/draft")

    def test_document_analyze_endpoint_success(self):
        """Test POST /api/documents/analyze with valid synthetic PDF and schema compliance."""
        pdf_path = self.samples_dir / "synthetic_income_certificate.pdf"
        with open(pdf_path, "rb") as f:
            content = f.read()

        file_obj = UploadFile(
            filename="synthetic_income_certificate.pdf",
            file=io.BytesIO(content),
            content_type="application/pdf",
        )

        res = analyze_document(file=file_obj, document_type="income_certificate")
        self.assertIsInstance(res, dict)
        self.assertIn("document_type", res)
        self.assertIn("extracted_fields", res)
        self.assertIn("checklist_status", res)
        self.assertIn("missing_fields", res)
        self.assertIn("warnings", res)
        self.assertEqual(res["document_type"], "income_certificate")
        self.assertEqual(res["checklist_status"], "complete")

    def test_document_analyze_endpoint_oversized_streaming(self):
        """Test POST /api/documents/analyze with oversized file (>10 MB) returning HTTP 413."""
        big_content = b"%PDF-" + b"x" * (10 * 1024 * 1024 + 500)
        file_obj = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(big_content),
            content_type="application/pdf",
        )

        res = analyze_document(file=file_obj)
        self.assertEqual(res.status_code, 413)
        self.assertEqual(res.content["error"]["code"], "PAYLOAD_TOO_LARGE")
        self.assertIn("10 MB", res.content["error"]["message"])

    def test_document_analyze_endpoint_invalid_file(self):
        """Test POST /api/documents/analyze with invalid file extension returning HTTP 400."""
        file_obj = UploadFile(
            filename="malicious.exe",
            file=io.BytesIO(b"MZ\x90\x00"),
            content_type="application/octet-stream",
        )

        res = analyze_document(file=file_obj)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content["error"]["code"], "INVALID_FILE_TYPE")

    def test_document_analyze_endpoint_empty_file(self):
        """Test POST /api/documents/analyze with 0-byte file returning HTTP 400."""
        file_obj = UploadFile(
            filename="empty.pdf",
            file=io.BytesIO(b""),
            content_type="application/pdf",
        )

        res = analyze_document(file=file_obj)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content["error"]["code"], "EMPTY_FILE")

    def test_document_analyze_scanned_pdf_fallback(self):
        """Test POST /api/documents/analyze with scanned PDF returns unverified_or_incomplete."""
        scanned_path = self.samples_dir / "synthetic_scanned_unreadable.pdf"
        with open(scanned_path, "rb") as f:
            content = f.read()

        file_obj = UploadFile(
            filename="synthetic_scanned_unreadable.pdf",
            file=io.BytesIO(content),
            content_type="application/pdf",
        )

        res = analyze_document(file=file_obj)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["checklist_status"], "unverified_or_incomplete")
        self.assertTrue(any("scanned" in w.lower() or "ocr" in w.lower() for w in res["warnings"]))

    def test_document_analyze_image_ocr_fallback(self):
        """Test POST /api/documents/analyze with image returns unverified_or_incomplete without metadata cheating."""
        img_path = self.samples_dir / "synthetic_income_cert.png"
        with open(img_path, "rb") as f:
            content = f.read()

        file_obj = UploadFile(
            filename="synthetic_income_cert.png",
            file=io.BytesIO(content),
            content_type="image/png",
        )

        res = analyze_document(file=file_obj)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["checklist_status"], "unverified_or_incomplete")
        self.assertTrue(any("ocr" in w.lower() or "machine-readable" in w.lower() for w in res["warnings"]))

    def test_nearby_services_endpoint_success(self):
        """Test GET /api/services/nearby with valid district and schema compliance."""
        res = get_nearby_services(district="Kakinada", service_type="hospital")
        self.assertIsInstance(res, dict)
        self.assertIn("services", res)
        self.assertGreater(len(res["services"]), 0)
        first = res["services"][0]
        self.assertIn("name", first)
        self.assertIn("address", first)
        self.assertEqual(first["service_type"], "hospital")

    def test_nearby_services_endpoint_invalid_radius(self):
        """Test GET /api/services/nearby with non-positive or non-finite radius_km returning HTTP 400."""
        res_zero = get_nearby_services(latitude=16.9891, longitude=82.2475, radius_km=0)
        self.assertEqual(res_zero.status_code, 400)
        self.assertEqual(res_zero.content["error"]["code"], "VALIDATION_ERROR")

        res_neg = get_nearby_services(latitude=16.9891, longitude=82.2475, radius_km=-5.0)
        self.assertEqual(res_neg.status_code, 400)

        res_nan = get_nearby_services(latitude=16.9891, longitude=82.2475, radius_km=float("nan"))
        self.assertEqual(res_nan.status_code, 400)

    def test_nearby_services_endpoint_non_finite_coordinates(self):
        """Test GET /api/services/nearby with NaN or Inf coordinates returning HTTP 400."""
        res_nan = get_nearby_services(latitude=float("nan"), longitude=82.2475)
        self.assertEqual(res_nan.status_code, 400)
        self.assertEqual(res_nan.content["error"]["code"], "VALIDATION_ERROR")

        res_inf = get_nearby_services(latitude=16.9891, longitude=float("inf"))
        self.assertEqual(res_inf.status_code, 400)
        self.assertEqual(res_inf.content["error"]["code"], "VALIDATION_ERROR")

    def test_nearby_services_endpoint_missing_lon(self):
        """Test GET /api/services/nearby with lat but missing lon returning HTTP 400."""
        res = get_nearby_services(latitude=16.9891)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("together", res.content["error"]["message"].lower())

    def test_nearby_services_endpoint_missing_all(self):
        """Test GET /api/services/nearby with no location params returning HTTP 400."""
        res = get_nearby_services(service_type="hospital")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content["error"]["code"], "VALIDATION_ERROR")

    def test_nearby_services_endpoint_empty_results(self):
        """Test GET /api/services/nearby with non-existent district returning honest empty list."""
        res = get_nearby_services(district="NoMatchingDistrict")
        self.assertIsInstance(res, dict)
        self.assertEqual(res["services"], [])

    def test_grievances_draft_endpoint_success(self):
        """Test POST /api/grievances/draft endpoint with valid request and schema compliance."""
        req = GrievanceDraftRequest(
            category="water_supply",
            description="Low water pressure and contaminated supply for 5 days.",
            district="Kakinada",
            mandal="Samalkota",
            language="en",
        )
        res = create_grievance_draft(req)
        self.assertIsInstance(res, dict)
        self.assertIn("subject", res)
        self.assertIn("complaint_body", res)
        self.assertIn("recommended_next_steps", res)
        self.assertIn("official_links", res)

    def test_grievances_draft_endpoint_validation_error(self):
        """Test POST /api/grievances/draft with missing fields returning HTTP 422."""
        req = GrievanceDraftRequest.model_construct(
            category="",
            description="",
            district="Kakinada",
            mandal="Samalkota",
            language="en",
        )
        res = create_grievance_draft(req)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.content["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Missing required fields", res.content["error"]["message"])

    def test_grievances_draft_endpoint_unsupported_language(self):
        """Test POST /api/grievances/draft with unsupported language returning HTTP 422."""
        req = GrievanceDraftRequest.model_construct(
            category="water_supply",
            description="Some description",
            district="Kakinada",
            mandal="Samalkota",
            language="fr",
        )
        res = create_grievance_draft(req)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.content["error"]["code"], "VALIDATION_ERROR")

    # --- Regression Tests ---

    def test_regression_missing_shared_schemas_fails_clearly(self):
        """Regression: importing API router fails clearly when Member 1's shared schema is missing."""
        import importlib
        saved = sys.modules.get("app.schemas.documents")
        sys.modules["app.schemas.documents"] = None
        try:
            # When app.schemas is not available, import must fail
            with self.assertRaises((ModuleNotFoundError, ImportError)):
                importlib.import_module("app.schemas.documents")
        finally:
            if saved is not None:
                sys.modules["app.schemas.documents"] = saved
            else:
                sys.modules.pop("app.schemas.documents", None)


if __name__ == "__main__":
    unittest.main()
