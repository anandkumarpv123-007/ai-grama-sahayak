import math
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.eligibility_rules import evaluate_scheme_eligibility, parse_and_validate_age, parse_and_validate_income

client = TestClient(app)


def test_eligibility_exact_contract_example_missing_fields():
    """
    Directly tests the contract example in docs/api_contracts.md Section 4.C:
    Expects status: 'needs_more_information' and missing_fields: ['annual_income'].
    Isolates scheme_example_001 as a synthetic non-production fixture.
    """
    payload = {
        "scheme_id": "scheme_example_001",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "district": "Kakinada",
            "age": 35,
            "occupation": "farmer",
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["scheme_id"] == "scheme_example_001"
    assert data["status"] == "needs_more_information"
    assert "annual_income" in data["missing_fields"]
    assert isinstance(data["reasons"], list)
    assert isinstance(data["benefits"], list)
    assert isinstance(data["required_documents"], list)
    assert isinstance(data["application_steps"], list)
    assert isinstance(data["sources"], list)
    # Confirm it is flagged as synthetic test data
    assert any("synthetic" in s["title"].lower() or "test" in s["title"].lower() for s in data["sources"])


def test_pm_kisan_needs_more_information_when_exclusions_unverified():
    """
    Safety Rule: Do not declare a person eligible if important official exclusion
    criteria have not been checked.
    """
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": True,
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            # Notice exclusion fields are omitted
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "paid_income_tax_last_ay" in data["missing_fields"]
    assert "is_regular_govt_employee" in data["missing_fields"]
    assert "is_institutional_landholder" in data["missing_fields"]


def test_pm_kisan_eligible_with_all_exclusions_cleared():
    """
    Tests legitimate PM-KISAN evaluation against verified official rules:
    - No 5-acre limit (cabinet removed in 2019)
    - No 3-lakh ceiling
    - Only official statutory exclusions verified clear.
    """
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": True,
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            "is_institutional_landholder": False,
            "holds_constitutional_post": False,
            "is_elected_representative": False,
            "is_regular_govt_employee": False,
            "is_pensioner_10k_plus": False,
            "paid_income_tax_last_ay": False,
            "is_registered_professional": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "eligible"
    assert len(data["missing_fields"]) == 0
    assert any("6,000" in b for b in data["benefits"])
    assert any("pmkisan.gov.in" in s["url"] for s in data["sources"])
    assert data["sources"][0]["verified_at"] == "2026-11-22"


def test_pm_kisan_ineligible_income_tax_payer_exclusion():
    """
    Official Exclusion: Income tax payers in last assessment year are ineligible.
    """
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": True,
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            "is_institutional_landholder": False,
            "holds_constitutional_post": False,
            "is_elected_representative": False,
            "is_regular_govt_employee": False,
            "is_pensioner_10k_plus": False,
            "paid_income_tax_last_ay": True,  # Disqualifying condition
            "is_registered_professional": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ineligible"
    assert any("income tax" in r.lower() for r in data["reasons"])


def test_pm_kisan_ineligible_not_landholding():
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": False,  # Not a landholder
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            "is_institutional_landholder": False,
            "holds_constitutional_post": False,
            "is_elected_representative": False,
            "is_regular_govt_employee": False,
            "is_pensioner_10k_plus": False,
            "paid_income_tax_last_ay": False,
            "is_registered_professional": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ineligible"
    assert any("cultivable land" in r.lower() for r in data["reasons"])


def test_ntr_bharosa_pension_eligible():
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 63,
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "eligible"
    assert any("4,000" in b for b in data["benefits"])
    assert any("sspensions.ap.gov.in" in s["url"] for s in data["sources"])


def test_ntr_bharosa_pension_underage_ineligible():
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 52,  # Under 60
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ineligible"
    assert any("60 years" in r for r in data["reasons"])


def test_transitioning_scheme_returns_unable_to_verify():
    """
    Safety Rule: Do not claim a scheme is currently active without verifying its current status.
    If current official rules cannot be verified, return unable_to_verify.
    """
    for scheme_id in ["amma_vodi", "ysr_rythu_bharosa"]:
        payload = {
            "scheme_id": scheme_id,
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "annual_income": 100000,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unable_to_verify"
        assert len(data["reasons"]) > 0
        assert any("transition" in r.lower() or "restructuring" in r.lower() for r in data["reasons"])


def test_unknown_scheme_returns_unable_to_verify():
    payload = {
        "scheme_id": "unknown_fictional_scheme_xyz",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unable_to_verify"
    assert len(data["reasons"]) > 0


def test_telugu_encoding_and_readability():
    """
    Tests that Telugu response text is valid, uncorrupted UTF-8 Telugu characters
    in the Telugu Unicode block (\\u0c00 - \\u0c7f).
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "te",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 65,
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "eligible"

    # Verify Telugu script is present and uncorrupted
    assert len(data["benefits"]) > 0
    first_benefit = data["benefits"][0]
    telugu_chars = [c for c in first_benefit if "\u0c00" <= c <= "\u0c7f"]
    assert len(telugu_chars) > 5, "Response benefit must contain valid Telugu characters"

    # Verify no raw unicode escape sequences leaked into the string
    assert "\\u" not in first_benefit

    # Verify Telugu reasons when missing information
    missing_payload = {
        "scheme_id": "pm_kisan",
        "language": "te",
        "applicant_profile": {},
    }
    missing_resp = client.post("/api/eligibility/check", json=missing_payload)
    missing_data = missing_resp.json()
    assert missing_data["status"] == "needs_more_information"
    first_reason = missing_data["reasons"][0]
    telugu_reason_chars = [c for c in first_reason if "\u0c00" <= c <= "\u0c7f"]
    assert len(telugu_reason_chars) > 5


def test_eligibility_blank_scheme_id_rejected():
    payload = {
        "scheme_id": "   ",
        "language": "en",
        "applicant_profile": {},
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data


# ---------------------------------------------------------------------------
# Targeted Regression Tests: Dr. NTR Vaidya Seva
# ---------------------------------------------------------------------------
def test_vaidya_seva_needs_more_information_when_no_card_and_no_income():
    """
    Safety Rule: Never return eligible when applicant has no qualifying card and
    income information is missing. Must return needs_more_information.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": False,
            "has_rice_card_or_aarogyasri_card": False,
            # annual_income is missing
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "annual_income" in data["missing_fields"]


def test_vaidya_seva_eligible_with_income_under_5l():
    """
    Applicant without a card is eligible if annual income <= Rs. 5,00,000.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": False,
            "has_rice_card_or_aarogyasri_card": False,
            "annual_income": 350000,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "eligible"
    assert any("25,00,000" in b for b in data["benefits"])
    assert any("aarogyasri.ap.gov.in" in s["url"] for s in data["sources"])


def test_vaidya_seva_ineligible_with_income_over_5l():
    """
    Applicant without a card is ineligible if annual income > Rs. 5,00,000.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": False,
            "has_rice_card_or_aarogyasri_card": False,
            "annual_income": 650000,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ineligible"
    assert any("5,00,000" in r for r in data["reasons"])


def test_vaidya_seva_eligible_with_qualifying_card():
    """
    Applicant holding an Aarogyasri/Rice card qualifies regardless of separate income entry.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": False,
            "has_rice_card_or_aarogyasri_card": True,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "eligible"


def test_vaidya_seva_ineligible_for_govt_employee_with_ehs():
    """
    Government employee covered by EHS is disqualified.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": True,
            "has_rice_card_or_aarogyasri_card": True,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ineligible"
    assert any("EHS" in r or "Employees Health Scheme" in r for r in data["reasons"])


# ---------------------------------------------------------------------------
# Targeted Regression Tests: NTR Bharosa Pension (Rural vs Urban thresholds)
# ---------------------------------------------------------------------------
def test_ntr_bharosa_needs_more_information_without_card_or_locality_income():
    """
    If applicant does NOT have White Ration Card, poverty status requires
    both area_type (rural/urban) and annual_income.
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 62,
            "has_white_ration_or_rice_card": False,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
            # area_type and annual_income omitted
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "area_type" in data["missing_fields"]
    assert "annual_income" in data["missing_fields"]


def test_ntr_bharosa_rural_income_threshold():
    """
    Rural statutory ceiling is Rs. 1,20,000 per annum (Rs. 10,000/month).
    Rs. 1,10,000 -> eligible; Rs. 1,30,000 -> ineligible.
    """
    base_profile = {
        "state": "Andhra Pradesh",
        "age": 65,
        "has_white_ration_or_rice_card": False,
        "area_type": "rural",
        "is_govt_employee_or_pensioner": False,
        "is_income_tax_payer": False,
        "owns_four_wheeler": False,
    }

    # Within rural limit
    resp_pass = client.post(
        "/api/eligibility/check",
        json={"scheme_id": "ntr_bharosa_pension", "language": "en", "applicant_profile": {**base_profile, "annual_income": 110000}},
    )
    assert resp_pass.status_code == 200
    assert resp_pass.json()["status"] == "eligible"

    # Exceeds rural limit
    resp_fail = client.post(
        "/api/eligibility/check",
        json={"scheme_id": "ntr_bharosa_pension", "language": "en", "applicant_profile": {**base_profile, "annual_income": 130000}},
    )
    assert resp_fail.status_code == 200
    assert resp_fail.json()["status"] == "ineligible"
    assert any("rural" in r.lower() or "1,20,000" in r for r in resp_fail.json()["reasons"])


def test_ntr_bharosa_urban_income_threshold():
    """
    Urban statutory ceiling is Rs. 1,44,000 per annum (Rs. 12,000/month).
    Rs. 1,30,000 -> eligible; Rs. 1,60,000 -> ineligible.
    """
    base_profile = {
        "state": "Andhra Pradesh",
        "age": 65,
        "has_white_ration_or_rice_card": False,
        "area_type": "urban",
        "is_govt_employee_or_pensioner": False,
        "is_income_tax_payer": False,
        "owns_four_wheeler": False,
    }

    # Within urban limit (Rs. 1,30,000 <= 1,44,000)
    resp_pass = client.post(
        "/api/eligibility/check",
        json={"scheme_id": "ntr_bharosa_pension", "language": "en", "applicant_profile": {**base_profile, "annual_income": 130000}},
    )
    assert resp_pass.status_code == 200
    assert resp_pass.json()["status"] == "eligible"

    # Exceeds urban limit (Rs. 1,60,000 > 1,44,000)
    resp_fail = client.post(
        "/api/eligibility/check",
        json={"scheme_id": "ntr_bharosa_pension", "language": "en", "applicant_profile": {**base_profile, "annual_income": 160000}},
    )
    assert resp_fail.status_code == 200
    assert resp_fail.json()["status"] == "ineligible"
    assert any("urban" in r.lower() or "1,44,000" in r for r in resp_fail.json()["reasons"])


# ---------------------------------------------------------------------------
# Targeted Regression Tests: Synthetic Scheme Blocked in Production
# ---------------------------------------------------------------------------
def test_scheme_example_001_blocked_in_production(monkeypatch):
    """
    Safety Rule: Synthetic scheme_example_001 must NEVER be exposed as an eligible
    government scheme in production. Must return unable_to_verify.
    """
    from app.core.config import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    payload = {
        "scheme_id": "scheme_example_001",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "district": "Kakinada",
            "age": 35,
            "occupation": "farmer",
            "annual_income": 100000,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unable_to_verify"
    assert any("synthetic test fixture" in r for r in data["reasons"])


# ---------------------------------------------------------------------------
# Targeted Regression Tests: Missing/Null Exclusion & Card-Status Values
# ---------------------------------------------------------------------------
def test_pm_kisan_null_exclusion_field_returns_needs_more_information():
    """
    Safety Rule: Every mandatory eligibility exclusion must be explicitly verified.
    A missing or null exclusion field must NEVER be silently interpreted as False.
    """
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": True,
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            "is_institutional_landholder": False,
            "holds_constitutional_post": False,
            "is_elected_representative": False,
            "is_regular_govt_employee": False,
            "is_pensioner_10k_plus": False,
            "paid_income_tax_last_ay": None,  # Null exclusion field
            "is_registered_professional": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "paid_income_tax_last_ay" in data["missing_fields"]


def test_pm_kisan_null_institutional_landholder_returns_needs_more_information():
    """Missing/null institutional landholder must require explicit verification."""
    payload = {
        "scheme_id": "pm_kisan",
        "language": "en",
        "applicant_profile": {
            "is_landholding_farmer": True,
            "has_aadhaar_linked_bank_account": True,
            "e_kyc_completed": True,
            "is_institutional_landholder": None,  # Null exclusion
            "holds_constitutional_post": False,
            "is_elected_representative": False,
            "is_regular_govt_employee": False,
            "is_pensioner_10k_plus": False,
            "paid_income_tax_last_ay": False,
            "is_registered_professional": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "is_institutional_landholder" in data["missing_fields"]


def test_ntr_bharosa_null_exclusion_returns_needs_more_information():
    """
    NTR Bharosa: Null or missing is_income_tax_payer must never be assumed False.
    Must return needs_more_information.
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 65,
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": None,  # Null exclusion
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "is_income_tax_payer" in data["missing_fields"]


def test_ntr_bharosa_unknown_card_status_returns_needs_more_information():
    """
    NTR Bharosa: Unknown card status (null or omitted) must be distinguished from confirmed
    absence (False), requesting has_white_ration_or_rice_card.
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": 65,
            "has_white_ration_or_rice_card": None,  # Unknown card status
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "has_white_ration_or_rice_card" in data["missing_fields"]


def test_vaidya_seva_null_ehs_exclusion_returns_needs_more_information():
    """
    Dr. NTR Vaidya Seva: Null or missing is_regular_govt_employee_with_ehs must never
    be assumed False. Must return needs_more_information.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": None,  # Null exclusion
            "has_rice_card_or_aarogyasri_card": True,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "is_regular_govt_employee_with_ehs" in data["missing_fields"]


def test_vaidya_seva_unknown_card_status_returns_needs_more_information():
    """
    Dr. NTR Vaidya Seva: Unknown card status (null or omitted) must be distinguished from
    confirmed absence (False), requesting has_rice_card_or_aarogyasri_card.
    """
    payload = {
        "scheme_id": "dr_ntr_vaidya_seva",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "is_regular_govt_employee_with_ehs": False,
            "has_rice_card_or_aarogyasri_card": None,  # Unknown card status
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "has_rice_card_or_aarogyasri_card" in data["missing_fields"]


def test_eligibility_rejects_fractional_age():
    """
    Input Validation Safety:
    Age must be a whole number. Fractional values (65.5, '65.5') must be rejected
    and never silently truncated to integer 65.
    Must return needs_more_information, never eligible or ineligible.
    """
    for frac_age in [65.5, "65.5", 60.1]:
        payload = {
            "scheme_id": "ntr_bharosa_pension",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "age": frac_age,
                "has_white_ration_or_rice_card": True,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "age" in data["missing_fields"]
        assert any("whole number" in r.lower() or "fractional" in r.lower() for r in data["reasons"])
        # Ensure it NEVER produces eligible or a false disqualification
        assert data["status"] != "eligible"
        assert data["status"] != "ineligible"


def test_eligibility_rejects_negative_age():
    """
    Input Validation Safety:
    Negative age (-5, '-5') is malformed data, not a confirmed scheme disqualification.
    Must return needs_more_information, never ineligible.
    """
    for neg_age in [-5, "-5", -1]:
        payload = {
            "scheme_id": "ntr_bharosa_pension",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "age": neg_age,
                "has_white_ration_or_rice_card": True,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "age" in data["missing_fields"]
        assert any("non-negative" in r.lower() for r in data["reasons"])
        assert data["status"] != "ineligible"
        assert data["status"] != "eligible"


def test_eligibility_rejects_nan_and_infinity_age():
    """
    Input Validation Safety:
    Reject NaN and infinity for age.
    Must return needs_more_information.
    Tests both HTTP string representations and direct float inputs.
    """
    # 1. Via HTTP API with string representations
    for str_special in ["NaN", "Infinity", "-Infinity", "nan", "inf", "-inf"]:
        payload = {
            "scheme_id": "ntr_bharosa_pension",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "age": str_special,
                "has_white_ration_or_rice_card": True,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "age" in data["missing_fields"]
        assert any("finite" in r.lower() or "nan" in r.lower() for r in data["reasons"])

    # 2. Direct programmatic evaluation with float NaN and Inf
    for float_val in [float("nan"), float("inf"), float("-inf")]:
        is_valid, parsed, err = parse_and_validate_age(float_val)
        assert is_valid is False
        assert "finite" in err.lower() or "nan" in err.lower()

        res = evaluate_scheme_eligibility(
            scheme_id="ntr_bharosa_pension",
            applicant_profile={
                "state": "Andhra Pradesh",
                "age": float_val,
                "has_white_ration_or_rice_card": True,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        )
        assert res["status"] == "needs_more_information"
        assert "age" in res["missing_fields"]


def test_eligibility_rejects_invalid_age_string():
    """
    Input Validation Safety:
    Reject non-numeric strings for age.
    Must return needs_more_information.
    """
    for invalid_age in ["sixty", "unknown", "60 years"]:
        payload = {
            "scheme_id": "ntr_bharosa_pension",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "age": invalid_age,
                "has_white_ration_or_rice_card": True,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "age" in data["missing_fields"]
        assert any("numeric" in r.lower() or "whole number" in r.lower() for r in data["reasons"])


def test_eligibility_rejects_negative_income():
    """
    Input Validation Safety:
    Negative annual_income (-50000, '-50000') must be rejected and never produce eligible.
    Must return needs_more_information.
    """
    for neg_income in [-50000, "-50000", -1.0]:
        payload = {
            "scheme_id": "ntr_bharosa_pension",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "age": 65,
                "has_white_ration_or_rice_card": False,
                "area_type": "rural",
                "annual_income": neg_income,
                "is_govt_employee_or_pensioner": False,
                "is_income_tax_payer": False,
                "owns_four_wheeler": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "annual_income" in data["missing_fields"]
        assert any("non-negative" in r.lower() for r in data["reasons"])
        assert data["status"] != "eligible"
        assert data["status"] != "ineligible"


def test_eligibility_rejects_nan_and_infinity_income():
    """
    Input Validation Safety:
    Reject NaN and infinity for annual_income before comparing with thresholds.
    Must return needs_more_information.
    Tests both HTTP string representations and direct float inputs.
    """
    # 1. Via HTTP API with string representations
    for str_special in ["NaN", "Infinity", "-Infinity", "nan", "inf", "-inf"]:
        payload = {
            "scheme_id": "dr_ntr_vaidya_seva",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "has_rice_card_or_aarogyasri_card": False,
                "annual_income": str_special,
                "is_regular_govt_employee_with_ehs": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "annual_income" in data["missing_fields"]
        assert any("finite" in r.lower() or "nan" in r.lower() for r in data["reasons"])

    # 2. Direct programmatic evaluation with float NaN and Inf
    for float_val in [float("nan"), float("inf"), float("-inf")]:
        is_valid, parsed, err = parse_and_validate_income(float_val)
        assert is_valid is False
        assert "finite" in err.lower() or "nan" in err.lower()

        res = evaluate_scheme_eligibility(
            scheme_id="dr_ntr_vaidya_seva",
            applicant_profile={
                "state": "Andhra Pradesh",
                "has_rice_card_or_aarogyasri_card": False,
                "annual_income": float_val,
                "is_regular_govt_employee_with_ehs": False,
            },
        )
        assert res["status"] == "needs_more_information"
        assert "annual_income" in res["missing_fields"]


def test_eligibility_rejects_invalid_income_string():
    """
    Input Validation Safety:
    Reject non-numeric strings for annual_income.
    Must return needs_more_information, never a confirmed disqualification.
    """
    for invalid_inc in ["fifty_thousand", "50k", "$50000", "nil"]:
        payload = {
            "scheme_id": "dr_ntr_vaidya_seva",
            "language": "en",
            "applicant_profile": {
                "state": "Andhra Pradesh",
                "has_rice_card_or_aarogyasri_card": False,
                "annual_income": invalid_inc,
                "is_regular_govt_employee_with_ehs": False,
            },
        }
        response = client.post("/api/eligibility/check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_more_information"
        assert "annual_income" in data["missing_fields"]
        assert any("numeric" in r.lower() for r in data["reasons"])
        assert data["status"] != "ineligible"


def test_eligibility_rejects_boolean_age_and_income():
    """
    Input Validation Safety:
    Booleans (True/False) must not be accepted as numbers for age or annual_income.
    Must return needs_more_information.
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "en",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": True,
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "age" in data["missing_fields"]
    assert any("boolean" in r.lower() for r in data["reasons"])


def test_eligibility_telugu_validation_messages():
    """
    Input Validation Safety:
    Validation error messages in Telugu must be readable and uncorrupted.
    """
    payload = {
        "scheme_id": "ntr_bharosa_pension",
        "language": "te",
        "applicant_profile": {
            "state": "Andhra Pradesh",
            "age": -10,
            "has_white_ration_or_rice_card": True,
            "is_govt_employee_or_pensioner": False,
            "is_income_tax_payer": False,
            "owns_four_wheeler": False,
        },
    }
    response = client.post("/api/eligibility/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "needs_more_information"
    assert "age" in data["missing_fields"]
    assert any("పూర్ణాంకమై" in r or "రుణాత్మకం" in r for r in data["reasons"])
