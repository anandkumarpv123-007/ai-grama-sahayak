"""Document Field Parser.

Extracts structured fields from raw document text for common Andhra Pradesh
citizen public certificates (Income Certificate, Caste Certificate, Rice/Ration Card,
Patta Passbook/RoR-1B, and General Documents).
"""

import re
from typing import Dict, Any, List, Tuple, Optional

# Expected required fields per document type for checklist status evaluation
DOCUMENT_CHECKLISTS: Dict[str, List[str]] = {
    "income_certificate": [
        "certificate_number",
        "applicant_name",
        "annual_income",
        "issue_date",
    ],
    "caste_certificate": [
        "certificate_number",
        "applicant_name",
        "caste_category",
        "issue_date",
    ],
    "ration_card": [
        "ration_card_number",
        "head_of_family",
        "district",
    ],
    "rice_card": [
        "ration_card_number",
        "head_of_family",
        "district",
    ],
    "patta_passbook": [
        "khata_number",
        "pattadar_name",
        "survey_number",
    ],
    "aadhaar_card": [
        "aadhaar_number",
        "name",
        "year_of_birth_or_dob",
    ],
    "general_document": [
        "document_number",
    ],
}

AP_DISTRICTS = [
    "Alluri Sitharama Raju",
    "Anakapalli",
    "Ananthapuramu",
    "Annamayya",
    "Bapatla",
    "Chittoor",
    "Dr. B.R. Ambedkar Konaseema",
    "East Godavari",
    "Eluru",
    "Guntur",
    "Kakinada",
    "Krishna",
    "Kurnool",
    "Nandyal",
    "NTR",
    "Palnadu",
    "Parvathipuram Manyam",
    "Prakasam",
    "Sri Potti Sriramulu Nellore",
    "Sri Sathya Sai",
    "Srikakulam",
    "Tirupati",
    "Visakhapatnam",
    "Vizianagaram",
    "West Godavari",
    "YSR Kadapa",
]


def detect_document_type(text: str, user_hint: Optional[str] = None) -> str:
    """Identify the document type from user hint or text content."""
    if user_hint and user_hint.strip():
        hint = user_hint.strip().lower().replace(" ", "_").replace("-", "_")
        if hint in DOCUMENT_CHECKLISTS:
            return hint
        # Normalize synonyms
        if "income" in hint:
            return "income_certificate"
        if "caste" in hint or "community" in hint:
            return "caste_certificate"
        if "ration" in hint or "rice" in hint or "food" in hint:
            return "ration_card"
        if "patta" in hint or "passbook" in hint or "ror" in hint:
            return "patta_passbook"
        if "aadhaar" in hint or "uidai" in hint:
            return "aadhaar_card"
        return hint

    lower_text = text.lower()

    if (
        "income certificate" in lower_text
        or "annual income" in lower_text
        or "family income" in lower_text
    ):
        return "income_certificate"

    if (
        "caste certificate" in lower_text
        or "community certificate" in lower_text
        or "sub-caste" in lower_text
        or ("community" in lower_text and "certificate" in lower_text)
        or ("caste" in lower_text and "certificate" in lower_text)
    ):
        return "caste_certificate"

    if (
        "rice card" in lower_text
        or "ration card" in lower_text
        or "food security card" in lower_text
    ):
        return "ration_card"

    if (
        "pattadar passbook" in lower_text
        or "khata no" in lower_text
        or "ror-1b" in lower_text
    ):
        return "patta_passbook"

    if (
        "aadhaar" in lower_text
        or "uidai" in lower_text
        or "unique identification" in lower_text
    ):
        return "aadhaar_card"

    return "general_document"


def _extract_ap_district(text: str) -> Optional[str]:
    for dist in AP_DISTRICTS:
        pattern = r"\b" + re.escape(dist) + r"(?=[A-Z\s,.:;\n]|$|\b)"
        if re.search(pattern, text, re.IGNORECASE):
            return dist
    return None


def _clean_field_val(val: str) -> str:
    return val.strip().strip(":,.-_ \t\r\n")


def parse_fields_from_text(text: str, doc_type: str) -> Dict[str, Any]:
    """Parse key metadata fields from document text based on document type."""
    fields: Dict[str, Any] = {}
    if not text or not text.strip():
        return fields

    # Extract dates: DD/MM/YYYY, DD-MM-YYYY, or YYYY-MM-DD
    date_matches = re.findall(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})\b", text
    )

    district_found = _extract_ap_district(text)
    if district_found:
        fields["district"] = district_found

    # Extract mandal if present (ensure 'Tahsildar' does not trigger false match)
    mandal_match = re.search(
        r"\b(?:Mandal|Tahsil)\s*[:\-]\s*([A-Za-z\s]+?)(?:\s+District|,|\n|$)",
        text,
        re.IGNORECASE,
    )
    if mandal_match:
        mandal_val = _clean_field_val(mandal_match.group(1))
        # Ensure it's not capturing "Tahsildar" title or garbage
        if len(mandal_val) > 2 and len(mandal_val) < 40 and "tahsildar" not in mandal_val.lower():
            fields["mandal"] = mandal_val

    if doc_type == "income_certificate":
        # Certificate Number
        cert_match = (
            re.search(r"\b(IC[0-9]{8,14})\b", text)
            or re.search(
                r"(?:Certificate\s*(?:No|Number)|Application\s*No|Cert\s*No|Application\s*Number)\s*[:\-]?\s*(IC[0-9]{8,14}|DEMO[0-9A-Za-z]+|[A-Za-z0-9\-_/]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if cert_match:
            fields["certificate_number"] = cert_match.group(1).strip()

        # Applicant Name
        name_match = re.search(
            r"(?:certify\s+that\s+(?:Sri|Smt|Kumari)?\s*|Applicant\s*Name\s*[:\-]?\s*|Name\s*[:\-]\s*)([A-Za-z\.\s]+?)(?:,|\s+(?:S/o|D/o|W/o)|\n|$)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            clean_name = _clean_field_val(name_match.group(1))
            if clean_name and len(clean_name) > 1:
                fields["applicant_name"] = clean_name

        # Father / Husband Name
        guardian_match = re.search(
            r"(?:S/o|D/o|W/o|Father(?:'s)?\s*Name|Husband(?:'s)?\s*Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|\s+resident|\s+residing|$)",
            text,
            re.IGNORECASE,
        )
        if guardian_match:
            clean_guardian = _clean_field_val(guardian_match.group(1))
            if clean_guardian and len(clean_guardian) > 1:
                fields["father_or_husband_name"] = clean_guardian

        # Annual Income
        income_match = re.search(
            r"(?:annual\s*income|total\s*income|income\s*is)\s*(?:is\s*)?(?:Rs\.?|INR)?\s*([0-9,]+)(?:\s*/-)?",
            text,
            re.IGNORECASE,
        ) or re.search(r"(?:Rs\.?|INR)\s*([0-9,]+)(?:\s*/-)?", text)
        if income_match:
            raw_inc = income_match.group(1).replace(",", "")
            fields["annual_income"] = f"Rs. {raw_inc}"

        # Issue Date
        issue_date_match = re.search(
            r"(?:Date\s*of\s*Issue|Issued\s*Date|Issue\s*Date|Date)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})",
            text,
            re.IGNORECASE,
        )
        if issue_date_match:
            fields["issue_date"] = issue_date_match.group(1).strip()
        elif date_matches:
            fields["issue_date"] = date_matches[0]

    elif doc_type == "caste_certificate":
        cert_match = (
            re.search(r"\b(CGC[0-9]{8,14}|CC[0-9]{8,14})\b", text)
            or re.search(
                r"(?:Certificate\s*(?:No|Number)|Application\s*No|Cert\s*No)\s*[:\-]?\s*(CGC[0-9]{8,14}|CC[0-9]{8,14}|DEMO[0-9A-Za-z]+|[A-Za-z0-9\-_/]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if cert_match:
            fields["certificate_number"] = cert_match.group(1).strip()

        name_match = re.search(
            r"(?:certify\s+that\s+(?:Sri|Smt|Kumari)?\s*|Applicant\s*Name\s*[:\-]?\s*|Name\s*[:\-]\s*)([A-Za-z\.\s]+?)(?:,|\s+(?:S/o|D/o|W/o|belongs)|\n|$)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            clean_name = _clean_field_val(name_match.group(1))
            if clean_name and len(clean_name) > 1:
                fields["applicant_name"] = clean_name

        # Caste category
        caste_match = re.search(
            r"\b(SC|ST|BC-[A-E]|BC\s*[A-E]|OBC|OC|Backward\s*Class|Scheduled\s*Caste|Scheduled\s*Tribe)\b",
            text,
            re.IGNORECASE,
        )
        if caste_match:
            fields["caste_category"] = caste_match.group(1).upper().replace(" ", "-")

        if date_matches:
            fields["issue_date"] = date_matches[0]

    elif doc_type in ("ration_card", "rice_card"):
        card_match = (
            re.search(r"\b([WR]AP[0-9]{10,12}|RC[0-9]{10,12})\b", text)
            or re.search(
                r"(?:Ration\s*Card\s*No|Rice\s*Card\s*No|Card\s*No)\s*[:\-]?\s*([WR]AP[0-9]{10,12}|RC[0-9]{10,12}|DEMO[0-9A-Za-z]+|[A-Za-z0-9]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if card_match:
            fields["ration_card_number"] = card_match.group(1).strip()

        hof_match = re.search(
            r"(?:Head\s*of\s*(?:the\s*)?Family|Head\s*of\s*Household|Name\s*of\s*Head)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|District|\s+District|$)",
            text,
            re.IGNORECASE,
        )
        if hof_match:
            fields["head_of_family"] = _clean_field_val(hof_match.group(1))

    elif doc_type == "patta_passbook":
        khata_match = re.search(r"(?:Khata\s*No|Khata\s*Number)\s*[:\-]?\s*([0-9]+)", text, re.IGNORECASE)
        if khata_match:
            fields["khata_number"] = khata_match.group(1).strip()

        pattadar_match = re.search(
            r"(?:Pattadar\s*Name|Pattadar|Owner\s*Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|$)",
            text,
            re.IGNORECASE,
        )
        if pattadar_match:
            fields["pattadar_name"] = _clean_field_val(pattadar_match.group(1))

        survey_match = re.search(r"(?:Survey\s*No|Sy\s*No)\s*[:\-]?\s*([0-9\-/]+)", text, re.IGNORECASE)
        if survey_match:
            fields["survey_number"] = survey_match.group(1).strip()

    elif doc_type == "aadhaar_card":
        # Mask Aadhaar number for citizen privacy (show only last 4 digits)
        aadhaar_match = re.search(r"\b([0-9]{4}\s+[0-9]{4}\s+[0-9]{4})\b", text) or re.search(r"\b([0-9]{12})\b", text)
        if aadhaar_match:
            raw_uid = aadhaar_match.group(1).replace(" ", "")
            fields["aadhaar_number"] = f"XXXX-XXXX-{raw_uid[-4:]}"

        name_match = re.search(r"(?:Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|DOB|Year|$)", text, re.IGNORECASE)
        if name_match:
            fields["name"] = _clean_field_val(name_match.group(1))

        dob_match = re.search(r"(?:DOB|Birth|Year\s*of\s*Birth)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4})", text, re.IGNORECASE)
        if dob_match:
            fields["year_of_birth_or_dob"] = dob_match.group(1).strip()

    else:
        # General Document fallback
        num_match = re.search(r"(?:Number|No|ID|Ref)\s*[:\-]?\s*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if num_match:
            fields["document_number"] = num_match.group(1).strip()
        name_match = re.search(r"(?:Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|$)", text, re.IGNORECASE)
        if name_match:
            fields["name"] = _clean_field_val(name_match.group(1))
        if date_matches:
            fields["date"] = date_matches[0]

    return fields


def evaluate_checklist(
    doc_type: str, extracted_fields: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """Determine checklist status and list missing required fields.

    Returns:
        (checklist_status, missing_fields)
        checklist_status is one of: 'complete', 'partially_complete', 'incomplete', 'unverified_or_incomplete'
    """
    required_fields = DOCUMENT_CHECKLISTS.get(doc_type, ["document_number"])

    if not extracted_fields:
        return "unverified_or_incomplete", list(required_fields)

    missing: List[str] = []
    present_count = 0

    for field in required_fields:
        if field in extracted_fields and str(extracted_fields[field]).strip():
            present_count += 1
        else:
            missing.append(field)

    if present_count == len(required_fields):
        status = "complete"
    elif present_count > 0:
        status = "partially_complete"
    else:
        status = "unverified_or_incomplete"

    return status, missing
