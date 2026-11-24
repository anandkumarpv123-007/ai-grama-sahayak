"""Tests for Nearby Government Services Service and API.

Validates:
- District-based queries
- Coordinate-based queries (latitude + longitude)
- Haversine distance accuracy and sorting
- Validation of coordinate coupling (lat without lon or vice versa)
- Validation of missing query parameters
- Out-of-bounds coordinates
- Non-finite coordinates (NaN, Inf, -Inf)
- Positive and finite radius_km validation
- Honest empty results for unrepresented districts (no hallucination)
- Verification of official sources (.gov.in / .nic.in) and verification dates
- Audited and substantiated public facility records
"""

import math
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.locations.models import VERIFIED_AP_SERVICES, haversine_distance_km
from app.services.locations.service_finder import find_nearby_services


class TestNearbyServices(unittest.TestCase):
    """Test suite for nearby public services finder."""

    def test_query_by_district_kakinada(self):
        """Test retrieving verified services for Kakinada district."""
        results = find_nearby_services(district="Kakinada")
        self.assertGreater(len(results), 0, "Should find facilities in Kakinada")

        names = [r["name"] for r in results]
        self.assertTrue(any("GGH" in n and "Kakinada" in n for n in names))
        for r in results:
            self.assertIn("address", r)
            self.assertIn("service_type", r)
            self.assertIsNone(r["distance_km"], "distance_km should be None when no coordinates provided")
            self.assertIsNotNone(r["source_url"], "Official source URL must be present")

    def test_query_by_district_and_service_type_hospital(self):
        """Test filtering by service_type='hospital'."""
        results = find_nearby_services(district="Visakhapatnam", service_type="hospital")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r["service_type"], "hospital")
            self.assertIn("King George Hospital", r["name"])

    def test_query_by_coordinates(self):
        """Test querying services using geographic coordinates (Kakinada town centre)."""
        results = find_nearby_services(latitude=16.9891, longitude=82.2475, radius_km=30.0)
        self.assertGreater(len(results), 0)

        distances = [r["distance_km"] for r in results]
        self.assertTrue(all(d is not None for d in distances))
        self.assertEqual(distances, sorted(distances), "Results must be sorted by distance ascending")
        self.assertTrue(all(d <= 30.0 for d in distances), "All results must be within radius")

    def test_missing_longitude_raises_error(self):
        """Test that supplying latitude without longitude raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            find_nearby_services(latitude=16.9891)
        self.assertIn("together", str(ctx.exception).lower())

    def test_missing_latitude_raises_error(self):
        """Test that supplying longitude without latitude raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            find_nearby_services(longitude=82.2475)
        self.assertIn("together", str(ctx.exception).lower())

    def test_missing_all_location_params_raises_error(self):
        """Test that omitting both district and coordinates raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            find_nearby_services(service_type="hospital")
        self.assertIn("either district or", str(ctx.exception).lower())

    def test_invalid_coordinate_ranges(self):
        """Test that coordinates outside valid geographic bounds raise ValueError."""
        with self.assertRaises(ValueError):
            find_nearby_services(latitude=95.0, longitude=80.0)

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=190.0)

    def test_non_finite_coordinates(self):
        """Test that NaN, Infinity, or -Infinity coordinates raise ValueError."""
        with self.assertRaises(ValueError):
            find_nearby_services(latitude=float("nan"), longitude=82.0)

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=float("inf"))

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=float("-inf"), longitude=82.0)

    def test_invalid_radius_values(self):
        """Test that zero, negative, or non-finite radius_km raises ValueError."""
        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=82.0, radius_km=0)

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=82.0, radius_km=-10.0)

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=82.0, radius_km=float("nan"))

        with self.assertRaises(ValueError):
            find_nearby_services(latitude=16.0, longitude=82.0, radius_km=float("inf"))

    def test_honest_empty_result_for_unknown_location(self):
        """Test that an unrepresented or non-existent district returns an empty list without fabricating."""
        results = find_nearby_services(district="FictitiousDistrictName123")
        self.assertEqual(results, [], "Must return empty list instead of inventing facilities")

    def test_verified_records_integrity(self):
        """Verify that every record in the substantiated dataset is verified with authoritative sources."""
        self.assertEqual(len(VERIFIED_AP_SERVICES), 15, "Audited dataset must contain 15 substantiated facilities")

        verified_phone_count = 0
        for item in VERIFIED_AP_SERVICES:
            self.assertTrue(item["name"].strip())
            self.assertTrue(item["address"].strip())
            self.assertTrue(item["district"].strip())
            self.assertIn(item["service_type"], ["hospital", "community_health_centre"])
            self.assertIsInstance(item["latitude"], (int, float))
            self.assertIsInstance(item["longitude"], (int, float))
            self.assertTrue(item.get("verified_at").startswith("2026-11-"))
            self.assertIn("evidence", item, "Every record must include audit evidence")

            # Check phone is either substantiated string or None
            if item.get("phone") is not None:
                self.assertTrue(item["phone"].strip())
                verified_phone_count += 1

            # Authoritative source URL verification (.gov.in or .nic.in)
            url = item["source_url"]
            self.assertTrue(
                url.startswith("https://") or url.startswith("http://"),
                f"Source URL must be valid: {url}",
            )
            self.assertTrue(
                ".gov.in" in url or ".nic.in" in url,
                f"Source URL must point to official government domain: {url}",
            )

        # 6 DME teaching hospitals have substantiated direct landlines
        self.assertEqual(verified_phone_count, 6)

    def test_palnadu_district_and_spelling_variants(self):
        """Test Palnadu district search with case-insensitivity, Telugu, and town names."""
        for d in ["palnadu", "Palnadu", "PALNADU", "పల్నాడు", "narasaraopet"]:
            results = find_nearby_services(district=d)
            self.assertGreaterEqual(len(results), 1, f"Must find Palnadu facilities for '{d}'")
            self.assertTrue(any("Narasaraopet" in r["name"] for r in results))

    def test_guntur_and_krishna_coverage(self):
        """Test expanded Guntur and Krishna coverage."""
        guntur_results = find_nearby_services(district="Guntur")
        self.assertGreaterEqual(len(guntur_results), 3)

        krishna_results = find_nearby_services(district="Krishna")
        self.assertGreaterEqual(len(krishna_results), 2)

    def test_education_service_type_honest_empty(self):
        """Test service_type='education' in Guntur returns honest empty results without fabricating."""
        results = find_nearby_services(service_type="education", district="Guntur")
        self.assertEqual(results, [], "Must return empty results when no facilities of that type exist")

    def test_gps_coordinate_search_palnadu(self):
        """Test GPS coordinate search near Narasaraopet (Palnadu) returns sorted radial facilities."""
        results = find_nearby_services(latitude=16.2354, longitude=80.0499, radius_km=50.0)
        self.assertGreaterEqual(len(results), 2)
        # Verify distance sorting
        distances = [r["distance_km"] for r in results]
        self.assertEqual(distances, sorted(distances))
        self.assertLessEqual(distances[0], 1.0)  # AH Narasaraopet should be ~0 km

    def test_haversine_distance_calculation(self):
        """Test Haversine distance accuracy against known geographic coordinates."""
        # Distance between Kakinada GGH (16.9604, 82.2381) and Ramachandrapuram CHC (16.8483, 82.0256)
        dist = haversine_distance_km(16.9604, 82.2381, 16.8483, 82.0256)
        self.assertGreater(dist, 20.0)
        self.assertLess(dist, 30.0)


if __name__ == "__main__":
    unittest.main()
