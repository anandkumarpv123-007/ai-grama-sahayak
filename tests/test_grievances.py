"""Tests for Grievance Drafting Service and API.

Validates:
- English complaint draft generation
- Telugu complaint draft generation
- Guardrails against false submission claims
- Guardrails against live tracking claims
- Official links format matching Common Source Object
- Validation of required fields and supported languages ('en', 'te')
- Respectful and formal tone
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.grievances.drafter import (
    draft_grievance,
    OFFICIAL_AP_GRIEVANCE_LINKS,
)


class TestGrievanceDrafting(unittest.TestCase):
    """Test suite for grievance drafting service."""

    def test_draft_english_water_supply_grievance(self):
        """Test English draft generation for a water supply issue."""
        result = draft_grievance(
            category="water_supply",
            description="There has been no drinking water supply in our street for the past four days.",
            district="Kakinada",
            mandal="Samalkota",
            language="en",
        )

        self.assertIn("subject", result)
        self.assertIn("complaint_body", result)
        self.assertIn("recommended_next_steps", result)
        self.assertIn("official_links", result)

        subject = result["subject"]
        body = result["complaint_body"]
        steps = result["recommended_next_steps"]

        # Subject and body checks
        self.assertIn("Samalkota", subject)
        self.assertIn("Kakinada", subject)
        self.assertIn("drinking water", body.lower())
        self.assertIn("Samalkota", body)
        self.assertIn("Kakinada", body)
        self.assertIn("Andhra Pradesh", body)

        # Tone checks
        self.assertIn("Respected Sir/Madam", body)
        self.assertIn("Yours sincerely", body)

        # Guardrails: verify NO false claims of submission
        body_lower = body.lower()
        self.assertNotIn("has been submitted", body_lower)
        self.assertNotIn("your complaint number is", body_lower)
        self.assertNotIn("we have forwarded your complaint to the collector", body_lower)

        # Verify next steps explicitly advise manual citizen submission
        steps_text = " ".join(steps).lower()
        self.assertTrue(
            any("not been submitted" in s.lower() or "not submitted" in s.lower() for s in steps),
            "Next steps must explicitly state that the draft was NOT submitted automatically.",
        )
        self.assertTrue(
            any("spandana" in s.lower() or "1902" in s.lower() for s in steps),
            "Next steps must provide official submission channels (Spandana or 1902).",
        )

    def test_draft_telugu_grievance(self):
        """Test Telugu draft generation for an electricity issue."""
        result = draft_grievance(
            category="electricity",
            description="గ్రామంలో గత రెండు రోజులుగా విద్యుత్ సరఫరా నిలిచిపోయింది.",
            district="విశాఖపట్నం",
            mandal="గాజువాక",
            language="te",
        )

        subject = result["subject"]
        body = result["complaint_body"]
        steps = result["recommended_next_steps"]

        # Telugu content checks
        self.assertIn("విజ్ఞప్తి", subject)
        self.assertIn("గాజువాక", subject)
        self.assertIn("గౌరవనీయులైన", body)
        self.assertIn("విద్యుత్ సరఫరా", body)
        self.assertIn("భవదీయుడు", body)

        # Guardrail: check Telugu next steps confirm it is only a draft
        steps_text = " ".join(steps)
        self.assertTrue(
            any("స్వయంచాలకంగా సమర్పించబడలేదు" in s or "ముసాయిదా మాత్రమే" in s for s in steps),
            "Telugu steps must clearly state this is only a draft.",
        )

    def test_official_links_conformance(self):
        """Verify that official links conform to the Common Source Object schema."""
        result = draft_grievance(
            category="roads",
            description="Potholes on the main road.",
            district="Guntur",
            mandal="Tenali",
            language="en",
        )

        links = result["official_links"]
        self.assertGreater(len(links), 0)
        for link in links:
            self.assertIn("title", link)
            self.assertIn("url", link)
            self.assertIn("publisher", link)
            self.assertIn("verified_at", link)
            # URL must point to verified official government domain
            self.assertTrue(
                link["url"].startswith("https://") and ".gov.in" in link["url"],
                f"URL must be official AP government site: {link['url']}",
            )

    def test_missing_category_raises_error(self):
        """Test that missing or blank category raises ValueError."""
        with self.assertRaises(ValueError):
            draft_grievance(
                category="",
                description="Valid description",
                district="Kakinada",
                mandal="Samalkota",
            )

    def test_missing_description_raises_error(self):
        """Test that missing or blank description raises ValueError."""
        with self.assertRaises(ValueError):
            draft_grievance(
                category="water_supply",
                description="   ",
                district="Kakinada",
                mandal="Samalkota",
            )

    def test_missing_district_or_mandal_raises_error(self):
        """Test that missing district or mandal raises ValueError."""
        with self.assertRaises(ValueError):
            draft_grievance(
                category="water_supply",
                description="Valid description",
                district="",
                mandal="Samalkota",
            )
        with self.assertRaises(ValueError):
            draft_grievance(
                category="water_supply",
                description="Valid description",
                district="Kakinada",
                mandal="",
            )

    def test_unsupported_language_raises_error(self):
        """Test that languages other than 'en' and 'te' raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            draft_grievance(
                category="water_supply",
                description="Valid description",
                district="Kakinada",
                mandal="Samalkota",
                language="hi",
            )
        self.assertIn("language must be", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
