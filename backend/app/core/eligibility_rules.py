"""
Deterministic Rule-Based Eligibility Engine for AI Grama Sahayak.

CRITICAL RULES:
1. Eligibility is strictly evaluated against documented, verifiable government rules.
2. An LLM must NEVER independently declare a citizen eligible.
3. Every rule is verified against an authoritative government order or operational guideline.
4. If current official rules cannot be verified or are under policy transition, return unable_to_verify.
5. If mandatory exclusion criteria or poverty checks are incomplete, return needs_more_information.
6. Allowed status values:
   - eligible
   - ineligible
   - needs_more_information
   - unable_to_verify
"""

import math
from typing import Any, Dict, List, Optional, Tuple
from app.schemas.common import Source, LanguageCode
from app.schemas.eligibility import EligibilityStatus
from app.core.config import settings


def parse_and_validate_age(
    val: Any,
    language: LanguageCode = LanguageCode.EN,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validates that age is a finite, non-negative whole number.
    Rejects:
    - Booleans (True/False)
    - Fractional / decimal values (e.g. 65.5, '65.5') - never silently truncated
    - NaN and Infinity
    - Negative values (e.g. -5, '-5')
    - Non-numeric strings or invalid types
    """
    is_te = language == LanguageCode.TE
    if val is None:
        err = "వయస్సు వివరాలు అవసరం." if is_te else "Age is required."
        return False, None, err
    if isinstance(val, bool):
        err = (
            "దరఖాస్తుదారు వయస్సు బూలియన్ (Boolean) విలువ కాకూడదు."
            if is_te
            else "Applicant age cannot be a boolean value. Please provide a valid, finite, non-negative whole number."
        )
        return False, None, err
    if isinstance(val, int):
        if val < 0:
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా రుణాత్మకం కాని పూర్ణాంకమై ఉండాలి."
                if is_te
                else "Applicant age must be a non-negative whole number (negative values are not permitted)."
            )
            return False, None, err
        return True, val, None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా పరిమిత సంఖ్య అయి ఉండాలి (NaN మరియు అనంతం అనుమతించబడవు)."
                if is_te
                else "Applicant age must be a finite number (NaN and Infinity are not permitted)."
            )
            return False, None, err
        if val < 0:
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా రుణాత్మకం కాని పూర్ణాంకమై ఉండాలి."
                if is_te
                else "Applicant age must be a non-negative whole number (negative values are not permitted)."
            )
            return False, None, err
        if not val.is_integer():
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా పూర్ణాంకమై ఉండాలి; భిన్నాలు లేదా దశాంశాలు అనుమతించబడవు."
                if is_te
                else "Applicant age must be a whole number; fractional values are not permitted and cannot be truncated."
            )
            return False, None, err
        return True, int(val), None
    if isinstance(val, str):
        s = val.strip()
        if not s or s.lower() in ["none", "null"]:
            err = "వయస్సు వివరాలు అవసరం." if is_te else "Age is required."
            return False, None, err
        try:
            f = float(s)
        except (ValueError, TypeError):
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా సరైన సంఖ్యా పూర్ణాంకమై ఉండాలి."
                if is_te
                else "Applicant age must be a valid numeric whole number."
            )
            return False, None, err
        if math.isnan(f) or math.isinf(f):
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా పరిమిత సంఖ్య అయి ఉండాలి (NaN మరియు అనంతం అనుమతించబడవు)."
                if is_te
                else "Applicant age must be a finite number (NaN and Infinity are not permitted)."
            )
            return False, None, err
        if f < 0:
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా రుణాత్మకం కాని పూర్ణాంకమై ఉండాలి."
                if is_te
                else "Applicant age must be a non-negative whole number (negative values are not permitted)."
            )
            return False, None, err
        if not f.is_integer():
            err = (
                "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా పూర్ణాంకమై ఉండాలి; భిన్నాలు లేదా దశాంశాలు అనుమతించబడవు."
                if is_te
                else "Applicant age must be a whole number; fractional values are not permitted and cannot be truncated."
            )
            return False, None, err
        return True, int(f), None

    err = (
        "దరఖాస్తుదారు వయస్సు తప్పనిసరిగా సరైన సంఖ్యా పూర్ణాంకమై ఉండాలి."
        if is_te
        else "Applicant age must be a valid numeric whole number."
    )
    return False, None, err


def parse_and_validate_income(
    val: Any,
    language: LanguageCode = LanguageCode.EN,
) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validates that annual_income is a finite, non-negative number.
    Rejects:
    - Booleans (True/False)
    - NaN and Infinity
    - Negative values (e.g. -50000, '-50000')
    - Non-numeric strings or invalid types
    """
    is_te = language == LanguageCode.TE
    if val is None:
        err = "వార్షిక ఆదాయ వివరాలు అవసరం." if is_te else "Annual income is required."
        return False, None, err
    if isinstance(val, bool):
        err = (
            "వార్షిక ఆదాయం బూలియన్ (Boolean) విలువ కాకూడదు."
            if is_te
            else "Applicant annual income cannot be a boolean value. Please provide a valid, finite, non-negative number."
        )
        return False, None, err
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            err = (
                "వార్షిక ఆదాయం తప్పనిసరిగా పరిమిత సంఖ్య అయి ఉండాలి (NaN మరియు అనంతం అనుమతించబడవు)."
                if is_te
                else "Applicant annual income must be a finite number (NaN and Infinity are not permitted)."
            )
            return False, None, err
        if val < 0:
            err = (
                "వార్షిక ఆదాయం తప్పనిసరిగా రుణాత్మకం కాని సంఖ్య అయి ఉండాలి."
                if is_te
                else "Applicant annual income must be a non-negative number (negative values are not permitted)."
            )
            return False, None, err
        return True, float(val), None
    if isinstance(val, str):
        s = val.strip()
        if not s or s.lower() in ["none", "null"]:
            err = "వార్షిక ఆదాయ వివరాలు అవసరం." if is_te else "Annual income is required."
            return False, None, err
        try:
            f = float(s)
        except (ValueError, TypeError):
            err = (
                "వార్షిక ఆదాయం తప్పనిసరిగా సరైన సంఖ్య అయి ఉండాలి."
                if is_te
                else "Applicant annual income must be a valid numeric value."
            )
            return False, None, err
        if math.isnan(f) or math.isinf(f):
            err = (
                "వార్షిక ఆదాయం తప్పనిసరిగా పరిమిత సంఖ్య అయి ఉండాలి (NaN మరియు అనంతం అనుమతించబడవు)."
                if is_te
                else "Applicant annual income must be a finite number (NaN and Infinity are not permitted)."
            )
            return False, None, err
        if f < 0:
            err = (
                "వార్షిక ఆదాయం తప్పనిసరిగా రుణాత్మకం కాని సంఖ్య అయి ఉండాలి."
                if is_te
                else "Applicant annual income must be a non-negative number (negative values are not permitted)."
            )
            return False, None, err
        return True, f, None

    err = (
        "వార్షిక ఆదాయం తప్పనిసరిగా సరైన సంఖ్య అయి ఉండాలి."
        if is_te
        else "Applicant annual income must be a valid numeric value."
    )
    return False, None, err


class SchemeRuleDefinition:
    def __init__(
        self,
        scheme_id: str,
        name_en: str,
        name_te: str,
        required_fields: List[str],
        evaluator_fn: Any,
        benefits_en: List[str],
        benefits_te: List[str],
        documents_en: List[str],
        documents_te: List[str],
        steps_en: List[str],
        steps_te: List[str],
        sources: List[Source],
        is_synthetic_test: bool = False,
    ):
        self.scheme_id = scheme_id
        self.name_en = name_en
        self.name_te = name_te
        self.required_fields = required_fields
        self.evaluator_fn = evaluator_fn
        self.benefits_en = benefits_en
        self.benefits_te = benefits_te
        self.documents_en = documents_en
        self.documents_te = documents_te
        self.steps_en = steps_en
        self.steps_te = steps_te
        self.sources = sources
        self.is_synthetic_test = is_synthetic_test


# =============================================================================
# 1. SYNTHETIC CONTRACT TEST EXAMPLE (ISOLATED - NOT A REAL SCHEME)
# =============================================================================
# Purpose: Strict compliance with Section 4.C of docs/api_contracts.md.
# Specifically tests: when state='Andhra Pradesh', district='Kakinada', age=35,
# occupation='farmer' are provided without 'annual_income', the response must be
# status: 'needs_more_information' and missing_fields: ['annual_income'].
# In production, this synthetic fixture is blocked and returns unable_to_verify.
# =============================================================================

def _eval_synthetic_test_example(
    profile: Dict[str, Any],
    language: LanguageCode,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    state = str(profile.get("state", "")).strip().lower()
    occupation = str(profile.get("occupation", "")).strip().lower()
    income = profile.get("annual_income")

    if state not in ["andhra pradesh", "ap"]:
        if language == LanguageCode.TE:
            reasons.append("దరఖాస్తుదారు తప్పనిసరిగా ఆంధ్రప్రదేశ్ నివాసి అయి ఉండాలి.")
        else:
            reasons.append("Applicant must be a resident of Andhra Pradesh.")

    if occupation not in ["farmer", "agriculture", "tenant farmer"]:
        if language == LanguageCode.TE:
            reasons.append("దరఖాస్తుదారు వృత్తి రైతు అయి ఉండాలి.")
        else:
            reasons.append("Applicant occupation must be farmer.")

    if income is not None:
        valid_inc, parsed_income, inc_err = parse_and_validate_income(income, language)
        if not valid_inc or parsed_income is None:
            reasons.append(inc_err or "Invalid annual income value provided.")
        elif parsed_income > 250000:
            if language == LanguageCode.TE:
                reasons.append("వార్షిక కుటుంబ ఆదాయం రూ. 2,50,000 మించకూడదు.")
            else:
                reasons.append("Applicant annual family income must not exceed Rs. 2,50,000.")

    is_eligible = len(reasons) == 0
    if is_eligible:
        if language == LanguageCode.TE:
            reasons.append("దరఖాస్తుదారు టెస్ట్ స్కీమ్ ప్రమాణాలన్నింటినీ సంతృప్తిపరిచారు.")
        else:
            reasons.append("Applicant meets all mock test criteria for scheme_example_001.")

    return is_eligible, reasons


# =============================================================================
# 2. PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)
# =============================================================================
# Authoritative Source: Ministry of Agriculture & Farmers Welfare, GoI
# Operational Guidelines verified at:
# https://pmkisan.gov.in/Documents/OperationalGuidelines(Revised).pdf (Verified: 2026-11-22)
#
# Crucial official facts:
# - There is NO 5-acre / 2-hectare land limit (Cabinet removed it on 31.05.2019).
# - There is NO Rs. 3 Lakh annual income ceiling.
# - The scheme covers all landholding farmer families with cultivable land.
# - Mandatory statutory exclusions (Higher Economic Status) MUST be checked:
#     a) Institutional landholders
#     b) Constitutional post holders (former/present)
#     c) Ministers, MPs, MLAs, MLCs, Mayors, District Panchayat Chairpersons
#     d) Regular serving/retired government/PSE/local body employees (excl. MTS/Class IV)
#     e) Retired pensioners receiving Rs. 10,000/month or more (excl. MTS/Class IV)
#     f) Income tax payers in last assessment year
#     g) Registered practicing professionals (Doctors, Engineers, Lawyers, CAs, Architects)
# - If any of these exclusion criteria are not verified, status CANNOT be eligible.
# =============================================================================

def _eval_pm_kisan(
    profile: Dict[str, Any],
    language: LanguageCode,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    # 1. Positive Eligibility Requirement: Must own cultivable land
    is_landholder = profile.get("is_landholding_farmer")
    if is_landholder is not True:
        if language == LanguageCode.TE:
            reasons.append(
                "పీఎం-కిసాన్ మార్గదర్శకాల ప్రకారం సాగుభూమి యాజమాన్య హక్కులు కలిగిన రైతు కుటుంబాలకు మాత్రమే ఈ పథకం వర్తిస్తుంది."
            )
        else:
            reasons.append(
                "Under official PM-KISAN guidelines, benefits are restricted to farmer families owning cultivable land."
            )

    # 2. Mandatory e-KYC and Bank Account status
    if profile.get("has_aadhaar_linked_bank_account") is not True:
        if language == LanguageCode.TE:
            reasons.append(
                "రైతు తప్పనిసరిగా ఆధార్‌తో లింక్ చేయబడిన క్రియాశీల బ్యాంక్ ఖాతాను కలిగి ఉండాలి."
            )
        else:
            reasons.append(
                "Applicant must possess an active bank account linked with Aadhaar for DBT credit."
            )

    if profile.get("e_kyc_completed") is not True:
        if language == LanguageCode.TE:
            reasons.append(
                "పీఎం-కిసాన్ పోర్టల్‌లో తప్పనిసరి బయోమెట్రిక్ లేదా OTP ఆధారిత ఈ-కేవైసీ పూర్తి కావాల్సి ఉంది."
            )
        else:
            reasons.append(
                "Mandatory e-KYC verification must be completed on the PM-KISAN portal."
            )

    # 3. Statutory Exclusion Categories Verification:
    # A missing or null exclusion field must NEVER be silently interpreted as False!
    exclusion_checks = [
        (
            profile.get("is_institutional_landholder"),
            "సంస్థాగత భూ యజమానులు పీఎం-కిసాన్ పథకానికి అర్హులు కారు.",
            "Institutional landholders are officially excluded from PM-KISAN benefits.",
            "సంస్థాగత భూ యజమాని మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Institutional landholder exclusion status must be explicitly verified.",
        ),
        (
            profile.get("holds_constitutional_post"),
            "రాజ్యాంగ పదవులు నిర్వహించిన లేదా నిర్వహిస్తున్న వ్యక్తులు మినహాయించబడ్డారు.",
            "Former and present holders of constitutional posts are officially excluded.",
            "రాజ్యాంగ పదవి మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Constitutional post exclusion status must be explicitly verified.",
        ),
        (
            profile.get("is_elected_representative"),
            "మంత్రులు, ఎంపీలు, ఎమ్మెల్యేలు, ఎమ్మెల్సీలు, మేయర్లు, జడ్పీ చైర్‌పర్సన్లు మినహాయించబడ్డారు.",
            "Ministers, MPs, MLAs, MLCs, Mayors, and District Panchayat Chairpersons are excluded.",
            "ప్రజా ప్రతినిధి మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Elected representative exclusion status must be explicitly verified.",
        ),
        (
            profile.get("is_regular_govt_employee"),
            "కేంద్ర/రాష్ట్ర ప్రభుత్వ లేదా ప్రభుత్వ రంగ సంస్థల రెగ్యులర్ ఉద్యోగులు మినహాయించబడ్డారు (MTS/గ్రూప్-డి మినహా).",
            "Serving or retired government and PSU employees (excluding MTS/Class IV/Group D) are excluded.",
            "ప్రభుత్వ ఉద్యోగ మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Government employee exclusion status must be explicitly verified.",
        ),
        (
            profile.get("is_pensioner_10k_plus"),
            "నెలకు రూ. 10,000 లేదా అంతకంటే ఎక్కువ పెన్షన్ పొందుతున్న విశ్రాంత ఉద్యోగులు మినహాయించబడ్డారు.",
            "Retired pensioners drawing monthly pension of Rs. 10,000 or more are excluded.",
            "రూ. 10,000 పైబడిన పెన్షనర్ మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Pensioner (Rs. 10,000+) exclusion status must be explicitly verified.",
        ),
        (
            profile.get("paid_income_tax_last_ay"),
            "గత అసెస్‌మెంట్ సంవత్సరంలో ఆదాయపు పన్ను చెల్లించిన వ్యక్తులు అర్హులు కారు.",
            "Persons who paid income tax in the last assessment year are officially excluded.",
            "ఆదాయపు పన్ను చెల్లింపుదారుల మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Income tax payment exclusion status must be explicitly verified.",
        ),
        (
            profile.get("is_registered_professional"),
            "వృత్తిపరమైన మండళ్లలో నమోదైన వైద్యులు, ఇంజనీర్లు, న్యాయవాదులు, చార్టర్డ్ అకౌంటెంట్లు మినహాయించబడ్డారు.",
            "Registered practicing professionals (Doctors, Engineers, Lawyers, CAs, Architects) are excluded.",
            "వృత్తిపరమైన రిజిస్ట్రేషన్ మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.",
            "Registered professional exclusion status must be explicitly verified.",
        ),
    ]

    for val, disqual_te, disqual_en, unverified_te, unverified_en in exclusion_checks:
        if val is True:
            reasons.append(disqual_te if language == LanguageCode.TE else disqual_en)
        elif val is not False:
            reasons.append(unverified_te if language == LanguageCode.TE else unverified_en)

    is_eligible = len(reasons) == 0
    if is_eligible:
        if language == LanguageCode.TE:
            reasons.append(
                "దరఖాస్తుదారు భూ యాజమాన్య ప్రమాణాలు పూర్తిచేశారు మరియు అధికారిక మినహాయింపు పరిధిలోకి రారు."
            )
        else:
            reasons.append(
                "Applicant family owns cultivable land and is verified clear of statutory exclusions under official PM-KISAN guidelines."
            )

    return is_eligible, reasons


# =============================================================================
# 3. NTR BHAROSA PENSION (Formerly YSR Pension Kanuka)
# =============================================================================
# Authoritative Source: Panchayat Raj and Rural Development Department, Govt of AP
# Verified at: G.O.Ms.No.39 (PR&RD Department) at https://sspensions.ap.gov.in/SSP/Reports/GOMsNo39.pdf (Verified: 2026-11-22)
#
# Rules for Old Age Pension (OAP):
# - Permanent resident of Andhra Pradesh
# - Age: 60 years or above
# - Below Poverty Line Poverty Verification:
#     Either applicant has a valid White Ration Card / Rice Card (has_white_ration_or_rice_card == True)
#     OR must verify locality-based statutory income limits:
#       * Rural: family monthly income <= Rs. 10,000 (Rs. 1,20,000 per annum)
#       * Urban: family monthly income <= Rs. 12,000 (Rs. 1,44,000 per annum)
# - Exclusions:
#     a) Government employee or government pensioner in family
#     b) Income taxpayer in family
#     c) Four-wheeler ownership (except commercial auto/tractor/taxi)
# =============================================================================

def _eval_ntr_bharosa_oap(
    profile: Dict[str, Any],
    language: LanguageCode,
) -> Tuple[Optional[bool], List[str]]:
    reasons: List[str] = []

    category = str(profile.get("pension_category", "")).strip().lower()
    if category and category not in ["oap", "old_age", "old age", "old age pension", "వృద్ధాప్య"]:
        if language == LanguageCode.TE:
            reason = (
                "ఈ నిబంధనల ఇంజిన్ ప్రస్తుతం వృద్ధాప్య పింఛను (OAP) మాత్రమే మూల్యాంకనం చేస్తుంది. "
                "ఇతర కేటగిరీలు (వితంతు పింఛనుకు మరణ ధృవీకరణ పత్రాలు, దివ్యాంగులకు సదరం/వైద్య ధృవీకరణలు మొదలైనవి) "
                "మరియు సంబంధిత ప్రభుత్వ ఉత్తర్వులపై ఆధారపడి ఉంటాయి. దయచేసి స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
            )
        else:
            reason = (
                f"The deterministic eligibility engine currently evaluates Old Age Pension (OAP) only. "
                f"Eligibility for requested category '{category}' depends on category-specific documentation "
                f"(such as civil records for widow pensions, medical/disability certifications for PwD, or departmental guidelines) "
                f"and active government orders that cannot be certified deterministically. "
                f"Please consult your local Grama / Ward Sachivalayam."
            )
        return None, [reason]

    state = str(profile.get("state", "")).strip().lower()
    if state not in ["andhra pradesh", "ap"]:
        if language == LanguageCode.TE:
            reasons.append("దరఖాస్తుదారు తప్పనిసరిగా ఆంధ్రప్రదేశ్ నివాసి అయి ఉండాలి.")
        else:
            reasons.append("Applicant must be a permanent resident of Andhra Pradesh.")

    age = profile.get("age")
    if age is not None:
        valid_age, parsed_age, age_err = parse_and_validate_age(age, language)
        if not valid_age or parsed_age is None:
            reasons.append(age_err or "Invalid applicant age provided.")
        elif parsed_age < 60:
            if language == LanguageCode.TE:
                reasons.append("వృద్ధాప్య పింఛను (OAP) పొందేందుకు వయస్సు కనీసం 60 సంవత్సరాలు నిండి ఉండాలి.")
            else:
                reasons.append("Applicant age must be 60 years or above for Old Age Pension (OAP).")

    # Poverty-status verification:
    # Distinguish unknown card status from confirmed absence of White Ration Card:
    card_status = profile.get("has_white_ration_or_rice_card")
    if card_status is True:
        # BPL status satisfied by confirmed possession of White Ration Card / Rice Card
        pass
    elif card_status is False:
        # Confirmed absence of White Ration Card: require locality (rural/urban) and verified income
        area_type = str(profile.get("area_type", "")).strip().lower()
        income = profile.get("annual_income")

        if income is not None and area_type in ["rural", "urban"]:
            valid_inc, parsed_income, inc_err = parse_and_validate_income(income, language)
            if not valid_inc or parsed_income is None:
                reasons.append(inc_err or "Invalid annual income value provided.")
            elif area_type == "rural" and parsed_income > 120000:
                if language == LanguageCode.TE:
                    reasons.append("గ్రామీణ ప్రాంత వార్షిక ఆదాయ పరిమితి రూ. 1,20,000 (నెలకు రూ. 10,000) మించి ఉంది.")
                else:
                    reasons.append(
                        "Annual family income exceeds the rural statutory threshold of Rs. 1,20,000 (Rs. 10,000/month)."
                    )
            elif area_type == "urban" and parsed_income > 144000:
                if language == LanguageCode.TE:
                    reasons.append("పట్టణ ప్రాంత వార్షిక ఆదాయ పరిమితి రూ. 1,44,000 (నెలకు రూ. 12,000) మించి ఉంది.")
                else:
                    reasons.append(
                        "Annual family income exceeds the urban statutory threshold of Rs. 1,44,000 (Rs. 12,000/month)."
                    )
        else:
            if language == LanguageCode.TE:
                reasons.append("వైట్ రేషన్ కార్డు లేనందున, ప్రాంతం (గ్రామీణ/పట్టణ) మరియు వార్షిక ఆదాయ వివరాలు లేకుండా పేదరిక స్థితిని ధృవీకరించలేము.")
            else:
                reasons.append(
                    "Applicant confirmed absence of White Ration Card; locality (rural/urban) and verified annual family income are required."
                )
    else:
        # Card status is unknown (None, omitted, or unverified)
        if language == LanguageCode.TE:
            reasons.append("వైట్ రేషన్ కార్డు లేదా రైస్ కార్డు స్థితి తెలియదు. దీనిని తప్పనిసరిగా ధృవీకరించాలి.")
        else:
            reasons.append("White Ration Card / Rice Card status is unknown. Card presence or confirmed absence must be verified.")

    # Exclusions:
    # A missing or null exclusion field must NEVER be silently interpreted as False!
    gov_emp = profile.get("is_govt_employee_or_pensioner")
    if gov_emp is True:
        if language == LanguageCode.TE:
            reasons.append("కుటుంబంలో ప్రభుత్వ ఉద్యోగి లేదా ప్రభుత్వ పెన్షనర్ ఉన్నవారు ఈ పింఛనుకు అర్హులు కారు.")
        else:
            reasons.append("Families with regular government employees or pensioners are excluded.")
    elif gov_emp is not False:
        if language == LanguageCode.TE:
            reasons.append("ప్రభుత్వ ఉద్యోగి లేదా పెన్షనర్ మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.")
        else:
            reasons.append("Government employee or pensioner exclusion status must be explicitly verified.")

    tax_payer = profile.get("is_income_tax_payer")
    if tax_payer is True:
        if language == LanguageCode.TE:
            reasons.append("కుటుంబంలో ఆదాయపు పన్ను చెల్లించే సభ్యులు ఉన్నవారు మినహాయించబడ్డారు.")
        else:
            reasons.append("Families with income taxpayers are officially excluded.")
    elif tax_payer is not False:
        if language == LanguageCode.TE:
            reasons.append("ఆదాయపు పన్ను చెల్లింపుదారు మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.")
        else:
            reasons.append("Income taxpayer exclusion status must be explicitly verified.")

    four_wheeler = profile.get("owns_four_wheeler")
    if four_wheeler is True:
        if language == LanguageCode.TE:
            reasons.append("నాలుగు చక్రాల వాహనం (కమర్షియల్ ట్రాక్టర్, ఆటో మినహా) కలిగిన కుటుంబాలు అర్హులు కారు.")
        else:
            reasons.append("Ownership of four-wheelers (excluding commercial auto/tractor) disqualifies the family.")
    elif four_wheeler is not False:
        if language == LanguageCode.TE:
            reasons.append("నాలుగు చక్రాల వాహన యాజమాన్య మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.")
        else:
            reasons.append("Four-wheeler vehicle ownership exclusion status must be explicitly verified.")

    is_eligible = len(reasons) == 0
    if is_eligible:
        if language == LanguageCode.TE:
            reasons.append(
                "దరఖాస్తుదారు వృద్ధాప్య పింఛను (OAP) ప్రాథమిక వయస్సు (60+) మరియు సామాజిక-ఆర్థిక నిబంధనలను సంతృప్తిపరిచారు; "
                "తుది మంజూరు క్షేత్రస్థాయి విచారణ మరియు అధికారిక ఉత్తర్వులపై ఆధారపడి ఉంటుంది."
            )
        else:
            reasons.append(
                "Applicant satisfies basic documented age (60+) and socio-economic criteria for Old Age Pension (OAP); "
                "final sanction depends on field verification and official orders."
            )

    return is_eligible, reasons


# =============================================================================
# 4. DR. NTR VAIDYA SEVA (Formerly Dr. YSR Aarogyasri)
# =============================================================================
# Authoritative Source: Dr. NTR Vaidya Seva Trust, Health Dept, Govt of AP
# Verified at: https://aarogyasri.ap.gov.in/web/guest/about-scheme (Verified: 2026-11-22)
#
# Rules:
# - Resident of Andhra Pradesh
# - Qualifying Card or Verified Income check:
#     Must possess valid Rice Card / Dr. NTR Vaidya Seva Health Card.
#     If no card, annual family income MUST be verified <= Rs. 5,00,000 per annum.
#     NEVER return eligible if neither card nor income is verified!
# - Exclusion: Regular government employees covered under Employees Health Scheme (EHS)
# =============================================================================

def _eval_vaidya_seva(
    profile: Dict[str, Any],
    language: LanguageCode,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    state = str(profile.get("state", "")).strip().lower()
    if state not in ["andhra pradesh", "ap"]:
        if language == LanguageCode.TE:
            reasons.append("దరఖాస్తుదారు తప్పనిసరిగా ఆంధ్రప్రదేశ్ నివాసి అయి ఉండాలి.")
        else:
            reasons.append("Applicant must be a permanent resident of Andhra Pradesh.")

    # Poverty-status / Qualifying Card check:
    # Distinguish unknown card status from confirmed absence of Rice Card / Aarogyasri Card
    card_status = profile.get("has_rice_card_or_aarogyasri_card")
    income = profile.get("annual_income")

    if card_status is True:
        # BPL health entitlement satisfied by confirmed possession of Rice Card / Aarogyasri Card
        pass
    elif card_status is False:
        # Confirmed absence of card: verified income <= Rs. 5,00,000 required
        if income is None or (isinstance(income, str) and not income.strip()):
            if language == LanguageCode.TE:
                reasons.append("బియ్యం కార్డు లేదా ఆరోగ్యశ్రీ కార్డు లేనందున, అర్హతను ధృవీకరించడానికి వార్షిక ఆదాయ వివరాలు తప్పనిసరి.")
            else:
                reasons.append("Applicant confirmed absence of Rice Card / Aarogyasri Card; verified annual family income is mandatory.")
        else:
            valid_inc, parsed_income, inc_err = parse_and_validate_income(income, language)
            if not valid_inc or parsed_income is None:
                reasons.append(inc_err or "Invalid annual income value provided.")
            elif parsed_income > 500000:
                if language == LanguageCode.TE:
                    reasons.append("కుటుంబ వార్షిక ఆదాయం గరిష్ట పరిమితి రూ. 5,00,000 మించి ఉంది.")
                else:
                    reasons.append("Annual family income exceeds the ceiling of Rs. 5,00,000 for Vaidya Seva/Aarogyasri.")
    else:
        # Card status is unknown (None, omitted, or unverified)
        if language == LanguageCode.TE:
            reasons.append("బియ్యం కార్డు లేదా ఆరోగ్యశ్రీ కార్డు స్థితి తెలియదు. దీనిని తప్పనిసరిగా ధృవీకరించాలి.")
        else:
            reasons.append("Rice Card / Aarogyasri Card status is unknown. Card presence or confirmed absence must be verified.")

    # Exclusion Check:
    # A missing or null exclusion field must NEVER be silently interpreted as False!
    ehs_val = profile.get("is_regular_govt_employee_with_ehs")
    if ehs_val is True:
        if language == LanguageCode.TE:
            reasons.append("ఉద్యోగుల ఆరోగ్య పథకం (EHS) కింద రక్షణ పొందుతున్న రెగ్యులర్ ప్రభుత్వ ఉద్యోగులు మినహాయించబడ్డారు.")
        else:
            reasons.append("Regular government employees covered under Employees Health Scheme (EHS) are excluded.")
    elif ehs_val is not False:
        if language == LanguageCode.TE:
            reasons.append("ప్రభుత్వ ఉద్యోగం / ఉద్యోగుల ఆరోగ్య పథకం (EHS) మినహాయింపు స్థితిని తప్పనిసరిగా నిర్ధారించాలి.")
        else:
            reasons.append("Government employee / Employees Health Scheme (EHS) exclusion status must be explicitly verified.")

    is_eligible = len(reasons) == 0
    if is_eligible:
        if language == LanguageCode.TE:
            reasons.append(
                "దరఖాస్తుదారు డా. ఎన్టీఆర్ వైద్య సేవ నివాస మరియు పేదరిక నిబంధనలను సంతృప్తిపరిచారు; "
                "ఉచిత చికిత్స నెట్‌వర్క్ ఆసుపత్రులు, ప్రొసీజర్ మాస్టర్ మరియు ప్రీ-ఆథరైజేషన్ అనుమతులకు లోబడి ఉంటుంది."
            )
        else:
            reasons.append(
                "Applicant satisfies documented residency and poverty criteria for Dr. NTR Vaidya Seva; "
                "treatment coverage remains subject to empaneled hospital guidelines, procedure master listing, and pre-authorization."
            )

    return is_eligible, reasons


# =============================================================================
# SCHEME REGISTRY OF OFFICIALLY VERIFIED SCHEMES
# =============================================================================

SCHEME_REGISTRY: Dict[str, SchemeRuleDefinition] = {
    # 1. Non-production synthetic contract test fixture (clearly isolated)
    "scheme_example_001": SchemeRuleDefinition(
        scheme_id="scheme_example_001",
        name_en="[Synthetic Test Example - Not a Real Scheme] Contract Mock Scheme",
        name_te="[టెస్ట్ నమూనా - నిజమైన పథకం కాదు] కాంట్రాక్ట్ మాక్ స్కీమ్",
        required_fields=["state", "occupation", "annual_income"],
        evaluator_fn=_eval_synthetic_test_example,
        benefits_en=[
            "[Test Data] Mock financial assistance of Rs. 13,500 per year",
            "[Test Data] Mock zero-interest crop loans",
        ],
        benefits_te=[
            "[టెస్ట్ సమాచారం] రూ. 13,500 నమూనా ఆర్థిక సాయం",
            "[టెస్ట్ సమాచారం] నమూనా సున్నా వడ్డీ పంట రుణాలు",
        ],
        documents_en=[
            "[Test Document] Aadhaar Card",
            "[Test Document] Land Title Document",
            "[Test Document] Bank Passbook",
        ],
        documents_te=[
            "[టెస్ట్ పత్రం] ఆధార్ కార్డు",
            "[టెస్ట్ పత్రం] భూమి హక్కు పత్రం",
            "[టెస్ట్ పత్రం] బ్యాంక్ పాస్‌బుక్",
        ],
        steps_en=[
            "[Test Step] Submit synthetic test application to local test suite",
        ],
        steps_te=[
            "[టెస్ట్ విధానం] లోకల్ టెస్ట్ సూట్ నందు దరఖాస్తును సమర్పించండి",
        ],
        sources=[
            Source(
                title="[Synthetic Test Data] Non-production test reference",
                url="https://mock-test.internal.local/scheme_example_001",
                publisher="AI Grama Sahayak Test Suite",
                verified_at="2026-11-22",
            )
        ],
        is_synthetic_test=True,
    ),

    # 2. PM-KISAN (National Scheme)
    "pm_kisan": SchemeRuleDefinition(
        scheme_id="pm_kisan",
        name_en="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        name_te="ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి (పీఎం-కిసాన్)",
        required_fields=[
            "is_landholding_farmer",
            "has_aadhaar_linked_bank_account",
            "e_kyc_completed",
            "is_institutional_landholder",
            "holds_constitutional_post",
            "is_elected_representative",
            "is_regular_govt_employee",
            "is_pensioner_10k_plus",
            "paid_income_tax_last_ay",
            "is_registered_professional",
        ],
        evaluator_fn=_eval_pm_kisan,
        benefits_en=[
            "Direct income support of Rs. 6,000 per year transferred in 3 equal four-monthly installments of Rs. 2,000 each via DBT.",
            "Aadhaar-seeded direct payment without intermediaries.",
        ],
        benefits_te=[
            "ఏడాదికి రూ. 6,000 నేరుగా మూడు సమాన విడతలలో (ప్రతి 4 నెలలకు రూ. 2,000 చొప్పున) ఆధార్ లింక్డ్ బ్యాంక్ ఖాతాలో జమ.",
            "మధ్యవర్తులు లేకుండా ప్రత్యక్ష ప్రయోజన బదిలీ (DBT).",
        ],
        documents_en=[
            "Aadhaar Card",
            "Official Land Record showing ownership of cultivable land (Adangal / RoR 1B / Pattadar Passbook)",
            "Aadhaar-seeded Bank Account passbook/statement",
        ],
        documents_te=[
            "ఆధార్ కార్డు",
            "సాగుభూమి యాజమాన్యాన్ని ధృవీకరించే అధికారిక భూ పత్రాలు (అడంగల్ / 1B / పట్టాదారు పాస్‌బుక్)",
            "ఆధార్‌తో లింక్ అయిన బ్యాంక్ ఖాతా వివరాలు",
        ],
        steps_en=[
            "Register on the official PM-KISAN portal (pmkisan.gov.in) or visit nearest CSC/RBK/Grama Sachivalayam",
            "Upload verified land record details and Aadhaar number",
            "Complete mandatory e-KYC authentication via OTP or biometric scan",
            "State / District nodal verification of landholding records",
        ],
        steps_te=[
            "అధికారిక పీఎం-కిసాన్ పోర్టల్ (pmkisan.gov.in) లేదా సమీప గ్రామ సచివాలయం/RBK/CSC లో నమోదు చేసుకోండి",
            "ధృవీకరించబడిన భూ రికార్డు వివరాలు మరియు ఆధార్ నంబర్ నమోదు చేయండి",
            "బయోమెట్రిక్ లేదా OTP ద్వారా తప్పనిసరి ఈ-కేవైసీ పూర్తి చేయండి",
            "జిల్లా/రాష్ట్ర నోడల్ అధికారుల ద్వారా భూమి రికార్డుల ధృవీకరణ",
        ],
        sources=[
            Source(
                title="PM-KISAN Operational Guidelines (Revised)",
                url="https://pmkisan.gov.in/Documents/OperationalGuidelines(Revised).pdf",
                publisher="Department of Agriculture & Farmers Welfare, Ministry of Agriculture & Farmers Welfare, GoI",
                verified_at="2026-11-22",
            )
        ],
    ),

    # 3. NTR Bharosa Social Security Pension (Andhra Pradesh)
    "ntr_bharosa_pension": SchemeRuleDefinition(
        scheme_id="ntr_bharosa_pension",
        name_en="NTR Bharosa Social Security Pension (Old Age Pension Only)",
        name_te="ఎన్టీఆర్ భరోసా సామాజిక భద్రతా పింఛను (వృద్ధాప్య పింఛను మాత్రమే)",
        required_fields=[
            "state",
            "age",
            "is_govt_employee_or_pensioner",
            "is_income_tax_payer",
            "owns_four_wheeler",
        ],
        evaluator_fn=_eval_ntr_bharosa_oap,
        benefits_en=[
            "Monthly social security pension of Rs. 4,000 disbursed directly on the 1st of every month.",
        ],
        benefits_te=[
            "ప్రతినెలా 1వ తేదీన రూ. 4,000 సామాజిక భద్రతా పెన్షన్ ప్రత్యక్ష పంపిణీ.",
        ],
        documents_en=[
            "Aadhaar Card",
            "Age Proof Document (Voter ID / Birth Certificate / School Leaving Certificate)",
            "White Ration Card / Rice Card as BPL proof (or Income Certificate)",
            "Bank Account linked with Aadhaar",
        ],
        documents_te=[
            "ఆధార్ కార్డు",
            "వయస్సు ధృవీకరణ పత్రం (ఓటర్ కార్డు / బర్త్ సర్టిఫికేట్ / ఆధార్)",
            "వైట్ రేషన్ కార్డు / రైస్ కార్డు (లేదా ఆదాయ ధృవీకరణ పత్రం)",
            "ఆధార్‌తో అనుసంధానమైన బ్యాంక్ ఖాతా",
        ],
        steps_en=[
            "Submit application through Welfare Assistant at local Grama / Ward Sachivalayam",
            "Field inquiry and biometric verification by Sachivalayam functionaries",
            "Social audit verification and approval by MPDO / Municipal Commissioner",
        ],
        steps_te=[
            "స్థానిక గ్రామ/వార్డు సచివాలయంలో సంక్షేమ సహాయకునికి దరఖాస్తు సమర్పించండి",
            "సచివాలయ సిబ్బంది క్షేత్రస్థాయి పరిశీలన మరియు బయోమెట్రిక్ ధృవీకరణ",
            "సామాజిక తనిఖీ అనంతరం MPDO / మున్సిపల్ కమిషనర్ ద్వారా ఆమోదం",
        ],
        sources=[
            Source(
                title="SERP Social Security Pensions Portal",
                url="https://sspensions.ap.gov.in",
                publisher="Society for Elimination of Rural Poverty (SERP), PR & RD Department, Government of Andhra Pradesh",
                verified_at="2026-11-22",
            )
        ],
    ),

    # 4. Dr. NTR Vaidya Seva (Andhra Pradesh)
    "dr_ntr_vaidya_seva": SchemeRuleDefinition(
        scheme_id="dr_ntr_vaidya_seva",
        name_en="Dr. NTR Vaidya Seva Scheme (formerly Dr. YSR Aarogyasri)",
        name_te="డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీ)",
        required_fields=[
            "state",
            "is_regular_govt_employee_with_ehs",
        ],
        evaluator_fn=_eval_vaidya_seva,
        benefits_en=[
            "Cashless medical treatment up to Rs. 25,00,000 per family per year across listed secondary and tertiary procedures in empaneled network hospitals with prior authorization.",
            "Coverage across empanelled government and private network hospitals.",
        ],
        benefits_te=[
            "గుర్తింపు పొందిన నెట్‌వర్క్ ఆసుపత్రుల్లో కుటుంబానికి ఏడాదికి రూ. 25,00,000 వరకు ఉచిత నగదు రహిత వైద్య చికిత్స (ప్రీ-ఆథరైజేషన్ నిబంధనలకు లోబడి).",
            "ప్రభుత్వ మరియు ప్రైవేట్ నెట్‌వర్క్ ఆసుపత్రులలో సేవలు.",
        ],
        documents_en=[
            "Dr. NTR Vaidya Seva / Aarogyasri Card or BPL Rice Card (or valid Income Certificate <= 5 Lakhs)",
            "Aadhaar Card of patient",
            "Doctor referral from government hospital/PHC (if required)",
        ],
        documents_te=[
            "డా. ఎన్టీఆర్ వైద్య సేవ / ఆరోగ్యశ్రీ కార్డు లేదా బియ్యం కార్డు (లేదా ఆదాయ ధృవీకరణ పత్రం)",
            "రోగి ఆధార్ కార్డు",
            "ప్రభుత్వ ఆసుపత్రి/PHC నుండి వైద్యుల సిఫార్సు (అవసరమైతే)",
        ],
        steps_en=[
            "Visit the Vaidya Seva / Aarogyasri help desk at any empanelled network hospital",
            "Aarogyamithra performs biometric validation and initiates pre-authorization",
            "Avail comprehensive cashless medical treatment",
        ],
        steps_te=[
            "నెట్‌వర్క్ ఆసుపత్రిలోని వైద్య సేవ / ఆరోగ్యశ్రీ హెల్ప్ డెస్క్‌ను సంప్రదించండి",
            "ఆరోగ్యమిత్ర బయోమెట్రిక్ నమోదు మరియు ప్రీ-ఆథరైజేషన్ పూర్తి చేస్తారు",
            "పూర్తి ఉచిత నగదు రహిత చికిత్స పొందండి",
        ],
        sources=[
            Source(
                title="Dr. NTR Vaidya Seva Trust Portal",
                url="https://drntrvaidyaseva.ap.gov.in",
                publisher="Dr. NTR Vaidya Seva Trust, Health, Medical & Family Welfare Department, Government of Andhra Pradesh",
                verified_at="2026-11-22",
            ),
            Source(
                title="Dr. NTR Vaidya Seva / Aarogyasri Trust Portal",
                url="https://aarogyasri.ap.gov.in/web/guest/about-scheme",
                publisher="Dr. NTR Vaidya Seva Trust, Health Dept, Government of Andhra Pradesh",
                verified_at="2026-11-22",
            ),
        ],
    ),
}

# Alias mapping for legacy names
SCHEME_ALIASES: Dict[str, str] = {
    "ysr_pension_kanuka": "ntr_bharosa_pension",
    "ysr_aarogyasri": "dr_ntr_vaidya_seva",
}

# Schemes under active government restructuring / policy transition
# Where current rules cannot be officially verified from an active Gazette notification
TRANSITIONING_SCHEMES: Dict[str, Dict[str, str]] = {
    "amma_vodi": {
        "en": (
            "The legacy 'Jagananna Amma Vodi' scheme is currently under state policy transition "
            "to 'Thalliki Vandanam' by the Government of Andhra Pradesh. Current operational rules "
            "and disbursement dates cannot be officially certified without published Gazette orders. "
            "Please check with your local Grama / Ward Sachivalayam."
        ),
        "te": (
            "'జగనన్న అమ్మ ఒడి' పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వంచే 'తల్లికి వందనం' పథకంగా మార్పు "
            "చెందుతోంది. అధికారిక గెజిట్ నోటిఫికేషన్ విడుదలయ్యే వరకు ఈ పథక నియమాలను ధృవీకరించడం సాధ్యం కాదు. "
            "దయచేసి మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
        ),
    },
    "thalliki_vandanam": {
        "en": (
            "The 'Thalliki Vandanam' scheme guidelines and operational eligibility rules "
            "are governed by annual administrative notifications issued by the School Education Department. "
            "Formal deterministic certification requires active Gazette orders and school Child Info synchronization. "
            "Mothers and guardians are advised to verify preliminary eligibility at their local Grama / Ward Sachivalayam."
        ),
        "te": (
            "'తల్లికి వందనం' పథక మార్గదర్శకాలు మరియు కార్యాచరణ నిబంధనలు పాఠశాల విద్యాశాఖ వార్షిక పరిపాలనా ఉత్తర్వుల ప్రకారం అమలు చేయబడతాయి. "
            "అధికారిక గెజిట్ మరియు చైల్డ్ ఇన్ఫో సరిపోలిక తర్వాతే తుది మంజూరు లభిస్తుంది. "
            "దయచేసి మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో ప్రాథమిక వివరాలు సరిచూసుకోండి."
        ),
    },
    "talliki_vandanam": {
        "en": (
            "The 'Thalliki Vandanam' scheme guidelines and operational eligibility rules "
            "are governed by annual administrative notifications issued by the School Education Department. "
            "Formal deterministic certification requires active Gazette orders and school Child Info synchronization. "
            "Mothers and guardians are advised to verify preliminary eligibility at their local Grama / Ward Sachivalayam."
        ),
        "te": (
            "'తల్లికి వందనం' పథక మార్గదర్శకాలు మరియు కార్యాచరణ నిబంధనలు పాఠశాల విద్యాశాఖ వార్షిక పరిపాలనా ఉత్తర్వుల ప్రకారం అమలు చేయబడతాయి. "
            "అధికారిక గెజిట్ మరియు చైల్డ్ ఇన్ఫో సరిపోలిక తర్వాతే తుది మంజూరు లభిస్తుంది. "
            "దయచేసి మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో ప్రాథమిక వివరాలు సరిచూసుకోండి."
        ),
    },
    "ysr_rythu_bharosa": {
        "en": (
            "The legacy 'YSR Rythu Bharosa' scheme framework is under administrative restructuring "
            "in Andhra Pradesh. Current official guidelines cannot be certified without active notification. "
            "Farmers are advised to consult their local Rythu Bharosa Kendram (RBK)."
        ),
        "te": (
            "'వైఎస్సార్ రైతు భరోసా' పథకం మార్గదర్శకాలు ప్రస్తుతం పునఃపరిశీలనలో ఉన్నాయి. "
            "ప్రస్తుత నిబంధనలు అధికారికంగా ధృవీకరించబడలేదు. దయచేసి మీ స్థానిక రైతు భరోసా కేంద్రాన్ని (RBK) సంప్రదించండి."
        ),
    },
}


def evaluate_scheme_eligibility(
    scheme_id: str,
    applicant_profile: Dict[str, Any],
    language: LanguageCode = LanguageCode.EN,
) -> Dict[str, Any]:
    """
    Evaluates applicant profile against deterministic, documented scheme rules.

    Strict contract rules:
    - Return ONLY the four agreed status values:
      'eligible', 'ineligible', 'needs_more_information', 'unable_to_verify'.
    - Identify missing applicant fields.
    - Never uses an LLM alone to declare eligibility.
    - If rules are missing or under policy transition, return 'unable_to_verify'.
    """
    clean_scheme_id = scheme_id.strip().lower()

    # 1. Prevent synthetic scheme from ever being evaluated in production
    if clean_scheme_id == "scheme_example_001":
        if getattr(settings, "ENVIRONMENT", "development").lower() == "production":
            return {
                "scheme_id": scheme_id,
                "status": EligibilityStatus.UNABLE_TO_VERIFY,
                "reasons": [
                    "The identifier 'scheme_example_001' is a non-production synthetic test fixture "
                    "and cannot be evaluated in production mode."
                ],
                "missing_fields": [],
                "benefits": [],
                "required_documents": [],
                "application_steps": [],
                "sources": [],
            }

    # 2. Check for schemes under active government policy transition
    if clean_scheme_id in TRANSITIONING_SCHEMES:
        msg = TRANSITIONING_SCHEMES[clean_scheme_id].get(
            language.value,
            TRANSITIONING_SCHEMES[clean_scheme_id]["en"],
        )
        return {
            "scheme_id": scheme_id,
            "status": EligibilityStatus.UNABLE_TO_VERIFY,
            "reasons": [msg],
            "missing_fields": [],
            "benefits": [],
            "required_documents": [],
            "application_steps": [],
            "sources": [],
        }

    # Resolve alias if present
    target_id = SCHEME_ALIASES.get(clean_scheme_id, clean_scheme_id)
    scheme = SCHEME_REGISTRY.get(target_id)

    # 3. Unknown or undocumented scheme
    if not scheme:
        if language == LanguageCode.TE:
            reason = (
                f"కోరబడిన పథకం '{scheme_id}' కు సంబంధించిన అధికారిక నిబంధనలు ప్రస్తుతం ధృవీకరించబడలేదు. "
                f"ధృవీకరించిన సమాచారం కొరకు దయచేసి అధికారిక ప్రభుత్వ పోర్టల్‌ను చూడండి."
            )
        else:
            reason = (
                f"Documented rules for requested scheme '{scheme_id}' are currently unavailable "
                f"in the verified scheme registry. Status cannot be certified without official guidelines."
            )
        return {
            "scheme_id": scheme_id,
            "status": EligibilityStatus.UNABLE_TO_VERIFY,
            "reasons": [reason],
            "missing_fields": [],
            "benefits": [],
            "required_documents": [],
            "application_steps": [],
            "sources": [],
        }

    # 4. Check for missing baseline required profile fields
    missing_fields: List[str] = []
    validation_reasons: List[str] = []

    for field in scheme.required_fields:
        val = applicant_profile.get(field)
        if (
            val is None
            or (isinstance(val, str) and (not val.strip() or val.strip().lower() in ["none", "null"]))
        ):
            missing_fields.append(field)

    # 4b. Validate 'age' when present in applicant_profile
    if "age" in applicant_profile:
        raw_age = applicant_profile.get("age")
        if raw_age is not None and not (isinstance(raw_age, str) and raw_age.strip().lower() in ["", "none", "null"]):
            valid_age, _, age_err = parse_and_validate_age(raw_age, language)
            if not valid_age:
                if "age" not in missing_fields:
                    missing_fields.append("age")
                if age_err:
                    validation_reasons.append(age_err)

    # 4c. Validate 'annual_income' when present in applicant_profile
    if "annual_income" in applicant_profile:
        raw_income = applicant_profile.get("annual_income")
        if raw_income is not None and not (isinstance(raw_income, str) and raw_income.strip().lower() in ["", "none", "null"]):
            valid_inc, _, inc_err = parse_and_validate_income(raw_income, language)
            if not valid_inc:
                if "annual_income" not in missing_fields:
                    missing_fields.append("annual_income")
                if inc_err:
                    validation_reasons.append(inc_err)

    # 5. Domain-specific mandatory poverty-status & card checks:
    # Explicitly distinguish unknown card status from confirmed absence of a qualifying card!
    # A. Dr. NTR Vaidya Seva:
    if target_id == "dr_ntr_vaidya_seva":
        card_status = applicant_profile.get("has_rice_card_or_aarogyasri_card")
        income = applicant_profile.get("annual_income")

        if (
            card_status is None
            or (isinstance(card_status, str) and (not card_status.strip() or card_status.strip().lower() in ["none", "null"]))
        ):
            # Unknown card status: applicant must clarify whether they have a card
            if "has_rice_card_or_aarogyasri_card" not in missing_fields:
                missing_fields.append("has_rice_card_or_aarogyasri_card")
        elif card_status is False:
            # Confirmed absence of qualifying card: Income MUST be provided
            if (
                income is None
                or (isinstance(income, str) and (not income.strip() or income.strip().lower() in ["none", "null"]))
            ):
                if "annual_income" not in missing_fields:
                    missing_fields.append("annual_income")

    # B. NTR Bharosa Pension:
    elif target_id == "ntr_bharosa_pension":
        card_status = applicant_profile.get("has_white_ration_or_rice_card")

        if (
            card_status is None
            or (isinstance(card_status, str) and (not card_status.strip() or card_status.strip().lower() in ["none", "null"]))
        ):
            # Unknown card status: applicant must clarify whether they have a card
            if "has_white_ration_or_rice_card" not in missing_fields:
                missing_fields.append("has_white_ration_or_rice_card")
        elif card_status is False:
            # Confirmed absence of White Ration Card: Locality and Income MUST be provided
            area_type = applicant_profile.get("area_type")
            income = applicant_profile.get("annual_income")
            if not area_type or area_type not in ["rural", "urban"]:
                if "area_type" not in missing_fields:
                    missing_fields.append("area_type")
            if (
                income is None
                or (isinstance(income, str) and (not income.strip() or income.strip().lower() in ["none", "null"]))
            ):
                if "annual_income" not in missing_fields:
                    missing_fields.append("annual_income")

    if missing_fields:
        reasons_list: List[str] = list(validation_reasons)
        if language == LanguageCode.TE:
            base_reason = f"అర్హతను నిర్ణయించడానికి ఈ క్రింది తప్పనిసరి వివరాలు అవసరం: {', '.join(missing_fields)}."
        else:
            base_reason = (
                f"Evaluation requires missing mandatory applicant profile fields: "
                f"{', '.join(missing_fields)}."
            )
        reasons_list.append(base_reason)
        return {
            "scheme_id": scheme_id,
            "status": EligibilityStatus.NEEDS_MORE_INFORMATION,
            "reasons": reasons_list,
            "missing_fields": missing_fields,
            "benefits": [],
            "required_documents": [],
            "application_steps": [],
            "sources": scheme.sources,
        }

    # 6. Deterministic evaluation against documented rules
    is_eligible, reasons = scheme.evaluator_fn(applicant_profile, language)

    if is_eligible is None:
        status = EligibilityStatus.UNABLE_TO_VERIFY
    elif is_eligible:
        status = EligibilityStatus.ELIGIBLE
    else:
        status = EligibilityStatus.INELIGIBLE

    benefits = scheme.benefits_te if language == LanguageCode.TE else scheme.benefits_en
    documents = scheme.documents_te if language == LanguageCode.TE else scheme.documents_en
    steps = scheme.steps_te if language == LanguageCode.TE else scheme.steps_en

    return {
        "scheme_id": scheme_id,
        "status": status,
        "reasons": reasons,
        "missing_fields": [],
        "benefits": benefits if is_eligible else [],
        "required_documents": documents if is_eligible else [],
        "application_steps": steps if is_eligible else [],
        "sources": scheme.sources,
    }
