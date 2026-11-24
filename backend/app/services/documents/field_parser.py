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

# 26 Official Districts of Andhra Pradesh (reorganized April 2022)
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

# Canonical district mapping supporting case-insensitivity, common abbreviations,
# legacy spellings, and Telugu district names.
AP_DISTRICT_SYNONYMS: Dict[str, str] = {
    # Alluri Sitharama Raju
    "alluri sitharama raju": "Alluri Sitharama Raju",
    "alluri sitharamaraju": "Alluri Sitharama Raju",
    "alluri seetharama raju": "Alluri Sitharama Raju",
    "asr": "Alluri Sitharama Raju",
    "asr district": "Alluri Sitharama Raju",
    "అల్లూరి సీతారామరాజు": "Alluri Sitharama Raju",
    "పాడేరు": "Alluri Sitharama Raju",
    "paderu": "Alluri Sitharama Raju",
    # Anakapalli
    "anakapalli": "Anakapalli",
    "anakapalle": "Anakapalli",
    "అనకాపల్లి": "Anakapalli",
    # Ananthapuramu
    "ananthapuramu": "Ananthapuramu",
    "anantapur": "Ananthapuramu",
    "anantapuramu": "Ananthapuramu",
    "అనంతపురం": "Ananthapuramu",
    "అనంతపురము": "Ananthapuramu",
    # Annamayya
    "annamayya": "Annamayya",
    "annamaiah": "Annamayya",
    "రాయచోటి": "Annamayya",
    "rayachoti": "Annamayya",
    # Bapatla
    "bapatla": "Bapatla",
    "బాపట్ల": "Bapatla",
    # Chittoor
    "chittoor": "Chittoor",
    "chittur": "Chittoor",
    "చిత్తూరు": "Chittoor",
    # Dr. B.R. Ambedkar Konaseema
    "dr. b.r. ambedkar konaseema": "Dr. B.R. Ambedkar Konaseema",
    "dr b r ambedkar konaseema": "Dr. B.R. Ambedkar Konaseema",
    "konaseema": "Dr. B.R. Ambedkar Konaseema",
    "కోనసీమ": "Dr. B.R. Ambedkar Konaseema",
    "అమలాపురం": "Dr. B.R. Ambedkar Konaseema",
    "amalapuram": "Dr. B.R. Ambedkar Konaseema",
    # East Godavari
    "east godavari": "East Godavari",
    "తూర్పు గోదావరి": "East Godavari",
    "రాజమండ్రి": "East Godavari",
    "rajamahendravaram": "East Godavari",
    "rajahmundry": "East Godavari",
    # Eluru
    "eluru": "Eluru",
    "ఏలూరు": "Eluru",
    # Guntur
    "guntur": "Guntur",
    "గుంటూరు": "Guntur",
    # Kakinada
    "kakinada": "Kakinada",
    "కాకినాడ": "Kakinada",
    # Krishna
    "krishna": "Krishna",
    "కృష్ణా": "Krishna",
    "మచిలీపట్నం": "Krishna",
    "machilipatnam": "Krishna",
    # Kurnool
    "kurnool": "Kurnool",
    "కర్నూలు": "Kurnool",
    # Nandyal
    "nandyal": "Nandyal",
    "నంద్యాల": "Nandyal",
    # NTR
    "ntr": "NTR",
    "ntr district": "NTR",
    "vijayawada": "NTR",
    "విజయవాడ": "NTR",
    "ఎన్టీఆర్": "NTR",
    # Palnadu
    "palnadu": "Palnadu",
    "పల్నాడు": "Palnadu",
    "నరసరావుపేట": "Palnadu",
    "narasaraopet": "Palnadu",
    # Parvathipuram Manyam
    "parvathipuram manyam": "Parvathipuram Manyam",
    "parvathipuram": "Parvathipuram Manyam",
    "manyam": "Parvathipuram Manyam",
    "పార్వతీపురం మన్యం": "Parvathipuram Manyam",
    "పార్వతీపురం": "Parvathipuram Manyam",
    # Prakasam
    "prakasam": "Prakasam",
    "ప్రకాశం": "Prakasam",
    "ఒంగోలు": "Prakasam",
    "ongole": "Prakasam",
    # Sri Potti Sriramulu Nellore
    "sri potti sriramulu nellore": "Sri Potti Sriramulu Nellore",
    "spsr nellore": "Sri Potti Sriramulu Nellore",
    "sps nellore": "Sri Potti Sriramulu Nellore",
    "nellore": "Sri Potti Sriramulu Nellore",
    "నెల్లూరు": "Sri Potti Sriramulu Nellore",
    # Sri Sathya Sai
    "sri sathya sai": "Sri Sathya Sai",
    "sathya sai": "Sri Sathya Sai",
    "పుట్టపర్తి": "Sri Sathya Sai",
    "puttaparthi": "Sri Sathya Sai",
    # Srikakulam
    "srikakulam": "Srikakulam",
    "శ్రీకాకుళం": "Srikakulam",
    # Tirupati
    "tirupati": "Tirupati",
    "తిరుపతి": "Tirupati",
    # Visakhapatnam
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "విశాఖపట్నం": "Visakhapatnam",
    # Vizianagaram
    "vizianagaram": "Vizianagaram",
    "విజయనగరం": "Vizianagaram",
    # West Godavari
    "west godavari": "West Godavari",
    "పశ్చిమ గోదావరి": "West Godavari",
    "భీమవరం": "West Godavari",
    "bhimavaram": "West Godavari",
    # YSR Kadapa
    "ysr kadapa": "YSR Kadapa",
    "ysr": "YSR Kadapa",
    "kadapa": "YSR Kadapa",
    "కడప": "YSR Kadapa",
}


def normalize_district(dist: Optional[str]) -> Optional[str]:
    """Normalize any district name, synonym, abbreviation or Telugu variant to canonical AP district."""
    if not dist or not dist.strip():
        return None
    raw = dist.strip().lower()
    # Check exact synonym map
    if raw in AP_DISTRICT_SYNONYMS:
        return AP_DISTRICT_SYNONYMS[raw]
    # Check substring match against official districts
    for canonical in AP_DISTRICTS:
        if raw == canonical.lower() or raw in canonical.lower():
            return canonical
    return dist.strip().title()


def detect_document_type(text: str, user_hint: Optional[str] = None) -> str:
    """Identify the document type from user hint or text content.

    If user_hint indicates auto detection or is empty/generic, inspects the extracted text
    honestly.
    """
    clean_hint = (user_hint or "").strip().lower().replace(" ", "_").replace("-", "_")

    # If the user supplied a specific explicit hint (other than auto detect), respect it
    AUTO_DETECT_HINTS = {
        "", "auto", "auto_detect", "autodetect", "auto_detection", "none",
        "undefined", "null", "--_auto_detect_--", "other", "general_document"
    }
    if clean_hint and clean_hint not in AUTO_DETECT_HINTS:
        if clean_hint in DOCUMENT_CHECKLISTS:
            return clean_hint
        if "income" in clean_hint:
            return "income_certificate"
        if "caste" in clean_hint or "community" in clean_hint:
            return "caste_certificate"
        if "ration" in clean_hint or "rice" in clean_hint or "food" in clean_hint:
            return "ration_card"
        if "patta" in clean_hint or "passbook" in clean_hint or "ror" in clean_hint:
            return "patta_passbook"
        if "aadhaar" in clean_hint or "uidai" in clean_hint:
            return "aadhaar_card"
        return clean_hint

    # Auto detect from text content (English & Telugu)
    lower_text = text.lower()

    # 1. Income Certificate (English & Telugu)
    if (
        "income certificate" in lower_text
        or "annual income" in lower_text
        or "family income" in lower_text
        or "total income" in lower_text
        or "ఆదాయ ధ్రువీకరణ" in lower_text
        or "ఆదాయ ధృవీకరణ" in lower_text
        or "వార్షిక ఆదాయం" in lower_text
        or "కుటుంబ ఆదాయం" in lower_text
        or "certificate of income" in lower_text
        or ("income" in lower_text and "certificate" in lower_text)
    ):
        return "income_certificate"

    # 2. Caste Certificate (English & Telugu)
    if (
        "caste certificate" in lower_text
        or "community certificate" in lower_text
        or "sub-caste" in lower_text
        or ("community" in lower_text and "certificate" in lower_text)
        or ("caste" in lower_text and "certificate" in lower_text)
        or "కుల ధ్రువీకరణ" in lower_text
        or "కుల ధృవీకరణ" in lower_text
        or "కుల సర్టిఫికేట్" in lower_text
        or "community, nativity" in lower_text
        or "nativity and date of birth" in lower_text
    ):
        return "caste_certificate"

    # 3. Rice / Ration Card (English & Telugu)
    if (
        "rice card" in lower_text
        or "ration card" in lower_text
        or "food security card" in lower_text
        or "రైస్ కార్డు" in lower_text
        or "రైస్ కార్డ్" in lower_text
        or "బియ్యం కార్డు" in lower_text
        or "రేషన్ కార్డు" in lower_text
        or "ఆహార భద్రత కార్డు" in lower_text
        or ("civil supplies" in lower_text and "card" in lower_text)
    ):
        return "ration_card"

    # 4. Patta Passbook / RoR-1B (English & Telugu)
    if (
        "pattadar passbook" in lower_text
        or "khata no" in lower_text
        or "ror-1b" in lower_text
        or "పట్టాదారు పాస్" in lower_text
        or "అడంగల్" in lower_text
        or "1-b" in lower_text
    ):
        return "patta_passbook"

    # 5. Aadhaar Card (English & Telugu)
    if (
        "aadhaar" in lower_text
        or "uidai" in lower_text
        or "unique identification" in lower_text
        or "ఆధార్" in lower_text
        or "విశిష్ట గుర్తింపు" in lower_text
        or "mera aadhaar" in lower_text
        or "help@uidai" in lower_text
        or "www.uidai" in lower_text
        or "1947" in lower_text
        or re.search(r"\b\d{4}\s+\d{4}\s+\d{4}\b", text)
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
        # Certificate Number (English & Telugu)
        cert_match = (
            re.search(r"\b(IC[0-9]{8,14}|WIC[0-9]{8,14}|APIC[0-9]{8,14})\b", text)
            or re.search(
                r"(?:Certificate\s*(?:No|Number)|Application\s*No|Cert\s*No|Application\s*Number|దరఖాస్తు\s*సంఖ్య|సర్టిఫికేట్\s*నంబర్)\s*[:\-]?\s*(IC[0-9]{8,14}|WIC[0-9]{8,14}|APIC[0-9]{8,14}|DEMO[0-9A-Za-z]+|[A-Za-z0-9\-_/]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if cert_match:
            fields["certificate_number"] = cert_match.group(1).strip()

        # Applicant Name (English & Telugu)
        name_match = (
            re.search(
                r"(?:certify\s+that\s+(?:Sri/Smt/Kumari|Sri\s*/\s*Smt\s*/\s*Kumari|Sri|Smt|Kumari)?\s*|Applicant\s*Name\s*[:\-]?\s*|Name\s*of\s*the\s*Applicant\s*[:\-]?\s*|Name\s*[:\-]\s*)([A-Za-z\.\s]+?)(?:,|\s+(?:S/o|D/o|W/o)|\n|$)",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:దరఖాస్తుదారు(?:\s*పేరు)?|పేరు)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\s+(?:తండ్రి|భర్త|S/o|D/o|W/o)|\n|$)",
                text,
            )
        )
        if name_match:
            clean_name = _clean_field_val(name_match.group(1))
            if clean_name and len(clean_name) > 1:
                fields["applicant_name"] = clean_name

        # Father / Husband Name (English & Telugu)
        guardian_match = (
            re.search(
                r"(?:S/o|D/o|W/o|Father(?:'s)?\s*Name|Husband(?:'s)?\s*Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|\s+resident|\s+residing|$)",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:తండ్రి(?:\s*పేరు)?|భర్త(?:\s*పేరు)?)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\n|\s+నివాసి|\s+గ్రామము|$)",
                text,
            )
        )
        if guardian_match:
            clean_guardian = _clean_field_val(guardian_match.group(1))
            if clean_guardian and len(clean_guardian) > 1:
                fields["father_or_husband_name"] = clean_guardian

        # Annual Income (English & Telugu)
        income_match = (
            re.search(
                r"(?:annual\s*income|total\s*income|family\s*income|income\s*is)\s*(?:is\s*)?(?:Rs\.?|INR)?\s*([0-9,]+)(?:\s*/-)?",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:వార్షిక\s*ఆదాయం|కుటుంబ\s*ఆదాయం|ఆదాయం)\s*(?:రూ\.?|INR|Rs\.?)?\s*([0-9,]+)(?:\s*/-)?",
                text,
            )
            or re.search(r"(?:Rs\.?|INR|రూ\.?)\s*([0-9,]+)(?:\s*/-)?", text)
        )
        if income_match:
            raw_inc = income_match.group(1).replace(",", "")
            fields["annual_income"] = f"Rs. {raw_inc}"

        # Issue Date
        issue_date_match = re.search(
            r"(?:Date\s*of\s*Issue|Issued\s*Date|Issue\s*Date|Date|తేదీ|జారీ\s*తేదీ)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})",
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
                r"(?:Certificate\s*(?:No|Number)|Application\s*No|Cert\s*No|దరఖాస్తు\s*సంఖ్య)\s*[:\-]?\s*(CGC[0-9]{8,14}|CC[0-9]{8,14}|DEMO[0-9A-Za-z]+|[A-Za-z0-9\-_/]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if cert_match:
            fields["certificate_number"] = cert_match.group(1).strip()

        name_match = (
            re.search(
                r"(?:certify\s+that\s+(?:Sri/Smt/Kumari|Sri|Smt|Kumari)?\s*|Applicant\s*Name\s*[:\-]?\s*|Name\s*[:\-]\s*)([A-Za-z\.\s]+?)(?:,|\s+(?:S/o|D/o|W/o|belongs)|\n|$)",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:దరఖాస్తుదారు(?:\s*పేరు)?|పేరు)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\s+(?:తండ్రి|భర్త|S/o|D/o|W/o)|\n|$)",
                text,
            )
        )
        if name_match:
            clean_name = _clean_field_val(name_match.group(1))
            if clean_name and len(clean_name) > 1:
                fields["applicant_name"] = clean_name

        # Caste category (English & Telugu)
        caste_match = (
            re.search(
                r"\b(SC|ST|BC-[A-E]|BC\s*[A-E]|OBC|OC|Backward\s*Class|Scheduled\s*Caste|Scheduled\s*Tribe)\b",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(ఎస్సీ|ఎస్టీ|బీసీ-[ఎ-ఇ]|బీసీ|ఓబీసీ|ఓసీ)",
                text,
            )
        )
        if caste_match:
            fields["caste_category"] = caste_match.group(1).upper().replace(" ", "-")

        if date_matches:
            fields["issue_date"] = date_matches[0]

    elif doc_type in ("ration_card", "rice_card"):
        card_match = (
            re.search(r"\b([WR]AP[0-9]{10,12}|RC[0-9]{10,12})\b", text)
            or re.search(
                r"(?:Ration\s*Card\s*No|Rice\s*Card\s*No|Card\s*No|కార్డు\s*నంబర్)\s*[:\-]?\s*([WR]AP[0-9]{10,12}|RC[0-9]{10,12}|DEMO[0-9A-Za-z]+|[A-Za-z0-9]+)",
                text,
                re.IGNORECASE,
            )
            or re.search(r"\b(DEMO[0-9A-Za-z]+)\b", text)
        )
        if card_match:
            fields["ration_card_number"] = card_match.group(1).strip()

        hof_match = (
            re.search(
                r"(?:Head\s*of\s*(?:the\s*)?Family|Head\s*of\s*Household|Name\s*of\s*Head)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|District|\s+District|$)",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:కుటుంబ\s*పెద్ద(?:\s*పేరు)?|యజమాని(?:\s*పేరు)?)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\n|జిల్లా|$)",
                text,
            )
        )
        if hof_match:
            fields["head_of_family"] = _clean_field_val(hof_match.group(1))

    elif doc_type == "patta_passbook":
        khata_match = re.search(r"(?:Khata\s*No|Khata\s*Number|ఖాతా\s*నంబర్)\s*[:\-]?\s*([0-9]+)", text, re.IGNORECASE)
        if khata_match:
            fields["khata_number"] = khata_match.group(1).strip()

        pattadar_match = (
            re.search(
                r"(?:Pattadar\s*Name|Pattadar|Owner\s*Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|$)",
                text,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:పట్టాదారు(?:\s*పేరు)?|భూయజమాని)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\n|$)",
                text,
            )
        )
        if pattadar_match:
            fields["pattadar_name"] = _clean_field_val(pattadar_match.group(1))

        survey_match = re.search(r"(?:Survey\s*No|Sy\s*No|సర్వే\s*నంబర్)\s*[:\-]?\s*([0-9\-/]+)", text, re.IGNORECASE)
        if survey_match:
            fields["survey_number"] = survey_match.group(1).strip()

    elif doc_type == "aadhaar_card":
        # Mask Aadhaar number for citizen privacy (show only last 4 digits)
        aadhaar_match = re.search(r"\b([0-9]{4}\s+[0-9]{4}\s+[0-9]{4})\b", text) or re.search(r"\b([0-9]{12})\b", text)
        if aadhaar_match:
            raw_uid = aadhaar_match.group(1).replace(" ", "")
            fields["aadhaar_number"] = f"XXXX-XXXX-{raw_uid[-4:]}"

        # Detect front vs back card side
        is_back = bool(
            re.search(r"(?:Address|చిరునామా|S/O|D/O|W/O|help@uidai|www\.uidai|1947)", text, re.IGNORECASE)
            and not re.search(r"(?:DOB|పుట్టిన\s*తేదీ|Year\s*of\s*Birth|Male|Female|పురుషుడు|స్త్రీ)", text, re.IGNORECASE)
        )
        if is_back:
            fields["card_side"] = "back"
            # Extract Address from back
            addr_match = re.search(
                r"(?:Address|చిరునామా)\s*[:\-/]?\s*([\s\S]+?)(?=\b\d{4}\s+\d{4}\s+\d{4}\b|\b1947\b|\bhelp@|www\.uidai|$)",
                text,
                re.IGNORECASE,
            )
            if addr_match:
                fields["address"] = " ".join(addr_match.group(1).split())
        else:
            fields["card_side"] = "front"

        # Name extraction (English & Telugu)
        name_match = (
            re.search(r"(?:Name)\s*[:\-]?\s*([A-Za-z\.\s]+?)(?:,|\n|DOB|Year|$)", text, re.IGNORECASE)
            or re.search(r"(?:పేరు)\s*[:\-]?\s*([\u0c00-\u0c7fA-Za-z\.\s]+?)(?:,|\n|తేదీ|DOB|$)", text)
        )
        if name_match:
            fields["name"] = _clean_field_val(name_match.group(1))
        else:
            # Fallback heuristic for standard Aadhaar front: look for line before DOB
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for idx, line in enumerate(lines):
                if re.search(r"(?:DOB|Birth|పుట్టిన\s*తేదీ)", line, re.IGNORECASE) and idx > 0:
                    cand = lines[idx - 1]
                    if not any(kw in cand.lower() for kw in ["government", "భారత", "india", "authority", "uidai"]):
                        clean_cand = _clean_field_val(cand)
                        if len(clean_cand) > 2 and len(clean_cand) < 50:
                            fields["name"] = clean_cand
                            break

        # DOB / Year of Birth
        dob_match = re.search(
            r"(?:DOB|Birth|పుట్టిన\s*తేదీ|Year\s*of\s*Birth)\s*[:\-/]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4})",
            text,
            re.IGNORECASE,
        )
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
