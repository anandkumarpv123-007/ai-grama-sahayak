import re
from typing import Any, Dict, List, Optional
from app.schemas.common import LanguageCode

INTENT_APPLICATION = "application"
INTENT_DOCUMENTS = "documents"
INTENT_ELIGIBILITY = "eligibility"
INTENT_BENEFITS = "benefits"
INTENT_STATUS = "status"
INTENT_COMPARISON = "comparison"
INTENT_OVERVIEW = "overview"

# Intent detection regex patterns
INTENT_APPLICATION_PATTERNS = [
    re.compile(r"\b(?:how\s+to\s+apply|how\s+do\s+i\s+apply|how\s+can\s+i\s+apply|apply|application|enroll|enrollment|register|registration|procedure|steps?|where\s+to\s+apply|form|how\s+to\s+get|avail)\b", re.IGNORECASE),
    re.compile(r"దరఖాస్తు|నమోదు|రిజిస్ట్రేషన్|ఎలా\s*దరఖాస్తు|ఎలా\s*నమోదు|ఎలా\s*అప్లై|అప్లై|ఎక్కడ\s*దరఖాస్తు|పద్ధతి|విధానం"),
]

INTENT_DOCUMENTS_PATTERNS = [
    re.compile(r"\b(?:documents?|papers?|paperwork|certificates?|proofs?|passbook|records?|what\s+documents|needed\s+documents|required\s+documents)\b", re.IGNORECASE),
    re.compile(r"పత్రాలు|కావాల్సిన\s*పత్రాలు|అవసరమైన\s*పత్రాలు|డాక్యుమెంట్లు|సర్టిఫికెట్లు|ధ్రువపత్రాలు|పాస్‌బుక్|పాసుపుస్తకం"),
]

INTENT_ELIGIBILITY_PATTERNS = [
    re.compile(r"\b(?:eligibility|eligible|who\s+is\s+eligible|who\s+qualifies|who\s+can\s+apply|criteria|qualifications?|conditions?|rules?|income\s+limit|age\s+limit|tenant\s+farmers?|who\s+gets)\b", re.IGNORECASE),
    re.compile(r"అర్హత|అర్హతలు|అర్హులు|ఎవరు\s*అర్హులు|అర్హుల\s*జాబితా|నిబంధనలు|షరతులు|కౌలు\s*రైతులు|పరిమితి"),
]

INTENT_BENEFITS_PATTERNS = [
    re.compile(r"\b(?:benefits?|financial\s+assistance|amount|how\s+much|money|payout|installment|rate|fund|pension\s+amount|subsidy|aid)\b", re.IGNORECASE),
    re.compile(r"ప్రయోజనాలు|ఆర్థిక\s*సహాయం|ఎంత|సహాయం|మొత్తం|విడత|డబ్బులు|రూపాయలు|రేటు|పింఛను\s*మొత్తం|లబ్ధి"),
]

INTENT_STATUS_PATTERNS = [
    re.compile(r"\b(?:check\s+status|payment\s+status|status|beneficiary\s+list|verify\s+status|tracking)\b", re.IGNORECASE),
    re.compile(r"స్థితి|స్టేటస్|తనిఖీ|పరిశీలన|చెల్లింపు\s*స్థితి|లబ్ధిదారుల\s*జాబితా|జాబితా"),
]

INTENT_COMPARISON_PATTERNS = [
    re.compile(r"\b(?:difference\s+between|compare|comparison|versus|vs|what\s+happened\s+to|earlier\s+scheme|previous\s+scheme|erstwhile|formerly|successor)\b", re.IGNORECASE),
    re.compile(r"తేడా|వ్యత్యాసం|పోలిక|మధ్య\s*తేడా|గతంలో|పూర్వపు|పాత\s*పథకం"),
]


def detect_query_intent(query: str, language: LanguageCode) -> str:
    """
    Classifies citizen question into a primary functional intent.
    Matches specific actionable intents (application, documents, eligibility, benefits, comparison)
    before falling back to general scheme overview.
    """
    if not query:
        return INTENT_OVERVIEW

    q = query.strip()

    # 1. Comparison intent check
    if any(p.search(q) for p in INTENT_COMPARISON_PATTERNS):
        return INTENT_COMPARISON

    # 2. Application procedure intent
    if any(p.search(q) for p in INTENT_APPLICATION_PATTERNS):
        return INTENT_APPLICATION

    # 3. Required documents intent
    if any(p.search(q) for p in INTENT_DOCUMENTS_PATTERNS):
        return INTENT_DOCUMENTS

    # 4. Eligibility intent
    if any(p.search(q) for p in INTENT_ELIGIBILITY_PATTERNS):
        return INTENT_ELIGIBILITY

    # 5. Financial benefits intent
    if any(p.search(q) for p in INTENT_BENEFITS_PATTERNS):
        return INTENT_BENEFITS

    # 6. Status check intent
    if any(p.search(q) for p in INTENT_STATUS_PATTERNS):
        return INTENT_STATUS

    return INTENT_OVERVIEW


def sanitize_english_text(text: str) -> str:
    """
    Enforces strict language isolation for English responses:
    Strips all Telugu Unicode characters (\u0C00-\u0C7F), empty parens, and orphan punctuation.
    Guarantees ZERO Telugu script leaks into English responses.
    """
    if not text:
        return ""
    # Remove Telugu script
    cleaned = re.sub(r"[\u0C00-\u0C7F]+", "", text)
    # Remove empty parentheticals left behind like " ()" or " ( )"
    cleaned = re.sub(r"\s*\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s*\[\s*\]", "", cleaned)
    # Normalize multiple whitespace
    lines = []
    for line in cleaned.split("\n"):
        l = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(l)
    return "\n".join(lines).strip()


def sanitize_telugu_text(text: str) -> str:
    """
    Enforces clean Telugu response format:
    Removes full English sentences while preserving URLs, numbers, helplines,
    and recognized acronyms (Aadhaar, NPCI, e-KYC, e-Crop, CCRC, DBT, RSK, RBK, VAA, WEA, OAP).
    """
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for l in lines:
        s = l.strip()
        if not s:
            cleaned_lines.append("")
            continue
        has_url = bool(re.search(r"https?://", s))
        s_no_url = re.sub(r"https?://[^\s]+", "", s)
        en_chars = len(re.findall(r"[a-zA-Z]", s_no_url))
        te_chars = len(re.findall(r"[\u0C00-\u0C7F]", s))
        # Drop lines where English sentence text is predominant (excluding URLs)
        if not has_url and en_chars > 10 and en_chars > te_chars:
            continue
        # Preserve lines with URLs or helplines or Telugu script
        has_te = bool(re.search(r"[\u0C00-\u0C7F]", s))
        has_url_or_num = bool(re.search(r"https?://|\b\d{4,6}\b", s))
        if has_te or has_url_or_num:
            cleaned_lines.append(s)
    return "\n".join(cleaned_lines).strip()


def _chunk_matches_intent(sec_title: str, c_text: str, intent: str) -> bool:
    """Checks whether a chunk's section genuinely corresponds to the query intent."""
    title_lower = sec_title.lower()
    text_lower = c_text.lower()

    if intent == INTENT_OVERVIEW:
        return any(w in title_lower for w in ["overview", "mandate", "objective", "purpose", "1.", "అవలోకనం", "లక్ష్యం", "ఉద్దేశం"])

    if intent == INTENT_APPLICATION:
        is_app = any(w in title_lower for w in [
            "application", "how to apply", "how to enroll", "how to access", "how to obtain",
            "how to avail", "enrollment", "registration", "procedure", "channels", "distribution",
            "modalities", "దరఖాస్తు", "నమోదు", "విధానం", "సేవలు పొందే", "పంపిణీ"
        ])
        is_other = any(w in title_lower for w in ["overview", "1. ", "అవలోకనం"])
        return is_app and not is_other

    if intent == INTENT_DOCUMENTS:
        is_doc = any(w in title_lower for w in ["document", "papers", "proofs", "పత్రాలు", "ధ్రువపత్రాలు"])
        is_other = any(w in title_lower for w in ["overview", "1. ", "అవలోకనం"])
        return is_doc and not is_other

    if intent == INTENT_ELIGIBILITY:
        is_elig = any(w in title_lower for w in [
            "eligibility", "criteria", "beneficiary", "exclusions", "ineligibility",
            "అర్హత", "నిబంధనలు", "అనర్హత", "లబ్ధిదారుల"
        ])
        is_other = any(w in title_lower for w in ["overview", "1. ", "అవలోకనం"])
        return is_elig and not is_other

    if intent == INTENT_BENEFITS:
        is_ben = any(w in title_lower for w in [
            "financial assistance", "assistance framework", "benefits", "entitlement",
            "payout", "rate", "wage", "subvention", "coverage", "scope", "preconditions",
            "పరిమితులు", "సహాయం", "ప్రయోజనాలు", "వేతనాలు", "రాయితీ", "చెల్లింపులు"
        ])
        is_other = any(w in title_lower for w in ["overview", "1. ", "అవలోకనం"])
        return is_ben and not is_other

    if intent == INTENT_COMPARISON:
        return any(w in title_lower or w in text_lower for w in ["comparison", "difference", "transition", "earlier", "erstwhile", "తేడా", "పోలిక", "గతంలో", "పూర్వపు"])

    return False


def extract_bilingual_evidence_from_chunks(
    chunks: Optional[List[Dict[str, Any]]],
    intent: str,
    language: LanguageCode,
    doc_id: Optional[str] = None,
) -> Optional[str]:
    """
    Extracts high-fidelity, grounded bilingual evidence directly from retrieved chunks.
    Prefers actual chunk text matching the citizen's intent over hardcoded statements:
    - In Telugu (TE): Extracts dedicated 'తెలుగు వివరణ' blocks and Telugu narrative,
      preserving URLs, helplines, and technical acronyms.
    - In English (EN): Extracts English narrative and bullet points, strictly eliminating
      any Telugu script or headers.
    Returns cleaned evidence text if substantive (>= 25 words), else None.
    """
    if not chunks:
        return None

    is_te = (language == LanguageCode.TE)

    # Filter chunks by doc_id and genuine intent match
    matching_chunks: List[Dict[str, Any]] = []
    for c in chunks:
        c_dict = c if isinstance(c, dict) else (c.to_dict() if hasattr(c, "to_dict") else getattr(c, "__dict__", {}))
        meta = c_dict.get("metadata", {}) or {}
        c_doc_id = meta.get("doc_id", "")
        sec_title = str(meta.get("section_title", ""))
        c_text = str(c_dict.get("text", ""))

        if doc_id and c_doc_id != doc_id:
            continue

        if _chunk_matches_intent(sec_title, c_text, intent):
            matching_chunks.append(c_dict)

    if not matching_chunks:
        return None

    extracted_sections: List[str] = []
    extracted_portals_and_helplines: List[str] = []

    for c in matching_chunks[:2]:
        raw_text = c.get("text", "").strip()
        if not raw_text:
            continue

        lines = raw_text.split("\n")

        # Extract portals and helplines from the chunk
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#") or "తెలుగు వివరణ" in s:
                continue
            if not is_te and any("\u0C00" <= c <= "\u0C7F" for c in s):
                continue
            if re.search(r"https?://[^\s]+|\b(?:108|104|14555|155251|1800-180-1551|14447|1902|1800-425-6776|1800-425-2123)\b", s):
                if any(w in s.lower() for w in ["portal", "helpline", "toll-free", "పోర్టల్", "హెల్ప్‌లైన్", "ఫోన్", "డయల్"]) or re.match(r"^[\*\-\s]*https?://", s):
                    clean_contact = re.sub(r"^[\*\-•\d\.\s]+", "", s).strip()
                    if not is_te:
                        clean_contact = sanitize_english_text(clean_contact)
                    if clean_contact and clean_contact not in extracted_portals_and_helplines:
                        extracted_portals_and_helplines.append(clean_contact)

        if is_te:
            te_lines = []
            capturing_te = False
            for line in lines:
                s = line.strip()
                if "తెలుగు వివరణ:" in s or "తెలుగు వివరణ" in s:
                    capturing_te = True
                    cleaned_start = re.sub(r"^\*?\s*\**తెలుగు వివరణ:?\**\s*", "", s).strip()
                    if cleaned_start:
                        te_lines.append(cleaned_start)
                    continue
                if capturing_te:
                    if s.startswith("## ") or (s.startswith("* **") and "తెలుగు వివరణ" not in s and re.search(r"[a-zA-Z]{4,}", s)):
                        capturing_te = False
                    else:
                        if s:
                            te_lines.append(s)

            chunk_te = "\n".join(te_lines).strip()
            if not chunk_te:
                te_narrative = []
                for line in lines:
                    s = line.strip()
                    if not s or s.startswith("#") or (s.startswith("[") and s.endswith("]")):
                        continue
                    en_chars = len(re.findall(r"[a-zA-Z]", s))
                    te_chars = len(re.findall(r"[\u0C00-\u0C7F]", s))
                    if te_chars >= 5 and te_chars >= en_chars:
                        te_narrative.append(s)
                chunk_te = "\n".join(te_narrative).strip()

            if chunk_te and len(chunk_te.split()) >= 15 and chunk_te not in extracted_sections:
                extracted_sections.append(chunk_te)

        else:
            en_lines = []
            for line in lines:
                s = line.strip()
                if not s or s.startswith("#") or (s.startswith("[") and s.endswith("]")):
                    continue
                if "తెలుగు వివరణ:" in s or "తెలుగు వివరణ" in s:
                    continue
                # Sanitize line removing any inline Telugu phrases
                clean_line = sanitize_english_text(s)
                if clean_line and len(re.findall(r"[a-zA-Z]", clean_line)) >= 3:
                    en_lines.append(clean_line)

            chunk_en = "\n".join(en_lines).strip()
            if chunk_en and len(chunk_en.split()) >= 15 and chunk_en not in extracted_sections:
                extracted_sections.append(chunk_en)

    if not extracted_sections:
        return None

    evidence_text = "\n\n".join(extracted_sections).strip()

    # Append contact / portals if available and not already in evidence
    if extracted_portals_and_helplines:
        contacts_to_add = [
            cp for cp in extracted_portals_and_helplines
            if cp not in evidence_text
        ]
        if contacts_to_add:
            if is_te:
                contact_header = "\n\n• **అధికారిక పోర్టల్స్ & హెల్ప్‌లైన్లు**:\n"
            else:
                contact_header = "\n\n• **Official Portals & Helplines**:\n"
            contact_body = "\n".join([f"  - {c}" for c in contacts_to_add[:4]])
            evidence_text = f"{evidence_text}{contact_header}{contact_body}"

    # Strict language sanitization on entire evidence
    if is_te:
        evidence_text = sanitize_telugu_text(evidence_text)
    else:
        evidence_text = sanitize_english_text(evidence_text)

    words = evidence_text.split()
    if len(words) < 25:
        return None

    return evidence_text


def _build_location_prefix(title: str, state: Optional[str], district: Optional[str], is_te: bool) -> str:
    """Builds clean, uniform location prefix header for responses."""
    if is_te:
        display_state = "ఆంధ్రప్రదేశ్" if state in ["Andhra Pradesh", "AP", "All India"] else state
    else:
        display_state = state

    if district and display_state:
        loc_str = f"{district}, {display_state}"
        if is_te:
            return f"[{title} - {loc_str} పరిధిలోని అధికారిక సమాచారం]:\n\n" if title else f"[{loc_str} పరిధిలోని అధికారిక సమాచారం]:\n\n"
        return f"[Verified official information on {title} for {loc_str}]:\n\n" if title else f"[Verified official information for {loc_str}]:\n\n"
    elif display_state:
        if is_te:
            return f"[{title} - {display_state} పరిధిలోని అధికారిక సమాచారం]:\n\n" if title else f"[{display_state} పరిధిలోని అధికారిక సమాచారం]:\n\n"
        return f"[Verified official information on {title} for {display_state}]:\n\n" if title else f"[Verified official information for {display_state}]:\n\n"
    elif title:
        if is_te:
            return f"[{title} - అధికారిక సమాచారం]:\n\n"
        return f"[Verified official information on {title}]:\n\n"
    return ""


# Grounded knowledge profiles for all 14 verified schemes
# Fully reconciled with Member 2's verified documents; conservative qualification of benefit claims
SCHEME_PROFILES: Dict[str, Dict[str, Any]] = {
    "agri_annadata_sukhibhava_pmkisan": {
        "title_en": "Annadata Sukhibhava – PM Kisan",
        "title_te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్",
        "portals": ["https://annadathasukhibhava.ap.gov.in", "https://pmkisan.gov.in"],
        "helplines": ["155251", "1902"],
        "overview": {
            "en": "Annadata Sukhibhava – PM Kisan is a farmer welfare and income support framework in Andhra Pradesh operating in convergence with the Central Government's PM-KISAN scheme. The scheme transitions upon the erstwhile Rythu Bharosa framework to provide structured investment assistance and debt relief for farming families.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వం కేంద్ర ప్రభుత్వ పీఎం కిసాన్ పథకంతో సమన్వయం చేసుకుంటూ రూపొందిస్తున్న ప్రధాన రైతు సంక్షేమ పథకం. గతంలో ఉన్న రైతు భరోసా వ్యవస్థ స్థానంలో రైతు కుటుంబాలకు సాగు పెట్టుబడి సాయం అందించి ఆర్థిక భద్రత చేకూర్చడం దీని ముఖ్య ఉద్దేశం.",
        },
        "application": {
            "en": "How to apply for Annadata Sukhibhava – PM Kisan:\n\n• **Enrollment & Verification:** Visit your local Rythu Seva Kendram (RSK) / Rythu Bharosa Kendram (RBK) or Grama / Ward Sachivalayam to meet the Village Agriculture Assistant (VAA). Ground-level field verification and beneficiary listing are carried out here.\n• **Mandatory e-Crop & e-KYC:** Complete crop cultivation booking on the state digital e-Crop (e-Panta) portal and finish biometric or OTP e-KYC on the PM-Kisan portal.\n• **Bank Account Mapping:** Ensure your active bank account is seeded with Aadhaar and mapped with NPCI for Direct Benefit Transfer (DBT).\n• **Official Portals:** Check application status and beneficiary lists at https://annadathasukhibhava.ap.gov.in and https://pmkisan.gov.in.\n• **Helpline & Grievances:** For assistance, contact your VAA or dial the farmer helpline at 155251 or Spandana at 1902.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకానికి దరఖాస్తు మరియు నమోదు విధానం:\n\n• **నమోదు కేంద్రాలు**: మీ సమీపంలోని రైతు సేవా కేంద్రం (RSK) / రైతు భరోసా కేంద్రం (RBK) లేదా గ్రామ/వార్డు సచివాలయాన్ని సందర్శించి గ్రామ వ్యవసాయ సహాయకుడిని (VAA) సంప్రదించండి. క్షేత్రస్థాయి విచారణ మరియు లబ్ధిదారుల నమోదు ఇక్కడే జరుగుతాయి.\n• **ఈ-పంట & ఈ-కేవైసీ**: తప్పనిసరిగా మీ సాగు వివరాలను ఈ-పంట (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో నమోదు చేయించుకోవాలి మరియు పీఎం కిసాన్ పోర్టల్‌లో ఈ-కేవైసీ (e-KYC) పూర్తి చేయాలి.\n• **బ్యాంక్ ఖాతా అనుసంధానం**: సాయం నేరుగా జమ కావడానికి మీ బ్యాంక్ ఖాతాకు ఆధార్ మరియు ఎన్‌పీసీఐ (NPCI) సీడింగ్ యాక్టివ్‌గా ఉండాలి.\n• **అధికారిక పోర్టల్స్**: దరఖాస్తు స్థితి మరియు లబ్ధిదారుల జాబితాను పరిశీలించడానికి:\n  - రాష్ట్ర పోర్టల్: https://annadathasukhibhava.ap.gov.in\n  - కేంద్ర పీఎం కిసాన్ పోర్టల్: https://pmkisan.gov.in\n• **సహాయం & ఫిర్యాదులు**: సమస్యల పరిష్కారం కొరకు గ్రామ వ్యవసాయ సహాయకుడిని కలవండి లేదా రాష్ట్ర రైతు హెల్ప్‌లైన్ 155251 లేదా స్పందన 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Annadata Sukhibhava – PM Kisan:\n\n• **Aadhaar Card:** Aadhaar Card of the applicant farmer and family head.\n• **Land Ownership / Cultivation Proof:** Land Pattadar Passbook, 1-B revenue record from Webland, or valid Crop Cultivator Rights Card (CCRC) agreement for tenant farmers.\n• **Bank Passbook:** Active bank account passbook seeded with Aadhaar and mapped with NPCI for Direct Benefit Transfer.\n• **Active Mobile Number:** Aadhaar-linked mobile number for OTP e-KYC and SMS alerts.\n• **e-Crop Booking:** Digital e-Crop / e-Panta cultivation receipt issued at RSK/RBK.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకానికి అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: రైతు మరియు కుటుంబ పెద్ద ఆధార్ కార్డు.\n• **భూమి రికార్డులు**: పట్టాదారు పాస్‌బుక్, వెబ్‌ల్యాండ్ 1-బి రికార్డు, లేదా కౌలు రైతులకు చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) ఒప్పంద పత్రం.\n• **బ్యాంక్ పాస్‌బుక్**: ఆధార్ మరియు ఎన్‌పీసీఐ (NPCI) తో అనుసంధానమైన బ్యాంక్ ఖాతా పాస్‌బుక్.\n• **మొబైల్ నంబర్**: ఆధార్‌తో లింక్ అయిన యాక్టివ్ మొబైల్ నంబర్ (ఈ-కేవైసీ కొరకు).\n• **ఈ-పంట రసీదు**: రైతు సేవా కేంద్రంలో నమోదైన ఈ-క్రాప్ (e-Crop / e-Panta) రికార్డు.",
        },
        "eligibility": {
            "en": "Eligibility criteria for Annadata Sukhibhava – PM Kisan:\n\n• **Residency:** Bonafide resident farmers cultivating agricultural land in Andhra Pradesh.\n• **Landholders:** Small and marginal landholding farmer families holding cultivable land documented in state Webland records.\n• **Tenant Farmers:** Tenant cultivators holding registered Crop Cultivator Rights Cards (CCRC) for the designated crop season.\n• **Mandatory Compliance:** Valid e-Crop booking, Aadhaar-NPCI seeded bank account, and completed e-KYC.\n• **Exclusions:** Institutional landholders, regular government employees, income tax payees, and constitutional post holders.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ అర్హత నిబంధనలు:\n\n• **స్థానికత**: ఆంధ్రప్రదేశ్‌లో వ్యవసాయ భూమి కలిగి ఉండి సాగుచేస్తున్న రైతులు.\n• **భూ యజమానులు**: అధికారిక వెబ్‌ల్యాండ్ రికార్డుల్లో పేరు నమోదైన చిన్న, సన్నకారు రైతు కుటుంబాలు.\n• **కౌలు రైతులు**: ప్రస్తుత వ్యవసాయ సీజన్‌కు చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) కార్డులు కలిగిన కౌలు రైతులు నిబంధనల ప్రకారం అర్హులు.\n• **తప్పనిసరి నిబంధనలు**: ఈ-పంట (e-Crop) నమోదు, ఆధార్-ఎన్‌పీసీఐ బ్యాంక్ సీడింగ్ మరియు ఈ-కేవైసీ (e-KYC) పూర్తయి ఉండాలి.\n• **మినహాయింపులు**: ప్రభుత్వ ఉద్యోగులు, ఆదాయపు పన్ను చెల్లించేవారు, మరియు సంస్థాగత భూ యజమానులు అనర్హులు.",
        },
        "benefits": {
            "en": "Financial assistance framework under Annadata Sukhibhava – PM Kisan:\n\n• **Central Component (PM-KISAN):** Direct income support of Rs. 6,000 per year disbursed by the Government of India in three equal four-monthly installments of Rs. 2,000 directly into Aadhaar-seeded bank accounts of eligible landholder farmers.\n• **State Financial Assistance Framework:** Under the Annadata Sukhibhava initiative, the Government of Andhra Pradesh plans supplemental state financial assistance as a state top-up for eligible landholding farmer families, alongside planned assistance for eligible tenant farmers.\n• **Operational Condition:** Exact state installment amounts, disbursement schedules, and tenant farmer eligibility criteria are governed by published state government operational guidelines, verified land records, and seasonal administrative orders; state assistance details are subject to published notifications and should not be treated as assured payments until officially notified.\n• **Disbursement Channel:** Direct Benefit Transfer (DBT) into Aadhaar-NPCI active accounts. Official portal: https://annadathasukhibhava.ap.gov.in.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ ఆర్థిక సహాయ వివరాలు:\n\n• **కేంద్ర పీఎం కిసాన్**: అర్హులైన భూ యజమానులకు ఏడాదికి రూ. 6,000 (మూడు విడతల్లో రూ. 2,000 చొప్పున) నేరుగా బ్యాంక్ ఖాతాలో జమ అవుతుంది.\n• **రాష్ట్ర టాప్-అప్ సహాయం**: రాష్ట్ర ప్రభుత్వం అర్హులైన రైతు కుటుంబాలకు మరియు కౌలు రైతులకు రాష్ట్ర టాప్-అప్ ఆర్థిక సహాయాన్ని డీబీటీ (DBT) ద్వారా అందించేందుకు కార్యాచరణ రూపొందిస్తోంది.\n• **ముఖ్య గమనిక**: ఖచ్చితమైన విడతల చెల్లింపులు, తేదీలు మరియు కౌలు రైతుల అర్హత నిబంధనలు రాష్ట్ర ప్రభుత్వం విడుదల చేసే అధికారిక ఉత్తర్వులకు లోబడి ఉంటాయి; అధికారికంగా నోటిఫై చేసే వరకు ఇవి నిశ్చయమైనవిగా భావించరాదు.\n• **చెల్లింపు విధానం**: నిధులు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాలకు నేరుగా బదిలీ అవుతాయి. అధికారిక పోర్టల్: https://annadathasukhibhava.ap.gov.in.",
        },
        "comparison": {
            "en": "Comparison between Rythu Bharosa and Annadata Sukhibhava:\n\n• **Administrative Transition:** Rythu Bharosa is the erstwhile agricultural investment support scheme in Andhra Pradesh, which has been succeeded, restructured, and reformed under the Government of Andhra Pradesh's current **Annadata Sukhibhava – PM Kisan** framework.\n• **Core Purpose:** Annadata Sukhibhava converges Central PM-KISAN benefits (Rs. 6,000/yr) with planned state top-up assistance to support farming investments and relieve agricultural debt.\n• **Enrollment & Verification:** Supported through field e-Crop (e-Panta) booking via Village Agriculture Assistants at Rythu Seva Kendrams (RSK/RBK) and Grama Sachivalayams.\n• **Official Portals:** Official information is available at https://annadathasukhibhava.ap.gov.in and helpline 155251 / 1902.",
            "te": "రైతు భరోసా మరియు అన్నదాత సుఖీభవ మధ్య తేడా మరియు పోలిక వివరాలు:\n\n• **పథక మార్పు**: గతంలో అమలులో ఉన్న రైతు భరోసా పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వ అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకంగా సంస్కరించబడి అమలు చేయబడుతోంది.\n• **లక్ష్యం**: కేంద్ర పీఎం కిసాన్ రూ. 6,000 తో పాటు రాష్ట్ర టాప్-అప్ సహాయాన్ని సమన్వయం చేస్తూ రైతులకు పెట్టుబడి సాయం అందించడం దీని ఉద్దేశం.\n• **నమోదు**: రైతు సేవా కేంద్రం (RSK/RBK) లో ఈ-పంట నమోదు మరియు ఈ-కేవైసీ ద్వారా ధ్రువీకరణ జరుగుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: అధికారిక పోర్టల్: https://annadathasukhibhava.ap.gov.in మరియు హెల్ప్‌లైన్ 155251 / 1902.",
        },
    },

    "edu_thalliki_vandanam_scheme": {
        "title_en": "Thalliki Vandanam Scheme",
        "title_te": "తల్లికి వందనం పథకం",
        "portals": ["https://schooledu.ap.gov.in", "https://gsws-nbm.ap.gov.in"],
        "helplines": ["1800-425-6776", "1902"],
        "overview": {
            "en": "Thalliki Vandanam is an educational financial support framework of the Government of Andhra Pradesh, succeeding and reforming previous school assistance frameworks (such as the erstwhile Amma Vodi framework). The objective is to encourage school education, incentivize mothers and guardians, and prevent dropouts from Class I through Intermediate (Class XII).",
            "te": "తల్లికి వందనం పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వం పాఠశాల విద్యాశాఖ ద్వారా అమలు చేస్తున్న ప్రధాన విద్యా ప్రోత్సాహక పథకం. గతంలో ఉన్న అమ్మ ఒడి స్థానంలో సంస్కరించబడిన ఈ కార్యక్రమం ద్వారా పిల్లలను బడికి పంపే తల్లులకు తోడ్పాటు అందించి, డ్రాపౌట్లను అరికట్టడం మరియు 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) వరకు నాణ్యమైన విద్యాభ్యాసానికి తోడ్పడటం దీని ముఖ్య ఉద్దేశం.",
        },
        "application": {
            "en": "How to verify and apply for Thalliki Vandanam:\n\n• **Database Synchronization:** Student enrollment and attendance records are synchronized directly from the School Child Info / UDISE+ database and the Grama/Ward Sachivalayam Beneficiary Management (GSWS-NBM) portal.\n• **Secretariat Verification:** Mothers and guardians can verify eligibility, attendance, and bank account seeding status at their local Grama / Ward Sachivalayam with the Welfare and Education Assistant (WEA).\n• **Mandatory Compliance:** Maintain at least 75% student attendance and ensure the mother's bank account has active Aadhaar-NPCI seeding.\n• **Official Portals:** Check status at https://schooledu.ap.gov.in and https://gsws-nbm.ap.gov.in or call citizen helpline 1800-425-6776 / 1902.",
            "te": "తల్లికి వందనం పథకం నమోదు మరియు ధ్రువీకరణ విధానం:\n\n• **ఆటోమేటిక్ అనుసంధానం**: పాఠశాలల చైల్డ్ ఇన్ఫో (Child Info / UDISE+) డేటాబేస్ మరియు గ్రామ/వార్డు సచివాలయ నవశకం బెనిఫిషియరీ మేనేజ్‌మెంట్ (GSWS-NBM) పోర్టల్ ద్వారా వివరాలు నేరుగా సమకాలీకరించబడతాయి.\n• **సచివాలయ తనిఖీ**: తల్లులు తమ స్థానిక గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్ (WEA) వద్ద అర్హత జాబితా, విద్యార్థి హాజరు మరియు బ్యాంక్ ఖాతా సీడింగ్ స్థితిని సరిచూసుకోవచ్చు.\n• **ముఖ్య నిబంధనలు**: పాఠశాలలో కనీసం 75% హాజరు ఉండాలి మరియు తల్లి బ్యాంక్ ఖాతాకు ఆధార్-ఎన్‌పీసీఐ సీడింగ్ పూర్తయి ఉండాలి.\n• **పోర్టల్స్ & హెల్ప్‌లైన్**: అధికారిక వివరాల కొరకు https://schooledu.ap.gov.in మరియు https://gsws-nbm.ap.gov.in చూడండి లేదా 1800-425-6776 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Thalliki Vandanam Scheme:\n\n• **Student Identification:** Child Info ID / School Admission Number and Student Aadhaar Card.\n• **Mother / Guardian Aadhaar:** Aadhaar Card of the mother (or recognized legal guardian if mother is deceased).\n• **Rice Card / BPL Proof:** Valid Rice Card / White Ration Card verified in the Grama / Ward Sachivalayam database.\n• **Bank Passbook:** Active bank account passbook in the mother's name with Aadhaar seeding and active NPCI mapping for DBT.\n• **School Attendance Record:** Proof of minimum 75% attendance recorded in the official Child Info portal.",
            "te": "తల్లికి వందనం పథకానికి అవసరమైన పత్రాలు:\n\n• **విద్యార్థి వివరాలు**: విద్యార్థి పాఠశాల/కళాశాల అడ్మిషన్ రికార్డు మరియు చైల్డ్ ఇన్ఫో (Child Info) ఐడీ, ఆధార్ కార్డు.\n• **తల్లి ఆధార్ కార్డు**: తల్లి (లేదా సంరక్షకురాలి) ఆధార్ కార్డు.\n• **రేషన్ కార్డు**: కుటుంబానికి చెందిన చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు (Rice Card / BPL card).\n• **బ్యాంక్ పాస్‌బుక్**: తల్లి పేరు మీద ఉన్న బ్యాంక్ ఖాతా పాస్‌బుక్ (తప్పనిసరిగా ఆధార్ మరియు ఎన్‌పీసీఐ - NPCI తో అనుసంధానమై ఉండాలి).\n• **హాజరు రికార్డు**: విద్యా సంవత్సరంలో కనీసం 75% పాఠశాల హాజరు నమోదై ఉండాలి.",
        },
        "eligibility": {
            "en": "Eligibility criteria for Thalliki Vandanam Scheme:\n\n• **Student Education Level:** Enrolled and studying in Classes I to XII (including Intermediate 1st and 2nd year) in recognized Government, Aided, Private Unaided, or Residential Schools / Junior Colleges in Andhra Pradesh.\n• **Attendance Benchmark:** Minimum 75% school or junior college attendance recorded during the academic year.\n• **Residency & Ration Card:** Permanent residents of Andhra Pradesh holding a valid Rice Card / BPL card.\n• **Exclusions:** Regular government employees and income tax payees are excluded.\n• **Disbursement Channel:** Direct Benefit Transfer (DBT) into the mother's verified Aadhaar-NPCI bank account.",
            "te": "తల్లికి వందనం పథకం అర్హతలు:\n\n• **విద్యార్హత**: ఆంధ్రప్రదేశ్‌లోని గుర్తింపు పొందిన ప్రభుత్వ, ఎయిడెడ్, ప్రైవేట్ అన్‌ఎయిడెడ్ లేదా రెసిడెన్షియల్ పాఠశాలలు/జూనియర్ కళాశాలల్లో 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) చదువుతుండాలి.\n• **హాజరు నిబంధన**: విద్యా సంవత్సరంలో కనీసం 75% హాజరు తప్పనిసరి.\n• **రేషన్ కార్డు**: కుటుంబం చెల్లుబాటు అయ్యే రైస్ కార్డు కలిగి ఉండాలి.\n• **మినహాయింపులు**: ప్రభుత్వ ఉద్యోగులు మరియు ఆదాయపు పన్ను చెల్లించే కుటుంబాలు అనర్హులు.\n• **చెల్లింపు**: నిధులు డీబీటీ (DBT) ద్వారా తల్లి ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాకు జమ అవుతాయి.",
        },
        "benefits": {
            "en": "Financial assistance framework under Thalliki Vandanam Scheme:\n\n• **Educational Financial Support:** The scheme provides annual educational financial support for students enrolled from Class I through Intermediate (Class XII) in recognized schools and colleges in Andhra Pradesh.\n• **Operational Condition:** Specific disbursement amounts, deductions, and installment schedules are governed by official operational guidelines and administrative orders issued by the School Education Department; assistance details are subject to published notifications and should not be treated as assured payments until officially notified.\n• **Attendance Mandate:** Mandatory 75% school or college attendance during the academic year.\n• **Disbursement Channel:** Direct Benefit Transfer (DBT) into the mother's verified Aadhaar-NPCI bank account. Portals: https://schooledu.ap.gov.in and https://gsws-nbm.ap.gov.in.",
            "te": "తల్లికి వందనం పథకం ఆర్థిక సహాయ వివరాలు:\n\n• **విద్యా ప్రోత్సాహకం**: 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) వరకు చదువుతూ కనీసం 75% హాజరు నిబంధనలు పాటించే విద్యార్థుల తల్లులకు విద్యా ప్రోత్సాహక ఆర్థిక తోడ్పాటు అందుతుంది.\n• **ముఖ్య గమనిక**: చెల్లింపుల మొత్తం, విడతలు మరియు మార్గదర్శకాలు పాఠశాల విద్యాశాఖ అధికారిక ఉత్తర్వుల ద్వారా తెలియజేయబడతాయి; తుది లబ్ధిదారుల జాబితా మరియు మంజూరు వివరాలు అధికారిక ఉత్తర్వులపై ఆధారపడి ఉంటాయి.\n• **హాజరు నిబంధన**: విద్యా సంవత్సరంలో కనీసం 75% పాఠశాల హాజరు తప్పనిసరి.\n• **చెల్లింపు విధానం**: నిధులు డీబీటీ (DBT) ద్వారా తల్లి ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాకు జమ అవుతాయి. అధికారిక పోర్టల్: https://schooledu.ap.gov.in.",
        },
        "comparison": {
            "en": "Comparison between Amma Vodi and Thalliki Vandanam:\n\n• **Administrative Transition:** Amma Vodi is the predecessor school education financial support initiative in Andhra Pradesh, which has been succeeded, restructured, and reformed under the Government of Andhra Pradesh's current **Thalliki Vandanam** scheme framework.\n• **Core Purpose:** Thalliki Vandanam encourages school education, incentivizes mothers, and prevents dropouts by providing annual educational financial assistance for students enrolled from Class I through Intermediate (Class XII).\n• **Eligibility & Attendance:** The student must be studying in a recognized government, aided, or private school / junior college in Andhra Pradesh and maintain the mandatory attendance benchmark (such as 75% attendance during the academic year). The family must hold a valid Rice Card / BPL card.\n• **Disbursement Modality:** Financial assistance is deposited via Direct Benefit Transfer (DBT) directly into the Aadhaar-seeded, NPCI-active bank account of the mother.\n• **Verification & Portals:** Beneficiary verification is synchronized through the School Child Info database and the Grama / Ward Sachivalayam portal at https://schooledu.ap.gov.in and https://gsws-nbm.ap.gov.in.",
            "te": "అమ్మ ఒడి మరియు తల్లికి వందనం మధ్య తేడా మరియు పోలిక వివరాలు:\n\n• **పథక మార్పు**: గతంలో అమలులో ఉన్న అమ్మ ఒడి పాఠశాల విద్యా ప్రోత్సాహక పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వ తల్లికి వందనం పథకం మార్గదర్శకాల ప్రకారం సంస్కరించబడి అమలు చేయబడుతోంది.\n• **లక్ష్యం**: 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) వరకు చదువుతున్న విద్యార్థుల తల్లులకు విద్యా ప్రోత్సాహక ఆర్థిక తోడ్పాటు అందించి డ్రాపౌట్లను నివారించడం దీని ఉద్దేశం.\n• **అర్హత & హాజరు**: గుర్తింపు పొందిన పాఠశాల లేదా కళాశాలలో కనీసం 75% హాజరు ఉండాలి మరియు తెల్ల రేషన్ కార్డు కలిగి ఉండాలి.\n• **చెల్లింపు విధానం**: ఆర్థిక సాయం డీబీటీ (DBT) ద్వారా నేరుగా తల్లి ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాకు జమ చేయబడుతుంది.\n• **పరిశీలన పోర్టల్స్**: చైల్డ్ ఇన్ఫో మరియు గ్రామ/వార్డు సచివాలయం ద్వారా ధ్రువీకరణ జరుగుతుంది. అధికారిక పోర్టల్: https://schooledu.ap.gov.in.",
        },
    },

    "schemes_ntr_bharosa_pension": {
        "title_en": "NTR Bharosa Social Security Pension",
        "title_te": "ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛను",
        "portals": ["https://sspensions.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "NTR Bharosa is the flagship social security pension initiative of the Government of Andhra Pradesh, succeeding and reforming previous welfare pension schemes (such as YSR Pension Kanuka) to provide enhanced monthly financial protection for senior citizens, widows, disabled persons, and vulnerable livelihoods.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వం అమలు చేస్తున్న ప్రధాన సామాజిక భద్రతా పథకం. గతంలో ఉన్న వైఎస్సార్ పెన్షన్ కానుక స్థానంలో సంస్కరించబడి, వృద్ధులు, వితంతువులు, దివ్యాంగులు మరియు నిరుపేద వర్గాలకు పెంచిన నెలవారీ ఆర్థిక భరోసా కల్పించడం దీని లక్ష్యం.",
        },
        "application": {
            "en": "How to apply for NTR Bharosa Social Security Pension:\n\n• **Secretariat Application:** Submit an application form at your local Grama / Ward Sachivalayam to the Welfare and Education Assistant (WEA) or Ward Welfare Secretary.\n• **Field Verification:** Secretariat functionaries and field staff verify age, residency, socio-economic criteria, and disability certificates.\n• **Social Audit & Approval:** Verified applications are placed for social audit approval in the Grama Sabha, and sanction orders are issued.\n• **Disbursement:** Monthly pension is distributed by secretariat staff or credited via DBT under applicable departmental distribution schedules.\n• **Portal & Helpline:** Check status at https://sspensions.ap.gov.in or call citizen helpline 1902.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను దరఖాస్తు విధానం:\n\n• **సచివాలయంలో దరఖాస్తు**: మీ స్థానిక గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్ (WEA) లేదా వార్డు వెల్ఫేర్ సెక్రటరీకి దరఖాస్తు సమర్పించండి.\n• **క్షేత్ర పరిశీలన**: సచివాలయ సిబ్బంది దరఖాస్తుదారుడి వయస్సు, నివాసం, ఆదాయం మరియు సదరమ్ (SADAREM) సర్టిఫికెట్లను క్షేత్రస్థాయిలో పరిశీలిస్తారు.\n• **సామాజిక తనిఖీ & మంజూరు**: పరిశీలన అనంతరం గ్రామసభ సోషల్ ఆడిట్ ద్వారా అర్హుల జాబితా ఆమోదించబడి పింఛను మంజూరు అవుతుంది.\n• **పంపిణీ**: సచివాలయ సిబ్బంది లేదా డీబీటీ ద్వారా ప్రభుత్వ పంపిణీ నిబంధనల ప్రకారం పింఛను సొమ్ము అందుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://sspensions.ap.gov.in చూడండి లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for NTR Bharosa Pension:\n\n• **Aadhaar Card:** Aadhaar Card of the applicant for identity and age verification.\n• **Age Proof:** Voter ID card, birth certificate, or school leaving certificate (for Old Age Pension - 60+ years).\n• **Disability Certificate:** Valid SADAREM certificate showing disability percentage (for Differently Abled pensions).\n• **Death Certificate of Husband:** In case of Widow Pension.\n• **Rice Card / BPL Proof:** Valid white ration card in Andhra Pradesh.\n• **Bank Passbook:** Active bank account passbook mapped with NPCI.",
            "te": "ఎన్టీఆర్ భరోసా పింఛనుకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: దరఖాస్తుదారు ఆధార్ కార్డు.\n• **వయస్సు ధ్రువీకరణ**: ఓటరు గుర్తింపు కార్డు లేదా పుట్టిన తేదీ ధ్రువీకరణ పత్రం (వృద్ధాప్య పింఛనుకు కనీసం 60 ఏళ్లు నిండి ఉండాలి).\n• **సదరమ్ (SADAREM) సర్టిఫికెట్**: దివ్యాంగుల పింఛను కొరకు వైకల్య శాతం ధ్రువీకరణ పత్రం.\n• **భర్త మరణ ధ్రువీకరణ పత్రం**: వితంతు పింఛను దరఖాస్తుదారులకు.\n• **రేషన్ కార్డు**: చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు (Rice Card).\n• **బ్యాంక్ పాస్‌బుక్**: ఆధార్ అనుసంధానమైన బ్యాంక్ ఖాతా పాస్‌బుక్.",
        },
        "eligibility": {
            "en": "Eligibility criteria for NTR Bharosa Pension:\n\n• **Residency:** Permanent resident of Andhra Pradesh holding a valid Rice Card / BPL card.\n• **Income Limit:** Total monthly family income within notified BPL parameters (rural below Rs. 10,000, urban below Rs. 12,000).\n• **Land Limits:** Within notified landholding limits (3 acres wetland or 10 acres dryland).\n• **Exclusions:** Ownership of four-wheelers (commercial livelihood vehicles exempted); regular government employees and existing government pensioners are excluded.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను అర్హతలు:\n\n• **నివాసం & రేషన్ కార్డు**: ఆంధ్రప్రదేశ్ శాశ్వత నివాసి అయి ఉండాలి; చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు / రైస్ కార్డు కలిగి ఉండాలి.\n• **ఆదాయ పరిమితి**: కుటుంబ నెలవారీ ఆదాయం గ్రామీణ ప్రాంతాల్లో రూ. 10,000, పట్టణాల్లో రూ. 12,000 లోపు ఉండాలి.\n• **భూమి పరిమితి**: వ్యవసాయ భూమి 3 ఎకరాల మాగాణి లేదా 10 ఎకరాల మెట్ట లోపు ఉండాలి.\n• **మినహాయింపులు**: నాలుగు చక్రాల వాహనం ఉన్నవారు (ఆటో వంటి జీవనోపాధి వాహనాలు మినహా), ప్రభుత్వ ఉద్యోగులు మరియు ఇతర పెన్షన్లు పొందుతున్న వారు అనర్హులు.",
        },
        "benefits": {
            "en": "Pension categories and monthly payout guidelines under NTR Bharosa:\n\n• **Old Age Pension (OAP 60+ yrs):** Benchmarked at Rs. 4,000 per month for eligible senior citizens under state guidelines.\n• **Other Welfare Categories:** Monthly pension amounts for widows, differently abled persons, occupational categories, and chronic illness patients are governed by applicable departmental notifications and government orders.\n• **Disbursement:** Disbursed through Grama / Ward Sachivalayam channels or DBT as per departmental distribution schedules.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను కేటగిరీలు మరియు చెల్లింపుల మార్గదర్శకాలు:\n\n• **వృద్ధాప్య పింఛను (OAP - 60 ఏళ్లు పైబడిన వారు)**: అర్హులైన వృద్ధులకు ప్రభుత్వ మార్గదర్శకాల ప్రకారం నెలకు రూ. 4,000 ప్రామాణికంగా అందుతుంది.\n• **ఇతర సంక్షేమ కేటగిరీలు**: వితంతువులు, దివ్యాంగులు, వృత్తి కార్మికులు మరియు దీర్ఘకాలిక వ్యాధిగ్రస్తులకు చెల్లించే పింఛను మొత్తాలు సంబంధిత శాఖ అధికారిక ఉత్తర్వులకు లోబడి ఉంటాయి.\n• **పంపిణీ**: సచివాలయ వ్యవస్థ లేదా డీబీటీ ద్వారా శాఖాపరమైన పంపిణీ షెడ్యూల్ ప్రకారం అందించబడుతుంది.",
        },
        "comparison": {
            "en": "Comparison between YSR Pension Kanuka and NTR Bharosa:\n\n• **Administrative Transition:** YSR Pension Kanuka is the predecessor social security pension scheme in Andhra Pradesh, which has been succeeded, restructured, and renamed as **NTR Bharosa Social Security Pension** under the Government of Andhra Pradesh.\n• **Key Enhancements:** Under NTR Bharosa, the Old Age Pension (OAP 60+ yrs) benchmark has been revised to Rs. 4,000 per month; assistance for other categories is governed by updated departmental government orders.\n• **Delivery Channel:** Distribution via Grama / Ward Sachivalayam channels and DBT. Official portal: https://sspensions.ap.gov.in.",
            "te": "వైఎస్సార్ పెన్షన్ కానుక మరియు ఎన్టీఆర్ భరోసా మధ్య తేడా మరియు పోలిక వివరాలు:\n\n• **పథక మార్పు**: గతంలో ఉన్న వైఎస్సార్ పెన్షన్ కానుక పథకం స్థానంలో ఆంధ్రప్రదేశ్ ప్రభుత్వం ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛను పథకాన్ని అమలు చేస్తోంది.\n• **సవరించిన పింఛను**: ఎన్టీఆర్ భరోసా కింద వృద్ధాప్య పింఛను ప్రామాణిక మొత్తం నెలకు రూ. 4,000 గా సవరించబడింది; ఇతర కేటగిరీల సహాయం తాజా ప్రభుత్వ ఉత్తర్వుల ప్రకారం అమలు చేయబడుతుంది.\n• **పంపిణీ**: సచివాలయ వ్యవస్థ మరియు డీబీటీ ద్వారా పంపిణీ జరుగుతుంది. అధికారిక పోర్టల్: https://sspensions.ap.gov.in.",
        },
    },

    "health_dr_ntr_vaidya_seva_aarogyasri": {
        "title_en": "Dr. NTR Vaidya Seva",
        "title_te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (ఆరోగ్యశ్రీ)",
        "portals": ["https://drntrvaidyaseva.ap.gov.in"],
        "helplines": ["104", "108", "1902"],
        "overview": {
            "en": "Dr. NTR Vaidya Seva (formerly functioning as Dr. YSR Aarogyasri) is the flagship healthcare scheme of the Government of Andhra Pradesh providing cashless medical and surgical treatment for listed secondary and tertiary illnesses to eligible low- and middle-income families at empaneled network hospitals.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీ) ఆంధ్రప్రదేశ్ ప్రభుత్వం అమలు చేస్తున్న ప్రధాన ఆరోగ్య పథకం. అర్హులైన నిరుపేద కుటుంబాలకు నెట్‌వర్క్ ఆసుపత్రులలో ఉచిత నగదు రహిత వైద్యం, శస్త్రచికిత్సలు మరియు చికిత్సానంతర సాయం అందించడం దీని ముఖ్య లక్ష్యం.",
        },
        "application": {
            "en": "How to access cashless healthcare under Dr. NTR Vaidya Seva:\n\n• **Hospital Helpdesk:** Visit any empaneled government or private network hospital in Andhra Pradesh. Approach the Aarogyamithra at the Dr. NTR Vaidya Seva helpdesk.\n• **Digital Pre-Authorization:** Present your Aadhaar Card and Rice Card. The Aarogyamithra coordinates clinical evaluation and online pre-authorization with the Trust.\n• **Cashless Treatment:** Once approved, medical treatment, surgery, ICU, medicines, and food are provided completely cashless.\n• **Emergency Safeguard:** In acute life-threatening medical emergencies, dial 108 immediately; hospital casualty departments stabilize patients and initiate emergency pre-authorization without delaying care.\n• **Post-Discharge:** Recovery allowance (Aarogya Asara) is provided during the recuperation period.\n• **Portal & Helpline:** Visit https://drntrvaidyaseva.ap.gov.in or dial 104 / 108 / 1902.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద ఉచిత చికిత్స పొందే విధానం:\n\n• **ఆసుపత్రిలో సంప్రదింపు**: ఏపీలోని నెట్‌వర్క్ ఆసుపత్రిలోని డాక్టర్ ఎన్టీఆర్ వైద్య సేవ హెల్ప్‌డెస్క్‌ వద్ద ఉన్న ఆరోగ్యమిత్రను సంప్రదించండి.\n• **గుర్తింపు కార్డులు సమర్పణ**: మీ ఆధార్ కార్డు మరియు రైస్ కార్డును ఆరోగ్యమిత్రకు చూపించండి. ఆసుపత్రి వైద్యుల సిఫార్సుతో ట్రస్ట్ నుండి ఆన్‌లైన్ ముందస్తు అనుమతి (Pre-authorization) తీసుకుంటారు.\n• **ఉచిత నగదు రహిత వైద్యం**: అనుమతి రాగానే చికిత్స, ఆపరేషన్, మందులు మరియు భోజనం పూర్తిగా ఉచితంగా అందించబడతాయి.\n• **అత్యవసర రక్షణ**: ప్రాణాపాయ అత్యవసర సమయాల్లో వెంటనే 108 కు కాల్ చేయండి; కార్డుల కోసం వెతకడానికి అత్యవసర చికిత్సను నిలిపివేయరాదు.\n• **ఆరోగ్య ఆసరా**: శస్త్రచికిత్స అనంతరం విశ్రాంతి సమయంలో కోలుకోవడానికి ఆరోగ్య ఆసరా ఆర్థిక సాయం అందుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://drntrvaidyaseva.ap.gov.in చూడండి లేదా 104 / 108 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Dr. NTR Vaidya Seva:\n\n• **Identity Proof:** Aadhaar Card of the patient and family members.\n• **Eligibility Proof:** BPL White Ration Card / Rice Card or Dr. NTR Vaidya Seva / Aarogyasri Health Card.\n• **Medical Documentation:** Doctor consultation prescription and diagnostic investigation reports (for planned admissions). In acute emergencies, treatment is initiated immediately without documentation delay.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: రోగి మరియు కుటుంబ సభ్యుల ఆధార్ కార్డు.\n• **రేషన్ కార్డు / హెల్త్ కార్డు**: ఆంధ్రప్రదేశ్ ప్రభుత్వం జారీ చేసిన రైస్ కార్డు (Rice Card) లేదా ఎన్టీఆర్ వైద్య సేవ హెల్త్ కార్డు.\n• **వైద్య నివేదికలు**: రోగ నిర్ధారణ రిపోర్టులు మరియు డాక్టర్ సిఫార్సు (ప్లాన్ చేసిన చికిత్సలకు). ప్రాణాపాయ అత్యవసర పరిస్థితుల్లో పత్రాల కోసం ఆలస్యం చేయరాదు.",
        },
        "eligibility": {
            "en": "Eligibility for Dr. NTR Vaidya Seva:\n\n• Permanent resident families of Andhra Pradesh holding a valid Rice Card / White Ration Card or Dr. NTR Vaidya Seva Health Card.\n• Families with verified annual income within state eligibility ceilings (benchmarked up to Rs. 5,00,000 per annum).\n• Covers listed secondary and tertiary inpatient procedures across empaneled network hospitals.\n• Regular government employees covered under the Employees Health Scheme (EHS) are excluded.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ అర్హత నిబంధనలు:\n\n• ఆంధ్రప్రదేశ్ శాశ్వత నివాసి అయి ఉండాలి; తెల్ల రేషన్ కార్డు / రైస్ కార్డు లేదా ఆరోగ్యశ్రీ హెల్త్ కార్డు ఉండాలి.\n• కార్డు లేని వారికి వార్షిక కుటుంబ ఆదాయం నిర్ణీత పరిమితికి (రూ. 5 లక్షల లోపు) లోబడి ఉండాలి.\n• ప్రభుత్వం నోటిఫై చేసిన ప్రొసీజర్ మాస్టర్ పరిధిలోని ద్వితీయ, తృతీయ స్థాయి రోగాలకు ఉచిత చికిత్స వర్తిస్తుంది.\n• ప్రభుత్వ ఉద్యోగుల ఆరోగ్య పథకం (EHS) కింద ఉన్న వారు మినహాయింపు.",
        },
        "benefits": {
            "en": "Coverage scope and benefits under Dr. NTR Vaidya Seva:\n\n• **Cashless Hospitalization:** Cashless medical and surgical care up to Rs. 25,00,000 per family per year for listed secondary and tertiary procedures in empaneled network hospitals as governed by Trust guidelines and package tariffs.\n• **Pre-Authorization Requirement:** Planned admissions require digital pre-authorization approved by the Trust via the Aarogyamithra help desk.\n• **Emergency Safeguard:** In life-threatening emergencies, network hospitals provide immediate emergency stabilization; pre-authorization protocols are initiated without delaying urgent medical care. Dial 108 immediately.\n• **Portability Boundary:** Treatment outside Andhra Pradesh is strictly restricted to participating empaneled network hospitals outside the state as designated by the Trust for approved super-specialty procedures.\n• **Post-Discharge Support:** Free follow-up medicines and post-operative sustenance allowance (Aarogya Asara) credited via DBT.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ ప్రయోజనాలు మరియు కవరేజ్:\n\n• **నగదు రహిత చికిత్స**: నెట్‌వర్క్ ఆసుపత్రులలో నోటిఫై చేసిన వ్యాధులకు ఏడాదికి కుటుంబానికి రూ. 25,00,000 వరకు ప్యాకేజీ టారిఫ్‌ల ప్రకారం ఉచిత నగదు రహిత చికిత్స లభిస్తుంది.\n• **ముందస్తు అనుమతి**: ప్లాన్ చేసిన అడ్మిషన్లకు ఆసుపత్రిలోని ఆరోగ్యమిత్ర ద్వారా ట్రస్ట్ ప్రీ-ఆథరైజేషన్ తప్పనిసరి.\n• **అత్యవసర చికిత్స రక్షణ**: ప్రాణాపాయ అత్యవసర పరిస్థితుల్లో తక్షణ ప్రాథమిక చికిత్స అందించబడుతుంది; వెంటనే 108 కు కాల్ చేయాలి.\n• **రాష్ట్రం వెలుపల సేవలు**: ట్రస్ట్ నిర్దేశించిన ఇతర రాష్ట్రాల ఎంపానెల్ నెట్‌వర్క్ ఆసుపత్రులలో మాత్రమే ప్రత్యేక శస్త్రచికిత్సలకు వర్తిస్తుంది.\n• **ఆరోగ్య ఆసరా**: చికిత్సానంతరం విశ్రాంతి సమయంలో కోలుకోవడానికి ఆర్థిక సాయం డీబీటీ ద్వారా అందుతుంది.",
        },
        "comparison": {
            "en": "Comparison between Aarogyasri and Dr. NTR Vaidya Seva:\n\n• **Administrative Transition:** Dr. YSR Aarogyasri is the predecessor healthcare scheme, which operates as **Dr. NTR Vaidya Seva** under the Government of Andhra Pradesh.\n• **Core Entitlement:** Retains cashless hospitalization for listed secondary and tertiary treatments at empaneled network hospitals with coverage ceiling up to Rs. 25 lakh per family per year for eligible cardholders.\n• **Portals & Emergency:** Managed via https://drntrvaidyaseva.ap.gov.in. Emergency helpline: 108, medical helpline: 104.",
            "te": "ఆరోగ్యశ్రీ మరియు డాక్టర్ ఎన్టీఆర్ వైద్య సేవ మధ్య తేడా మరియు పోలిక వివరాలు:\n\n• **పథక మార్పు**: గతంలో డాక్టర్ వైఎస్సార్ ఆరోగ్యశ్రీగా ఉన్న పథకం ప్రస్తుతం డాక్టర్ ఎన్టీఆర్ వైద్య సేవగా అమలు చేయబడుతోంది.\n• **ప్రధాన సేవలు**: అర్హులైన కుటుంబాలకు నెట్‌వర్క్ ఆసుపత్రులలో రూ. 25 లక్షల వరకు నగదు రహిత ద్వితీయ, తృతీయ స్థాయి చికిత్సలు యథాతథంగా కొనసాగుతున్నాయి.\n• **పోర్టల్ & హెల్ప్‌లైన్లు**: అధికారిక పోర్టల్: https://drntrvaidyaseva.ap.gov.in, అత్యవసర అంబులెన్స్: 108, వైద్య సమాచారం: 104.",
        },
    },

    "schemes_grama_ward_sachivalayam": {
        "title_en": "Grama / Ward Sachivalayam",
        "title_te": "గ్రామ/వార్డు సచివాలయం",
        "portals": ["https://gramawardsachivalayam.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "Grama and Ward Sachivalayams provide decentralized, transparent, citizen-centric doorstep governance across Andhra Pradesh, functioning as an integrated single-window service delivery framework for over 500 government services and welfare schemes.",
            "te": "గ్రామ మరియు వార్డు సచివాలయాలు ఆంధ్రప్రదేశ్‌లోని గ్రామీణ మరియు పట్టణ ప్రాంతాల్లో ప్రజల ముంగిటకే పారదర్శక పరిపాలన అందించే వికేంద్రీకృత వ్యవస్థ. 500కు పైగా ప్రభుత్వ పౌర సేవలు మరియు సంక్షేమ పథకాలకు ఇవి ఏకగవాక్ష కేంద్రాలుగా పనిచేస్తున్నాయి.",
        },
        "application": {
            "en": "How to avail services and track status at Grama / Ward Sachivalayam:\n\n• **Visit Secretariat:** Visit your local village or ward secretariat and meet the Digital Assistant, VRO, or Welfare and Education Assistant (WEA).\n• **Submit Application:** Submit required documents with biometric authentication for citizen services or scheme enrollments.\n• **Service Request Number:** Receive a digital acknowledgment slip containing a unique Service Request Number (SRN) for tracking.\n• **Citizens' Charter SLAs:** Routine certificates and services are processed within defined Citizen's Charter timelines.\n• **Track Status:** Track application progress on https://gramawardsachivalayam.ap.gov.in or dial Spandana helpline 1902.",
            "te": "గ్రామ/వార్డు సచివాలయంలో సేవలు పొందే విధానం:\n\n• **సచివాలయం సందర్శన**: మీ స్థానిక గ్రామ లేదా వార్డు సచివాలయాన్ని సందర్శించి డిజిటల్ అసిస్టెంట్, వీఆర్వో లేదా వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్‌ను కలవండి.\n• **దరఖాస్తు సమర్పణ**: అవసరమైన ధ్రువపత్రాలు మరియు బయోమెట్రిక్ ధ్రువీకరణతో సేవలకు దరఖాస్తు చేసుకోండి.\n• **రసీదు (SRN)**: దరఖాస్తు సమర్పించిన వెంటనే సర్వీస్ రిక్వెస్ట్ నంబర్ (SRN) కలిగిన డిజిటల్ రసీదు లభిస్తుంది.\n• **ఎస్ఎల్ఏ కాలపరిమితి**: సిటిజన్ చార్టర్ సర్వీస్ లెవల్ అగ్రిమెంట్ ప్రకారం నిర్ణీత గడువులో సేవలు అందుతాయి.\n• **స్టేటస్ పరిశీలన**: దరఖాస్తు నంబర్ ద్వారా అధికారిక పోర్టల్ https://gramawardsachivalayam.ap.gov.in లో పురోగతిని తెలుసుకోవచ్చు లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents at Grama / Ward Sachivalayam:\n\n• **Identity Proof:** Aadhaar Card of the applicant.\n• **Ration Proof:** Rice Card / White Ration Card.\n• **Active Mobile Number:** For OTP verification and SMS progress tracking.\n• **Service-Specific Proofs:** Land title deeds / Pattadar passbook (revenue), hospital birth/death reports, electricity bills, etc.",
            "te": "గ్రామ/వార్డు సచివాలయ సేవలకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: దరఖాస్తుదారు ఆధార్ కార్డు.\n• **రేషన్ కార్డు**: తెల్ల రేషన్ కార్డు / రైస్ కార్డు.\n• **మొబైల్ నంబర్**: ఓటీపీ ధ్రువీకరణ మరియు ఎస్ఎంఎస్ ట్రాకింగ్ కొరకు.\n• **సేవకు సంబంధించిన పత్రాలు**: భూమి రికార్డులు (రెవెన్యూ కొరకు), ఆసుపత్రి జనన/మరణ నివేదికలు, కరెంట్ బిల్లు మొదలైనవి.",
        },
        "eligibility": {
            "en": "Eligibility for Grama / Ward Sachivalayam services:\n\n• All resident citizens of Andhra Pradesh residing within the jurisdiction of the designated Grama (rural) or Ward (urban) Sachivalayam.",
            "te": "సచివాలయ సేవల అర్హత:\n\n• సంబంధిత గ్రామ సచివాలయం (గ్రామీణ) లేదా వార్డు సచివాలయం (పట్టణ) పరిధిలో నివసించే ఆంధ్రప్రదేశ్ పౌరులందరూ ఈ సేవలు పొందవచ్చు.",
        },
        "benefits": {
            "en": "Benefits provided through Grama / Ward Sachivalayam:\n\n• Over 500 government services delivered across Revenue, Civil Supplies, Welfare, Panchayat, and Municipal domains.\n• Access to integrated caste, income, and residence certificates within statutory SLA windows.\n• Direct enrollment for welfare schemes (NTR Bharosa, Annadata Sukhibhava, Thalliki Vandanam, MGNREGS, Housing).\n• Transparent tracking via unique SRN numbers and SMS updates without middlemen.",
            "te": "గ్రామ/వార్డు సచివాలయ సేవల ప్రయోజనాలు:\n\n• రెవెన్యూ, పౌర సరఫరాలు, సంక్షేమం మరియు పంచాయతీ శాఖలకు సంబంధించి 500కు పైగా సేవలు ప్రజల ముంగిటకే అందుతాయి.\n• కుల, ఆదాయ, నివాస ధ్రువపత్రాలు నిర్ణీత ఎస్ఎల్ఏ (SLA) కాలపరిమితిలో లభిస్తాయి.\n• సంక్షేమ పథకాల నమోదు (ఎన్టీఆర్ భరోసా, అన్నదాత సుఖీభవ, తల్లికి వందనం, ఉపాధి హామీ, ఇళ్ల పథకం) సచివాలయం ద్వారానే జరుగుతుంది.\n• దళారుల ప్రమేయం లేకుండా ఎస్ఆర్ఎన్ (SRN) నంబర్ ద్వారా పారదర్శక ట్రాకింగ్ లభిస్తుంది.",
        },
    },

    "schemes_mgnregs_andhra_pradesh": {
        "title_en": "MGNREGS Andhra Pradesh",
        "title_te": "ఉపాధి హామీ పథకం (MGNREGS)",
        "portals": ["https://nrega.ap.gov.in", "https://nrega.nic.in"],
        "helplines": ["1800-425-2123", "1902"],
        "overview": {
            "en": "The Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS) is designed to provide rural livelihood security by offering wage employment to adult members of rural households volunteering for unskilled manual labor under notified Ministry of Rural Development (MoRD) guidelines.",
            "te": "మహాత్మా గాంధీ జాతీయ గ్రామీణ ఉపాధి హామీ పథకం (MGNREGS) గ్రామీణ ప్రాంతాల్లోని కుటుంబాలకు నైపుణ్యం లేని శారీరక శ్రమతో కూడిన ఉపాధిని కల్పించి జీవనోపాధి భద్రత చేకూర్చేందుకు కేంద్ర గ్రామీణాభివృద్ధి మంత్రిత్వ శాఖ (MoRD) మార్గదర్శకాల ప్రకారం అమలు చేయబడుతోంది.",
        },
        "application": {
            "en": "How to apply for MGNREGS Job Card and demand work:\n\n• **Job Card Application:** Rural adults approach the Panchayat Secretary, Field Assistant (FA), or Engineering Assistant at their local Grama Sachivalayam.\n• **Documents Needed:** Aadhaar cards of adult family members, Rice Card / ration card, and bank/post office account passbook. Job Card is issued within 15 days.\n• **Demand Work (Form 6):** Submit a work demand application at the Grama Sachivalayam; statutory work allocation is guaranteed within 15 days within 5 km of the village.\n• **Direct Wage Payment:** Wages are credited directly via DBT into Aadhaar-seeded accounts via e-FMS.\n• **Portals & Helpline:** Check records at https://nrega.ap.gov.in or call Ombudsman helpline 1800-425-2123 / Spandana 1902.",
            "te": "ఉపాధి హామీ జాబ్ కార్డు దరఖాస్తు మరియు పని పొందే విధానం:\n\n• **జాబ్ కార్డు దరఖాస్తు**: స్థానిక గ్రామ సచివాలయంలోని పంచాయతీ కార్యదర్శి లేదా ఫీల్డ్ అసిస్టెంట్‌ను (FA) సంప్రదించి జాబ్ కార్డు కోసం దరఖాస్తు చేసుకోండి. 15 రోజుల్లో జాబ్ కార్డు జారీ చేస్తారు.\n• **అవసరమైన పత్రాలు**: కుటుంబ వయోజనుల ఆధార్ కార్డులు, రేషన్ కార్డు మరియు బ్యాంక్/పోస్టాఫీస్ పాస్‌బుక్.\n• **పని డిమాండ్ (ఫారం-6)**: గ్రామ సచివాలయంలో పని కోసం ఫారం-6 దరఖాస్తు సమర్పించి రసీదు పొందండి; 15 రోజుల్లోగా గ్రామానికి 5 కి.మీ పరిధిలో పని కల్పిస్తారు.\n• **వేతన చెల్లింపు**: వేతనాలు నేరుగా డీబీటీ (DBT) ద్వారా ఆధార్-సీడెడ్ బ్యాంక్ ఖాతాకు జమ అవుతాయి.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://nrega.ap.gov.in చూడండి లేదా 1800-425-2123 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for MGNREGS Job Card:\n\n• **Aadhaar Cards:** Aadhaar Cards of all adult family members willing to do manual labor.\n• **Residency Proof:** BPL White Ration Card / Rice Card.\n• **Bank / Post Office Passbook:** Active Aadhaar-seeded, NPCI-linked savings account passbook for DBT wage crediting.\n• **Photographs:** Passport-size photographs of adult family members.",
            "te": "ఉపాధి హామీ జాబ్ కార్డుకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డులు**: పని చేయగోరే కుటుంబ వయోజనులందరి ఆధార్ కార్డులు.\n• **నివాస ధ్రువీకరణ**: తెల్ల రేషన్ కార్డు / రైస్ కార్డు.\n• **బ్యాంక్ / పోస్టాఫీస్ పాస్‌బుక్**: వేతనాలు జమయ్యేందుకు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ లేదా పోస్టాఫీస్ ఖాతా పాస్‌బుక్.\n• **ఫోటోలు**: జాబ్ కార్డు కొరకు దరఖాస్తుదారుల పాస్‌పోర్ట్ సైజు ఫోటోలు.",
        },
        "eligibility": {
            "en": "Eligibility for MGNREGS:\n\n• Adult members (18+ years) residing in rural areas of Andhra Pradesh willing to do unskilled manual work.\n• Must reside within the Gram Panchayat area.",
            "te": "ఉపాధి హామీ అర్హత నిబంధనలు:\n\n• గ్రామీణ ప్రాంతంలో నివసిస్తూ, 18 ఏళ్లు నిండిన వయోజనులై ఉండాలి.\n• నైపుణ్యం లేని శారీరక శ్రమ చేయడానికి సిద్ధంగా ఉన్న గ్రామీణ కుటుంబాలు అర్హులు.",
        },
        "benefits": {
            "en": "Entitlements and benefits under MGNREGS:\n\n• **Wage Employment Allocation:** Rural households volunteering for unskilled manual work receive work allocation under notified state and central operational guidelines.\n• **Statutory Wage Rates:** Daily wage rates are officially notified and periodically revised by the Ministry of Rural Development (MoRD); verify current notified rates via panchayat or official portal.\n• **Direct Wage Transfer:** Wages credited directly into bank or post office accounts via DBT without intermediary deductions.\n• **Worksite Amenities:** Provision of safe drinking water, shade for resting, and first-aid kits at active worksites.",
            "te": "ఉపాధి హామీ హక్కులు మరియు ప్రయోజనాలు:\n\n• **ఉపాధి కల్పన**: నైపుణ్యం లేని శారీరక శ్రమ చేయడానికి సిద్ధంగా ఉన్న గ్రామీణ కుటుంబాలకు ప్రభుత్వ మార్గదర్శకాల ప్రకారం పనులు కేటాయించబడతాయి.\n• **నోటిఫై చేసిన వేతనాలు**: రోజువారీ వేతనాలు కేంద్ర గ్రామీణాభివృద్ధి శాఖ (MoRD) ద్వారా నోటిఫై చేయబడతాయి (తాజా వేతన వివరాలను సచివాలయంలో తెలుసుకోవచ్చు).\n• **నేరుగా వేతన జమ**: వేతనాలు ఎటువంటి తగ్గింపులు లేకుండా నేరుగా బ్యాంక్ లేదా పోస్టాఫీసు ఖాతాలో డీబీటీ ద్వారా జమవుతాయి.\n• **పని ప్రదేశ సౌకర్యాలు**: తాగునీరు, విశ్రాంతి నీడ మరియు ప్రథమ చికిత్స సౌకర్యాలు పని ప్రదేశంలో కల్పించబడతాయి.",
        },
    },

    "schemes_pedalandariki_illu_housing": {
        "title_en": "Pedalandariki Illu Housing Scheme",
        "title_te": "పేదలందరికీ ఇళ్లు గృహ నిర్మాణ పథకం",
        "portals": ["https://housing.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "Pedalandariki Illu is the flagship affordable housing initiative in Andhra Pradesh implemented by APSHCL in convergence with PMAY, providing free house site pattas registered in the name of female heads of households and structured financial assistance for pucca house construction.",
            "te": "పేదలందరికీ ఇళ్లు పథకం ఆంధ్రప్రదేశ్ హౌసింగ్ కార్పొరేషన్ (APSHCL) ద్వారా కేంద్ర పీఎం ఆవాస్ యోజన (PMAY) సమన్వయంతో పేద మహిళల పేరిట ఉచిత ఇళ్ల పట్టాలు మరియు పక్కా ఇళ్ల నిర్మాణానికి ఆర్థిక సహాయాన్ని అందించే పథకం.",
        },
        "application": {
            "en": "How to apply for Pedalandariki Illu Housing:\n\n• **Secretariat Application:** Apply at your local Grama / Ward Sachivalayam through the Engineering Assistant (EA) and Welfare & Education Assistant (WEA).\n• **Verification:** Field verification validates homelessness, landlessness, and BPL status.\n• **Geo-Tagging & Staged Subsidy:** Financial subsidies are released across 4 physical construction milestones (basement level, lintel level, roof cast, and completion) following mandatory physical geo-tagging inspection by the Engineering Assistant.\n• **Portals & Helpline:** Check status at https://housing.ap.gov.in or call Spandana at 1902.",
            "te": "పేదలందరికీ ఇళ్లు పథకం దరఖాస్తు విధానం:\n\n• **సచివాలయంలో దరఖాస్తు**: మీ స్థానిక గ్రామ/వార్డు సచివాలయంలోని ఇంజనీరింగ్ అసిస్టెంట్ మరియు వెల్ఫేర్ అసిస్టెంట్‌కు దరఖాస్తు చేసుకోండి.\n• **క్షేత్ర పరిశీలన**: రెవెన్యూ మరియు ఇంజనీరింగ్ సిబ్బంది నివాస అర్హతలు, నిరుపేద స్థితిని పరిశీలిస్తారు.\n• **జియో-ట్యాగింగ్ & నిధుల విడుదల**: భౌతిక నిర్మాణ పురోగతి మైలురాళ్ల ఆధారంగా (బేస్‌మెంట్, లింటెల్ లెవల్, స్లాబ్, మరియు పూర్తి కావడం) ఇంజనీరింగ్ అసిస్టెంట్ జియో-ట్యాగింగ్ ఫోటోల ధ్రువీకరణ తర్వాత నేరుగా బ్యాంక్ ఖాతాకు నిధులు అందుతాయి.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://housing.ap.gov.in చూడండి లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Pedalandariki Illu Housing:\n\n• **Aadhaar Cards:** Aadhaar Card of the applicant (female head of family) and spouse.\n• **Ration Proof:** Valid BPL White Ration Card / Rice Card.\n• **House Site Document:** House Site Allotment Patta copy.\n• **Bank Passbook:** Active Aadhaar-seeded, NPCI-linked bank account passbook for DBT subsidy.\n• **Self-Declaration:** Non-possession of pucca house self-declaration affidavit and family photographs.",
            "te": "పేదలందరికీ ఇళ్లు పథకానికి అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డులు**: దరఖాస్తుదారు (మహిళా యజమాని) మరియు భర్త ఆధార్ కార్డులు.\n• **రేషన్ కార్డు**: తెల్ల రేషన్ కార్డు / రైస్ కార్డు.\n• **ఇంటి పట్టా**: ప్రభుత్వం జారీ చేసిన ఇంటి స్థలం పట్టా పత్రం.\n• **బ్యాంక్ పాస్‌బుక్**: సబ్సిడీ జమ కొరకు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ పాస్‌బుక్.\n• **డిక్లరేషన్**: సొంత పక్కా ఇల్లు లేదని సెల్ఫ్ డిక్లరేషన్ పత్రం మరియు కుటుంబ ఫోటోలు.",
        },
        "eligibility": {
            "en": "Eligibility criteria for Pedalandariki Illu Housing:\n\n• Permanent resident of Andhra Pradesh holding a valid Rice Card / White Ration Card.\n• Must not own a pucca residential house or house site anywhere in India.\n• Total household income within notified BPL/EWS economic ceilings.\n• Exclusions: Families where an adult member is a regular government employee or owns a four-wheeler (commercial livelihood vehicles like autos exempted).",
            "te": "పేదలందరికీ ఇళ్లు అర్హతలు:\n\n• ఆంధ్రప్రదేశ్ శాశ్వత నివాసి అయి ఉండాలి; తెల్ల రేషన్ కార్డు / రైస్ కార్డు కలిగి ఉండాలి.\n• భారతదేశంలో ఎక్కడా సొంత పక్కా ఇల్లు లేదా ఇంటి స్థలం ఉండరాదు.\n• కుటుంబ ఆదాయం నిర్ణీత బీపీఎల్/ఈడబ్ల్యూఎస్ పరిమితి లోపు ఉండాలి.\n• మినహాయింపులు: కుటుంబంలో ప్రభుత్వ ఉద్యోగులు ఉండరాదు మరియు నాలుగు చక్రాల వాహనం (ఆటో వంటి జీవనోపాధి వాహనాలు మినహా) ఉండరాదు.",
        },
        "benefits": {
            "en": "Benefits provided under Pedalandariki Illu Housing:\n\n• **House Site Allotment:** Free house site patta registered in the name of the female head of the household (benchmarked around 1.5 cents in rural areas and 1 cent in urban areas where land is available).\n• **Construction Subsidy:** Staged financial construction assistance released across 4 physical milestones (basement level, lintel level, roof cast, and completion) following mandatory geo-tagging.\n• **Layout Infrastructure:** Basic infrastructure support including road access, water supply, and electricity in designated government layouts.\n• **Disbursement Mode:** Direct Benefit Transfer (DBT) directly into the beneficiary's Aadhaar-seeded account.",
            "te": "పేదలందరికీ ఇళ్లు పథకం ప్రయోజనాలు:\n\n• **ఇంటి స్థలం కేటాయింపు**: అర్హులైన మహిళా యజమాని పేరిట ఉచిత ఇంటి పట్టా కేటాయింపు (గ్రామీణ ప్రాంతాల్లో దాదాపు 1.5 సెంట్లు, పట్టణాల్లో 1 సెంటు వరకు స్థానిక నిబంధనల ప్రకారం).\n• **నిర్మాణ ఆర్థిక సాయం**: నాలుగు దశల్లో భౌతిక నిర్మాణ మైలురాళ్ల ఆధారంగా (బేస్‌మెంట్, లింటెల్, స్లాబ్, మరియు పూర్తి కావడం) మొబైల్ జియో-ట్యాగింగ్ ధ్రువీకరణ తర్వాత నిధులు విడుదలవుతాయి.\n• **మౌలిక వసతులు**: లేఅవుట్లలో రోడ్లు, తాగునీరు మరియు విద్యుత్ సౌకర్యాలు కల్పించడం.\n• **చెల్లింపు విధానం**: సాయం నేరుగా డీబీటీ (DBT) ద్వారా లబ్ధిదారురాలి బ్యాంక్ ఖాతాకు జమ అవుతుంది.",
        },
    },

    "edu_vidya_deevena_vasathi_deevena": {
        "title_en": "Vidya Deevena & Vasathi Deevena",
        "title_te": "విద్యా దీవెన మరియు వసతి దీవెన",
        "portals": ["https://jnanabhumi.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "The Government of Andhra Pradesh operates comprehensive post-matric financial support schemes through the dedicated JnanaBhumi portal. These programs encompass Reimbursement of Tuition Fee (RTF, also known as Vidya Deevena) and Maintenance Fee (MTF, also known as Vasathi Deevena) for higher education.",
            "te": "ఆంధ్రప్రదేశ్ ప్రభుత్వం పేద విద్యార్థులు ఉన్నత విద్య, డిగ్రీ, పాలిటెక్నిక్, ఇంజనీరింగ్, మెడిసిన్ వంటి కోర్సులు అభ్యసించేందుకు జ్ఞానభూమి (JnanaBhumi) పోర్టల్ ద్వారా ట్యూషన్ ఫీజు రీయింబర్స్‌మెంట్ (RTF / విద్యా దీవెన) మరియు వసతి, భోజన నిర్వహణ రుసుము (MTF / వసతి దీవెన) పథకాలను అమలు చేస్తోంది.",
        },
        "application": {
            "en": "How to apply for Vidya Deevena & Vasathi Deevena:\n\n• **JnanaBhumi Online Submission:** Applications are submitted through college verification on the official JnanaBhumi portal: https://jnanabhumi.ap.gov.in.\n• **College Certification:** Principals and college scholarship nodal officers verify admission allotment, fee structure, and biometric attendance.\n• **Attendance Mandate:** Mandatory minimum 75% college aggregate attendance.\n• **Disbursement Channel:** Tuition fees and maintenance allowances are disbursed via DBT in accordance with prevailing state scholarship and JnanaBhumi guidelines.\n• **Helpline & Tracking:** Track application status on JnanaBhumi or contact Spandana at 1902.",
            "te": "విద్యా దీవెన మరియు వసతి దీవెన దరఖాస్తు విధానం:\n\n• **జ్ఞానభూమి దరఖాస్తు**: విద్యార్థులు తాము చేరిన కళాశాల ద్వారా అధికారిక జ్ఞానభూమి పోర్టల్ (https://jnanabhumi.ap.gov.in) లో ఆన్‌లైన్ దరఖాస్తు సమర్పించాలి.\n• **కళాశాల ధ్రువీకరణ**: కళాశాల ప్రిన్సిపాల్ మరియు స్కాలర్‌షిప్ నోడల్ ఆఫీసర్ అడ్మిషన్, ఫీజు రసీదు మరియు హాజరును ధ్రువీకరిస్తారు.\n• **హాజరు నిబంధన**: కళాశాలలో కనీసం 75% హాజరు తప్పనిసరి.\n• **చెల్లింపు విధానం**: ఫీజు మరియు వసతి నిధులు డీబీటీ (DBT) ద్వారా ప్రభుత్వ నిబంధనల ప్రకారం విడుదల చేయబడతాయి.\n• **పోర్టల్ & హెల్ప్‌లైన్**: దరఖాస్తు స్థితిని జ్ఞానభూమి పోర్టల్‌లో తెలుసుకోవచ్చు లేదా స్పందన 1902 కు కాల్ చేయవచ్చు.",
        },
        "documents": {
            "en": "Required documents for Vidya Deevena & Vasathi Deevena:\n\n• **Identity Proof:** Student and Mother/Guardian Aadhaar Cards.\n• **Income Proof:** Valid Rice Card or MeeSeva Income Certificate validating annual family income <= Rs. 2,50,000 (2.5 Lakh).\n• **Community Proof:** Integrated Community / Caste Certificate for SC, ST, BC, EBC, Kapu, Minority categories.\n• **Admission Records:** College Admission Allotment Order and institutional Fee Structure receipt.\n• **Bank Passbook:** Mother's active Aadhaar-seeded, NPCI-mapped bank passbook.\n• **Academic Marksheets:** Previous qualifying examination marksheet.",
            "te": "విద్యా దీవెన మరియు వసతి దీవెనకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డులు**: విద్యార్థి మరియు తల్లి/సంరక్షకురాలి ఆధార్ కార్డులు.\n• **ఆదాయ ధ్రువీకరణ**: రైస్ కార్డు లేదా మీసేవ ఆదాయ ధ్రువీకరణ పత్రం (కుటుంబ వార్షిక ఆదాయం రూ. 2.50 లక్షల లోపు).\n• **కుల ధ్రువీకరణ**: ఎస్సీ, ఎస్టీ, బీసీ, ఈబీసీ, కాపు, మైనారిటీ విద్యార్థులకు కుల ధ్రువీకరణ పత్రం.\n• **అడ్మిషన్ పత్రాలు**: కళాశాల అడ్మిషన్ అలాట్‌మెంట్ ఆర్డర్ మరియు ఫీజు రసీదు.\n• **బ్యాంక్ పాస్‌బుక్**: తల్లి పేరు మీద ఉన్న ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ పాస్‌బుక్.\n• **మార్కుల జాబితా**: మునుపటి ఉత్తీర్ణత మార్కుల జాబితా.",
        },
        "eligibility": {
            "en": "Eligibility for Vidya Deevena & Vasathi Deevena:\n\n• Students pursuing recognized post-matric courses (ITI, Polytechnic, Degree, Engineering, Medicine, Pharmacy, MBA, MCA, PG).\n• Total annual family income from all sources must not exceed Rs. 2,50,000 (2.5 Lakh).\n• Agricultural landholding under 25 acres dry land or 10 acres wetland.\n• Mandatory 75% minimum aggregate attendance in the enrolled course.\n• Exclusions: Four-wheeler ownership (commercial livelihood vehicles exempted); families with regular government employees or pensioners.",
            "te": "విద్యా దీవెన మరియు వసతి దీవెన అర్హతలు:\n\n• గుర్తింపు పొందిన ఐటీఐ, పాలిటెక్నిక్, డిగ్రీ, ఇంజనీరింగ్, మెడిసిన్, పీజీ కోర్సులు చదువుతున్న విద్యార్థులు.\n• కుటుంబ వార్షిక ఆదాయం రూ. 2.50 లక్షల లోపు ఉండాలి.\n• వ్యవసాయ భూమి 25 ఎకరాల మెట్ట లేదా 10 ఎకరాల మాగాణి లోపు ఉండాలి.\n• కళాశాలలో కనీసం 75% హాజరు తప్పనిసరి.\n• మినహాయింపులు: ప్రభుత్వ ఉద్యోగులు మరియు నాలుగు చక్రాల వాహనం ఉన్న కుటుంబాలు అనర్హులు.",
        },
        "benefits": {
            "en": "Financial assistance under Vidya Deevena (RTF) & Vasathi Deevena (MTF):\n\n• **Vidya Deevena (RTF):** Full tuition fee reimbursement covering approved college tuition fees, examination fees, and special fees determined by higher education regulatory authorities.\n• **Vasathi Deevena (MTF):** Maintenance financial assistance to support food, hostel, and boarding expenses as determined by applicable official assistance schedules and departmental budget notifications.\n• **Disbursement Channel:** Released via Direct Benefit Transfer (DBT) into verified Aadhaar-NPCI accounts as prescribed by departmental guidelines.",
            "te": "విద్యా దీవెన మరియు వసతి దీవెన ఆర్థిక సహాయ ప్రయోజనాలు:\n\n• **విద్యా దీవెన (RTF)**: ప్రభుత్వం నిర్ణయించిన ప్యాకేజీల ప్రకారం అర్హులైన విద్యార్థుల పూర్తి కళాశాల ట్యూషన్ ఫీజు రీయింబర్స్‌మెంట్ లభిస్తుంది.\n• **వసతి దీవెన (MTF)**: విద్యార్థుల వసతి మరియు భోజన ఖర్చుల కోసం వర్తించే అధికారిక సహాయ షెడ్యూళ్లు మరియు శాఖాపరమైన బడ్జెట్ నిబంధనల ప్రకారం నిర్వహణ భత్యం అందుతుంది.\n• **చెల్లింపు విధానం**: నిధులు డీబీటీ (DBT) ద్వారా నేరుగా ఆధార్ అనుసంధాన ఖాతాలకు జమ చేయబడతాయి.",
        },
    },

    "agri_kisan_credit_card": {
        "title_en": "Kisan Credit Card (KCC)",
        "title_te": "కిసాన్ క్రెడిట్ కార్డు (KCC)",
        "portals": ["https://agricoop.gov.in", "https://pmkisan.gov.in", "https://www.jansamarth.in"],
        "helplines": ["1800-180-1551", "1902"],
        "overview": {
            "en": "Kisan Credit Card (KCC) provides farmers with timely, adequate, and affordable institutional credit under a simplified single-window mechanism to meet short-term crop cultivation expenses, post-harvest expenses, farm asset maintenance, and working capital for dairy, poultry, and fisheries.",
            "te": "కిసాన్ క్రెడిట్ కార్డు (KCC) రైతులకు వ్యవసాయ సాగు ఖర్చులు, విత్తనాలు, ఎరువులు మరియు పాడి పశువులు, మత్స్య సాగు పెట్టుబడి అవసరాల కోసం సకాలంలో రాయితీ వడ్డీతో బ్యాంక్ రుణాలు అందించే ప్రభుత్వ పథకం.",
        },
        "application": {
            "en": "How to apply for Kisan Credit Card (KCC):\n\n• **Bank / RSK Application:** Apply at any Commercial Bank, Regional Rural Bank (APGVB/CGGB), or District Cooperative Central Bank (DCCB) / PACS branch, or meet the Village Agriculture Assistant (VAA) at your local Rythu Seva Kendram (RSK/RBK).\n• **Online Route:** PM-Kisan beneficiaries and farmers can submit inquiries online via https://www.jansamarth.in or https://pmkisan.gov.in.\n• **Documents Needed:** KCC application form, Aadhaar Card, land records (Pattadar passbook / 1-B) or CCRC agreement for tenant farmers, and bank passbook.\n• **Helplines:** Contact Kisan Call Centre toll-free at 1800-180-1551 or Spandana at 1902.",
            "te": "కిసాన్ క్రెడిట్ కార్డు దరఖాస్తు విధానం:\n\n• **బ్యాంక్ లేదా రైతు సేవా కేంద్రం**: మీ సమీపంలోని ఏదైనా వాణిజ్య బ్యాంకు, ప్రాంతీయ గ్రామీణ బ్యాంకు (APGVB / CGGB) లేదా డీసీసీబీ / పీఏసీఎస్ శాఖను సంప్రదించండి లేదా రైతు సేవా కేంద్రంలో (RSK/RBK) గ్రామ వ్యవసాయ సహాయకుడిని కలవండి.\n• **ఆన్‌లైన్ దరఖాస్తు**: పీఎం కిసాన్ లబ్ధిదారులు jansamarth.in లేదా pmkisan.gov.in పోర్టల్ ద్వారా ఆన్‌లైన్‌లో దరఖాస్తు చేసుకోవచ్చు.\n• **అవసరమైన పత్రాలు**: నింపిన దరఖాస్తు ఫారం, ఆధార్ కార్డు, పట్టాదారు పాస్‌బుక్ / 1-బి రికార్డు (కౌలు రైతులకు సీసీఆర్‌సీ కార్డు) మరియు బ్యాంక్ పాస్‌బుక్.\n• **హెల్ప్‌లైన్లు**: కిసాన్ కాల్ సెంటర్ ఉచిత నంబర్ 1800-180-1551 లేదా స్పందన 1902 కు కాల్ చేయవచ్చు.",
        },
        "documents": {
            "en": "Required documents for Kisan Credit Card (KCC):\n\n• **Application Form:** Signed KCC loan application form.\n• **Identity & Address Proof:** Aadhaar Card, Voter ID, or PAN Card.\n• **Land Proof:** Pattadar Passbook, 1-B revenue extract, or registered CCRC agreement for tenant farmers / JLGs.\n• **Bank Records:** Active bank account passbook and recent passport-size photographs.",
            "te": "కిసాన్ క్రెడిట్ కార్డుకు అవసరమైన పత్రాలు:\n\n• **దరఖాస్తు ఫారం**: సంతకం చేసిన కేసీసీ రుణ దరఖాస్తు ఫారం.\n• **గుర్తింపు పత్రాలు**: ఆధార్ కార్డు, ఓటర్ గుర్తింపు కార్డు లేదా పాన్ కార్డు.\n• **భూమి పత్రాలు**: పట్టాదారు పాస్‌బుక్, 1-బి రెవెన్యూ రికార్డు (కౌలు రైతులకు సీసీఆర్‌సీ సాగు ఒప్పంద పత్రం).\n• **బ్యాంక్ రికార్డులు**: ఆధార్ అనుసంధాన బ్యాంక్ పాస్‌బుక్ మరియు పాస్‌పోర్ట్ సైజు ఫోటోలు.",
        },
        "eligibility": {
            "en": "Eligibility for Kisan Credit Card (KCC):\n\n• Individual owner-cultivators and joint borrowers cultivating land in Andhra Pradesh.\n• Tenant farmers, oral lessees, and sharecroppers cultivating under valid tenancy arrangements or organized into Joint Liability Groups (JLGs) / Self Help Groups (SHGs).\n• Animal husbandry, dairy, and fisheries farmers requiring working capital.",
            "te": "కిసాన్ క్రెడిట్ కార్డు అర్హతలు:\n\n• సొంత భూమి ఉన్న రైతులు మరియు ఉమ్మడి సాగుదారులు.\n• చెల్లుబాటు అయ్యే సీసీఆర్‌సీ ఒప్పంద పత్రాలు కలిగిన కౌలు రైతులు, జేఎల్జీ (JLG) లేదా స్వయం సహాయక బృందాల (SHG) రైతులు.\n• పాడి పశువులు, గొర్రెలు/మేకల పెంపకం మరియు చేపల సాగు చేపట్టే రైతులు కూడా అర్హులు.",
        },
        "benefits": {
            "en": "Credit terms and interest subvention under Kisan Credit Card (KCC):\n\n• **Interest Subvention Framework:** Agricultural crop credit is extended at concessional interest rates under Government of India and RBI guidelines; interest subvention and prompt repayment incentives are governed by prevailing central and banking directives.\n• **Prompt Repayment Incentive (PRI):** An additional interest subvention is available for disciplined borrowers repaying loans on or before the due date as per applicable departmental circulars.\n• **Credit Limits & Collateral Terms:** Loan limits, collateral waivers, and margin norms are governed by prevailing RBI and NABARD directives; applicants should verify current credit limits and applicable terms directly with their lending bank.\n• **Allied Activities:** Working capital credit is available for animal husbandry, dairy, and fisheries within applicable banking guidelines.",
            "te": "కిసాన్ క్రెడిట్ కార్డు వడ్డీ రాయితీ మరియు ప్రయోజనాలు:\n\n• **వడ్డీ రాయితీ మార్గదర్శకాలు**: కేంద్ర ప్రభుత్వం మరియు రిజర్వ్ బ్యాంక్ మార్గదర్శకాల ప్రకారం పంట రుణాలకు రాయితీ వడ్డీ రేట్లు వర్తిస్తాయి; ఖచ్చితమైన వడ్డీ రేట్లు మరియు రాయితీలు తాజా నిబంధనలపై ఆధారపడి ఉంటాయి.\n• **సకాల చెల్లింపు ప్రోత్సాహకం (PRI)**: గడువు తేదీ లోపు రుణాలు తిరిగి చెల్లించే రైతులకు ప్రోత్సాహక వడ్డీ రాయితీ వర్తించే ప్రభుత్వ సర్క్యులర్ల ప్రకారం లభిస్తుంది.\n• **రుణ పరిమితులు & హామీ నిబంధనలు**: రుణ పరిమితులు, తాకట్టు మినహాయింపులు రిజర్వ్ బ్యాంక్ (RBI) మరియు నాబార్డ్ నిబంధనలకు లోబడి ఉంటాయి; ప్రస్తుత రుణ పరిమితులను సంబంధిత బ్యాంక్ శాఖలో నిర్ధారించుకోవాలి.\n• **అనుబంధ రంగాలు**: పాడి పరిశ్రమ, పశుసంవర్ధక మరియు మత్స్య సాగుకు కూడా బ్యాంకింగ్ నిబంధనల ప్రకారం వర్కింగ్ క్యాపిటల్ రుణాలు లభిస్తాయి.",
        },
    },

    "agri_pm_crop_insurance_ap": {
        "title_en": "PM Fasal Bima Yojana & Crop Insurance in AP",
        "title_te": "ఆంధ్రప్రదేశ్ పంటల బీమా పథకం (పీఎం ఫసల్ బీమా యోజన)",
        "portals": ["https://pmfby.gov.in", "https://apagrisnet.gov.in"],
        "helplines": ["14447", "1800-180-1551", "1902"],
        "overview": {
            "en": "The Crop Insurance program in Andhra Pradesh operates within the framework of Pradhan Mantri Fasal Bima Yojana (PMFBY) alongside state-notified agricultural guidelines. Crop insurance provides financial risk coverage and compensation against crop yield losses caused by notified natural calamities, unseasonal weather, and pests.",
            "te": "ఆంధ్రప్రదేశ్‌లో పంటల బీమా కార్యక్రమం కేంద్ర ప్రభుత్వ పీఎం ఫసల్ బీమా యోజన (PMFBY) మరియు రాష్ట్ర వ్యవసాయ శాఖ మార్గదర్శకాల ప్రకారం అమలు చేయబడుతోంది. ప్రకృతి వైపరీత్యాలు, కరువు, వరదలు మరియు తెగుళ్ళ వల్ల జరిగే పంట నష్టాలకు ఇది రైతులకు ఆర్థిక రక్షణ మరియు బీమా పరిహారం అందిస్తుంది.",
        },
        "application": {
            "en": "How to enroll and apply for Crop Insurance in Andhra Pradesh:\n\n• **Mandatory e-Crop Booking:** Cultivating farmers must complete field crop booking on the state e-Crop (e-Panta) digital portal through their Village Agriculture Assistant (VAA) at the local Rythu Seva Kendram (RSK/RBK). Digital e-Crop booking is the baseline record for crop insurance.\n• **RSK / RBK Verification:** Visit your local Rythu Seva Kendram to verify that your sown crop, survey number, and acreage are accurately recorded in the seasonal notification list.\n• **Bank Account Mapping:** Ensure your bank account is seeded with Aadhaar and mapped with NPCI for direct DBT claim crediting.\n• **Claim Settlement:** Loss assessment is conducted via Crop Cutting Experiments (CCEs) on an area approach basis, and compensation is deposited directly via DBT.\n• **Portals & Helpline:** Check national PMFBY portal at https://pmfby.gov.in, AP Agriculture portal at https://apagrisnet.gov.in, or call toll-free helpline 14447 / 1800-180-1551 / 1902.",
            "te": "ఆంధ్రప్రదేశ్ పంటల బీమా పథకం (పీఎం ఫసల్ బీమా యోజన) నమోదు విధానం:\n\n• **ఈ-పంట (e-Crop) నమోదు ప్రాథమికం**: పంటల బీమా రక్షణ పొందడానికి రైతులు విధిగా తమ స్థానిక గ్రామ వ్యవసాయ సహాయకుడి (VAA) ద్వారా ఈ-క్రాప్ (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో సాగు వివరాలను నమోదు చేయించుకోవాలి. ఈ-పంట నమోదే బీమాకు ప్రాథమిక ప్రాతిపదిక.\n• **రైతు సేవా కేంద్రం (RSK/RBK)**: మీ సమీపంలోని రైతు సేవా కేంద్రం / రైతు భరోసా కేంద్రాన్ని సందర్శించి పంట నమోదు, సర్వే నంబర్లు మరియు నోటిఫై చేసిన పంటల జాబితాను నిర్ధారించుకోండి.\n• **బ్యాంక్ ఖాతా అనుసంధానం**: నష్టపరిహారం డీబీటీ (DBT) ద్వారా నేరుగా జమ కావడానికి మీ బ్యాంక్ ఖాతాకు ఆధార్ మరియు ఎన్‌పీసీఐ అనుసంధానం పూర్తయి ఉండాలి.\n• **పరిహారం చెల్లింపు**: పంట కోత ప్రయోగాలు (CCEs) మరియు ప్రభుత్వ నిబంధనల ఆధారంగా నష్టం లెక్కించబడి పరిహారం నేరుగా అందుతుంది.\n• **అధికారిక పోర్టల్స్ & హెల్ప్‌లైన్**:\n  - జాతీయ పంటల బీమా పోర్టల్: https://pmfby.gov.in\n  - ఏపీ వ్యవసాయ పోర్టల్: https://apagrisnet.gov.in\n  - టోల్ ఫ్రీ హెల్ప్‌లైన్: 14447 / కిసాన్ కాల్ సెంటర్: 1800-180-1551 / స్పందన: 1902.",
        },
        "documents": {
            "en": "Required documents for AP Crop Insurance:\n\n• **e-Crop Registration:** Verified e-Crop / e-Panta booking receipt from RSK/RBK.\n• **Aadhaar Card:** Aadhaar Card of the cultivating farmer.\n• **Land Proof:** Pattadar passbook, 1-B record, or registered CCRC card for tenant farmers.\n• **Bank Passbook:** Aadhaar-linked active bank account passbook for DBT claims.",
            "te": "పంటల బీమాకు అవసరమైన పత్రాలు:\n\n• **ఈ-పంట రసీదు**: గ్రామ వ్యవసాయ సహాయకుడి ద్వారా జారీ చేయబడిన ఈ-క్రాప్ (e-Crop / e-Panta) నమోదు రసీదు.\n• **ఆధార్ కార్డు**: సాగుదారు ఆధార్ కార్డు.\n• **భూమి పత్రాలు**: పట్టాదారు పాస్‌బుక్, 1-బి రికార్డు లేదా కౌలు రైతులకు సీసీఆర్‌సీ (CCRC) ఒప్పంద పత్రం.\n• **బ్యాంక్ పాస్‌బుక్**: పరిహారం డీబీటీ కొరకు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతా పాస్‌బుక్.",
        },
        "eligibility": {
            "en": "Eligibility for AP Crop Insurance:\n\n• Farmers cultivating notified crops in notified areas in Andhra Pradesh during the agricultural season.\n• Compulsory enrollment and digital booking on the state e-Crop (e-Panta) portal.\n• Premium contributions and coverage terms depend on applicable seasonal notifications and crop listings.\n• Tenant farmers with valid CCRC cards are eligible subject to departmental guidelines.",
            "te": "పంటల బీమా అర్హత నిబంధనలు:\n\n• ఆంధ్రప్రదేశ్‌లో నోటిఫై చేసిన ప్రాంతాల్లో, నోటిఫై చేసిన పంటలను సాగుచేస్తున్న రైతులు.\n• తప్పనిసరిగా ఈ-క్రాప్ (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో సాగు నమోదు పూర్తయి ఉండాలి.\n• ప్రీమియం మరియు కవరేజ్ నిబంధనలు ఆయా సీజనల్ ప్రభుత్వ ఉత్తర్వులకు లోబడి ఉంటాయి.\n• చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) కార్డులు ఉన్న కౌలు రైతులకు కూడా నిబంధనల ప్రకారం బీమా రక్షణ వర్తిస్తుంది.",
        },
        "benefits": {
            "en": "Risk coverage and compensation under AP Crop Insurance:\n\n• **Prevented Sowing:** Deficit rainfall or adverse weather preventing sowing in notified areas.\n• **Standing Crop Losses:** Damage from drought, flood, inundation, pests, cyclonic rains, or hailstorms.\n• **Post-Harvest Losses:** Damage to harvested crops kept in 'cut and spread' condition in the field for up to 14 days due to unseasonal rains or cyclones.\n• **Area Approach Settlement:** Compensation assessed through digital Crop Cutting Experiments (CCEs) and credited directly via DBT without intermediaries.",
            "te": "పంటల బీమా రక్షణ మరియు పరిహార వివరాలు:\n\n• **విత్తనం వేయలేని స్థితి**: వర్షాభావం లేదా విపత్తుల వల్ల విత్తనం వేయలేకపోవడం.\n• **నిలబడిన పంట నష్టం**: కరువు, వరదలు, ముంపు, తెగుళ్ళు, అకాల వర్షాలు మరియు తుఫానుల వల్ల పంట నష్టం.\n• **కోత తర్వాతి నష్టం**: కోసి పొలంలో ఆరబెట్టిన 14 రోజుల లోపు అకాల వర్షాల వల్ల కలిగే నష్టం.\n• **పరిహారం చెల్లింపు**: పంట కోత ప్రయోగాల (CCEs) ద్వారా నష్టం లెక్కించబడి నేరుగా డీబీటీ (DBT) ద్వారా రైతుల ఖాతాలకు జమ అవుతుంది.",
        },
    },

    "health_104_108_emergency_health_services": {
        "title_en": "104 & 108 Emergency Health Services",
        "title_te": "104 మరియు 108 అత్యవసర ఆరోగ్య సేవలు",
        "portals": ["https://cfw.ap.nic.in", "https://drntrvaidyaseva.ap.gov.in"],
        "helplines": ["108", "104", "1902"],
        "overview": {
            "en": "108 Emergency Ambulance Service provides 24/7 free toll-free emergency transport and immediate pre-hospital care for trauma, accidents, and acute conditions. 104 Mobile Medical Units and Health Helpline provide free medical counseling, chronic disease screening, and doorstep village healthcare.",
            "te": "108 అంబులెన్స్ సేవ ప్రమాదాలు, తీవ్ర అనారోగ్య పరిస్థితుల్లో 24/7 ఉచిత అత్యవసర రవాణా అందిస్తుంది. 104 సంచార వైద్య వాహనాలు (MMU) మరియు హెల్ప్‌లైన్ గ్రామాల్లో ఉచిత వైద్య సలహాలు, పరీక్షలు మరియు మందులు అందిస్తాయి.",
        },
        "application": {
            "en": "How to access 108 and 104 Health Services:\n\n• **108 Medical Emergency:** Dial 108 from any mobile or landline without dialing code for immediate free ambulance dispatch. No documentation or identity card is required to receive emergency medical response; never delay lifesaving medical treatment to search for cards.\n• **104 Health Helpline:** Dial 104 for free medical counseling, blood bank availability, government health scheme details, and Family Doctor village schedules.\n• **Zero Charges:** Both services are completely free of cost across Andhra Pradesh.",
            "te": "108 మరియు 104 సేవలు పొందే విధానం:\n\n• **108 అత్యవసర వైద్య సేవ**: ప్రమాదాలు, గుండెపోటు లేదా ఇతర అత్యవసర సమయాల్లో ఏ ఫోన్ నుండైనా 108 కు ఉచితంగా కాల్ చేయండి. ఎటువంటి గుర్తింపు పత్రాలు లేదా రేషన్ కార్డులు అవసరం లేదు; కార్డుల కోసం వెతకడానికి కాల్ చేయడంలో ఆలస్యం చేయరాదు.\n• **104 ఉచిత వైద్య సలహా**: ఉచిత వైద్య సలహాలు, రక్త లభ్యత, మరియు ఫ్యామిలీ డాక్టర్ గ్రామ పర్యటనల వివరాల కొరకు 104 కు కాల్ చేయండి.\n• **పూర్తి ఉచితం**: ఈ రెండు సేవలు ఆంధ్రప్రదేశ్ ప్రభుత్వం ద్వారా ప్రజలకు పూర్తిగా ఉచితంగా అందించబడుతున్నాయి.",
        },
        "documents": {
            "en": "Documentation for 108 and 104 Services:\n\n• **108 Emergency Service:** ZERO documents required. Lifesaving treatment and ambulance dispatch are never conditioned on possessing cards or identity proofs.\n• **104 Mobile Medical Clinics:** Patient Aadhaar Card or previous clinic doctor prescriptions (to dispense chronic monthly maintenance medications).",
            "te": "108 మరియు 104 సేవలకు పత్రాలు:\n\n• **108 అత్యవసర సేవ**: ఎటువంటి పత్రాలు అవసరం లేదు. అత్యవసర సహాయం పూర్తిగా ఉచితం.\n• **104 మొబైల్ క్లినిక్**: నెలవారీ బీపీ, షుగర్ మందుల పంపిణీ కొరకు పాత ప్రిస్క్రిప్షన్ లేదా ఆధార్ కార్డు.",
        },
        "eligibility": {
            "en": "Eligibility for 108 and 104 Services:\n\n• All citizens and residents in Andhra Pradesh requiring acute emergency medical care or village-level healthcare support.",
            "te": "108 మరియు 104 సేవల అర్హత:\n\n• అత్యవసర వైద్య సహాయం లేదా గ్రామస్థాయి ఆరోగ్య సేవలు అవసరమైన ఆంధ్రప్రదేశ్‌లోని ప్రజలందరూ అర్హులు.",
        },
        "benefits": {
            "en": "Services and facilities provided under 108 and 104:\n\n• **108 Fleet:** Advanced Life Support (ALS) and Basic Life Support (BLS) ambulances equipped with oxygen, defibrillators, multipara monitors, and trained Emergency Medical Technicians (EMTs).\n• **Emergency Conditions Covered:** Road accidents, cardiac arrest, stroke, maternal labor, acute poisoning, snakebites, and neonatal emergencies.\n• **104 Mobile Units & Family Doctor:** Village-level screening for BP and diabetes, free monthly chronic medication refills, antenatal/postnatal care, and doorstep doctor checkups for bedridden patients.",
            "te": "108 మరియు 104 అందించే సేవలు మరియు ప్రయోజనాలు:\n\n• **108 అంబులెన్స్ వాహనాలు**: ఆక్సిజన్, డీఫిబ్రిలేటర్, మల్టీపారా మానిటర్లు మరియు నిపుణులైన ఈఎంటీ (EMT) సిబ్బందితో కూడిన అధునాతన అంబులెన్సులు.\n• **కవర్ అయ్యే అత్యవసర పరిస్థితులు**: రోడ్డు ప్రమాదాలు, గుండెపోటు, ప్రసవ నొప్పులు, పక్షవాతం, పాముకాటు, విషప్రయోగాలు.\n• **104 మరియు ఫ్యామిలీ డాక్టర్**: గ్రామంలోనే ఉచిత బీపీ, షుగర్ పరీక్షలు, దీర్ఘకాలిక రోగులకు ఉచిత నెలవారీ మందుల పంపిణీ, గర్భిణీ స్త్రీల పరీక్షలు.",
        },
    },

    "health_ayushman_bharat_pmjay_ap": {
        "title_en": "Ayushman Bharat PM-JAY",
        "title_te": "ఆయుష్మాన్ భారత్ – పీఎం జన్ ఆరోగ్య యోజన",
        "portals": ["https://nha.gov.in", "https://pmjay.gov.in", "https://drntrvaidyaseva.ap.gov.in"],
        "helplines": ["14555", "104", "1902"],
        "overview": {
            "en": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB PM-JAY) is the National Health Assurance scheme funded jointly by the Government of India and the Government of Andhra Pradesh. In Andhra Pradesh, it operates in co-branded convergence with the state's Dr. NTR Vaidya Seva healthcare framework to extend secondary and tertiary care hospitalization benefits.",
            "te": "ఆయుష్మాన్ భారత్ ప్రధాన మంత్రి జన్ ఆరోగ్య యోజన (AB PM-JAY) కేంద్ర మరియు రాష్ట్ర ప్రభుత్వాల భాగస్వామ్యంతో అమలు చేయబడుతున్న జాతీయ ఆరోగ్య రక్షణ పథకం. ఆంధ్రప్రదేశ్‌లో ఇది డాక్టర్ ఎన్టీఆర్ వైద్య సేవతో సమన్వయం చేయబడి ద్విభాషా కో-బ్రాండెడ్ కార్డుల ద్వారా ద్వితీయ, తృతీయ స్థాయి వైద్య సేవలు అందిస్తోంది.",
        },
        "application": {
            "en": "How to access services and verify eligibility under Ayushman Bharat PM-JAY:\n\n• **Hospital Helpdesk:** Visit any empaneled government or private network hospital across Andhra Pradesh or nationwide. Approach the Ayushman Mitra / Aarogyamithra at the helpdesk.\n• **Beneficiary Verification:** Present your co-branded Ayushman Card, Aadhaar Card, or valid state Rice Card for instant digital biometric verification.\n• **Cashless Treatment:** Eligible patients receive pre-authorized cashless secondary and tertiary hospitalization.\n• **Portals & Helpline:** Verify eligibility online at https://beneficiary.nha.gov.in or https://pmjay.gov.in, or call national toll-free helpline 14555 or 104 / 1902.",
            "te": "ఆయుష్మాన్ భారత్ పీఎం-జేవై సేవలు పొందే విధానం మరియు ధ్రువీకరణ:\n\n• **ఆసుపత్రి హెల్ప్‌డెస్క్**: ఆంధ్రప్రదేశ్‌లోని లేదా దేశవ్యాప్తంగా నెట్‌వర్క్ ఆసుపత్రులలోని ఆయుష్మాన్ మిత్ర / ఆరోగ్యమిత్ర హెల్ప్‌డెస్క్‌ను సంప్రదించండి.\n• **గుర్తింపు పత్రాలు**: తక్షణ ధ్రువీకరణ కొరకు మీ కో-బ్రాండెడ్ ఆయుష్మాన్ కార్డ్, ఆధార్ కార్డు లేదా రాష్ట్ర రైస్ కార్డును చూపించండి.\n• **ఉచిత నగదు రహిత చికిత్స**: ముందస్తు అనుమతి (Pre-authorization) ద్వారా ఆసుపత్రులలో ఉచిత నగదు రహిత చికిత్స లభిస్తుంది.\n• **పోర్టల్స్ & హెల్ప్‌లైన్**: అర్హత వివరాల కొరకు https://pmjay.gov.in చూడండి లేదా జాతీయ టోల్ ఫ్రీ నంబర్ 14555 లేదా 104 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Ayushman Bharat PM-JAY:\n\n• **Identity Proof:** Aadhaar Card of the patient and family head.\n• **Eligibility Card:** Co-branded Ayushman Card (PM-JAY Golden Card) or valid state Rice Card / Ration Card.\n• **Hospital Referral:** Referral slip from primary/secondary health center if applicable.",
            "te": "ఆయుష్మాన్ భారత్ పథకానికి అవసరమైన పత్రాలు:\n\n• **గుర్తింపు కార్డు**: రోగి మరియు కుటుంబ పెద్ద ఆధార్ కార్డు.\n• **అర్హత పత్రం**: కో-బ్రాండెడ్ ఆయుష్మాన్ కార్డ్ లేదా రాష్ట్ర ప్రభుత్వం జారీ చేసిన తెల్ల రేషన్ కార్డు (Rice Card).\n• **వైద్య రికార్డులు**: ప్రాథమిక ఆరోగ్య కేంద్రం రెఫరల్ లేదా ముందస్తు వైద్య రికార్డులు (వర్తిస్తే).",
        },
        "eligibility": {
            "en": "Eligibility for Ayushman Bharat PM-JAY:\n\n• Families identified under SECC database or active holders of state Rice Cards / BPL cards in Andhra Pradesh.\n• Covers pre-existing conditions from day one with no restriction on family size or age.\n• Provides national portability for hospitalization at any empaneled hospital across India under NHA guidelines.",
            "te": "ఆయుష్మాన్ భారత్ అర్హత నిబంధనలు:\n\n• ఎస్ఈసీసీ (SECC) డేటాబేస్ ప్రకారం గుర్తించబడిన కుటుంబాలు మరియు ఆంధ్రప్రదేశ్‌లో చెల్లుబాటు అయ్యే రైస్ కార్డు కలిగిన కుటుంబాలు అర్హులు.\n• కుటుంబ సభ్యుల సంఖ్య లేదా వయస్సుతో సంబంధం లేకుండా కుటుంబం మొత్తానికి ఉచిత చికిత్స వర్తిస్తుంది.\n• దేశవ్యాప్తంగా ఏ ఎంపానెల్ నెట్‌వర్క్ ఆసుపత్రిలోనైనా పోర్టబిలిటీ ద్వారా ఉచిత చికిత్స పొందవచ్చు.",
        },
        "benefits": {
            "en": "Benefits and national portability under Ayushman Bharat PM-JAY:\n\n• **Inpatient Hospitalization:** Inpatient care coverage for secondary and tertiary medical/surgical procedures at empaneled hospitals across India under NHA package rates.\n• **National Portability:** Beneficiaries from Andhra Pradesh can access inpatient hospitalization at participating PM-JAY empaneled hospitals nationwide subject to NHA portability rules.\n• **Senior Citizens:** Senior citizens aged 70 and above may access designated health benefits under the Ayushman framework (such as through the Ayushman Vay Vandana Card) subject to NHA operational guidelines.",
            "te": "ఆయుష్మాన్ భారత్ ప్రయోజనాలు మరియు జాతీయ పోర్టబిలిటీ:\n\n• **ఇన్-పేషెంట్ చికిత్స**: దేశవ్యాప్తంగా పీఎం-జేఏవై కింద ఎంపానెల్ అయిన ఆసుపత్రులలో జాతీయ ఆరోగ్య అథారిటీ (NHA) ప్యాకేజీ రేట్ల ప్రకారం ఇన్-పేషెంట్ చికిత్స అందుబాటులో ఉంటుంది.\n• **జాతీయ పోర్టబిలిటీ**: ఆంధ్రప్రదేశ్‌లోని లబ్ధిదారులు దేశవ్యాప్తంగా ఏ నెట్‌వర్క్ ఆసుపత్రిలోనైనా పోర్టబిలిటీ ద్వారా ఉచిత చికిత్స పొందవచ్చు.\n• **సీనియర్ సిటిజన్లు**: 70 ఏళ్లు పైబడిన వృద్ధులు ఆయుష్మాన్ వయ వందన కార్డ్ ద్వారా ప్రత్యేక ప్రయోజనాలు పొందవచ్చు.",
        },
        "comparison": {
            "en": "Relationship between Ayushman Bharat PM-JAY and Dr. NTR Vaidya Seva:\n\n• **Co-Branded Convergence:** In Andhra Pradesh, Ayushman Bharat PM-JAY operates in unified convergence with Dr. NTR Vaidya Seva.\n• **State vs National Scope:** Dr. NTR Vaidya Seva governs extensive state coverage within Andhra Pradesh and designated super-specialty network hospitals, while PM-JAY provides national portability across India at NHA-empaneled hospitals.\n• **Official Helpdesk:** Both schemes are accessed through the hospital Aarogyamithra / Ayushman Mitra help desk. Helplines: 14555, 104, 108.",
            "te": "ఆయుష్మాన్ భారత్ మరియు డాక్టర్ ఎన్టీఆర్ వైద్య సేవ సమన్వయం:\n\n• **ఉమ్మడి అనుసంధానం**: ఆంధ్రప్రదేశ్‌లో ఆయుష్మాన్ భారత్ పీఎం-జేఏవై రాష్ట్ర డాక్టర్ ఎన్టీఆర్ వైద్య సేవతో సమన్వయం చేయబడి కో-బ్రాండెడ్ కార్డులతో అమలు చేయబడుతోంది.\n• **రాష్ట్ర మరియు జాతీయ పరిధి**: ఎన్టీఆర్ వైద్య సేవ రాష్ట్ర పరిధిలోని నెట్‌వర్క్ ఆసుపత్రులలో సమగ్ర రక్షణ కల్పించగా, ఆయుష్మాన్ భారత్ దేశవ్యాప్తంగా ఎంపానెల్ ఆసుపత్రులలో పోర్టబిలిటీ చికిత్సను అందిస్తుంది.\n• **హెల్ప్‌డెస్క్**: ఆసుపత్రిలోని ఆరోగ్యమిత్ర ద్వారా రెండు సేవలూ లభిస్తాయి. హెల్ప్‌లైన్లు: 14555, 104, 108.",
        },
    },

    "edu_samagra_shiksha_ap": {
        "title_en": "Samagra Shiksha AP",
        "title_te": "సమగ్ర శిక్ష ఆంధ్రప్రదేశ్",
        "portals": ["https://samagrashiksha.ap.gov.in", "https://schooledu.ap.gov.in"],
        "helplines": ["1800-425-6776", "1902"],
        "overview": {
            "en": "Samagra Shiksha Andhra Pradesh is an overarching school education program extending from pre-school through Class XII, implemented jointly by the Central Government and the Government of Andhra Pradesh. In synergy with the national Mid-Day Meal scheme (PM POSHAN / school nutrition programs), it delivers free learning materials, fortified nutrition, and school infrastructure.",
            "te": "సమగ్ర శిక్షా ఆంధ్రప్రదేశ్ పాఠశాల విద్యలో నాణ్యతా ప్రమాణాలు పెంచేందుకు కేంద్ర మరియు రాష్ట్ర ప్రభుత్వాల భాగస్వామ్యంతో నడుస్తున్న సమగ్ర పథకం. ఇందులో జాతీయ మధ్యాహ్న భోజన పథకం (పీఎం పోషణ్ / పాఠశాల పౌష్టికాహార కార్యక్రమాలు) ద్వారా పౌష్టికాహారం, ఉచిత పాఠ్యపుస్తకాలు, యూనిఫారాలు మరియు మౌలిక వసతులు కల్పించడం జరుగుతుంది.",
        },
        "application": {
            "en": "How to access entitlements under Samagra Shiksha:\n\n• **School Admission:** Enroll your child directly in any recognized Government, Mandal Parishad (MPPS), Zilla Parishad (ZPHS), or Municipal school in Andhra Pradesh.\n• **Automatic Entitlements:** Enrolled students automatically receive free bilingual textbooks, uniforms, school kits, and daily mid-day meals directly at school; no separate application or fee is required.\n• **Official Inquiries:** Inquire at your local government school or contact the Department of School Education at https://schooledu.ap.gov.in or helpline 1800-425-6776 / 1902.",
            "te": "సమగ్ర శిక్ష సేవలు పొందే విధానం:\n\n• **పాఠశాల ప్రవేశం**: ఆంధ్రప్రదేశ్‌లోని ఏదైనా ప్రభుత్వ, మండల పరిషత్ (MPPS), జిల్లా పరిషత్ (ZPHS), లేదా మున్సిపల్ పాఠశాలలో విద్యార్థిని చేర్పించండి.\n• **ఉచిత సేవలు**: చేరిన విద్యార్థులందరికీ ఉచిత ద్విభాషా పాఠ్యపుస్తకాలు, యూనిఫాం వస్త్రాలు, స్కూల్ కిట్లు మరియు మధ్యాహ్న భోజనం నేరుగా బడిలోనే ఉచితంగా లభిస్తాయి; ప్రత్యేక దరఖాస్తు అవసరం లేదు.\n• **సంప్రదింపులు**: మీ స్థానిక ప్రభుత్వ పాఠశాల ప్రధానోపాధ్యాయుడిని సంప్రదించండి లేదా విద్యాశాఖ పోర్టల్ https://schooledu.ap.gov.in చూడండి లేదా 1800-425-6776 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Samagra Shiksha entitlements:\n\n• **School Admission Registration:** Basic school enrollment form.\n• **Student Aadhaar Card:** For Child Info database recording.\n• **No Fees / No Complex Paperwork:** Textbooks, uniforms, and mid-day meals are distributed free of cost to all enrolled students without fees.",
            "te": "సమగ్ర శిక్షకు అవసరమైన పత్రాలు:\n\n• **పాఠశాల అడ్మిషన్**: ప్రాథమిక పాఠశాల ప్రవేశ నమోదు.\n• **విద్యార్థి ఆధార్ కార్డు**: చైల్డ్ ఇన్ఫో డేటాబేస్ నమోదు కొరకు.\n• **ఎటువంటి రుసుము లేదు**: చేరిన విద్యార్థులందరికీ పుస్తకాలు, యూనిఫారాలు, భోజనం ఉచితంగా అందుతాయి.",
        },
        "eligibility": {
            "en": "Eligibility for Samagra Shiksha:\n\n• All students enrolled in Government, Mandal Parishad, Zilla Parishad, Municipal, Tribal, and Social Welfare schools (Classes 1 to 10/12) across Andhra Pradesh.",
            "te": "సమగ్ర శిక్ష అర్హతలు:\n\n• ఆంధ్రప్రదేశ్‌లోని అన్ని ప్రభుత్వ, మండల పరిషత్, జిల్లా పరిషత్, మున్సిపల్ మరియు సంక్షేమ వసతి పాఠశాలల్లో చదువుతున్న విద్యార్థులందరూ అర్హులు.",
        },
        "benefits": {
            "en": "Student entitlements under Samagra Shiksha & School Nutrition Programs:\n\n• **Bilingual Textbooks & Workbooks:** Free distribution of bilingual (English & Telugu side-by-side mirror text) textbooks and workbooks to all students from Class 1 to 10 in Government and Aided schools.\n• **School Uniforms & Kits:** Three pairs of stitched uniforms, school bag, shoes, two pairs of socks, notebooks, and belt distributed at the beginning of the academic year.\n• **Nutritional Mid-Day Meal (PM POSHAN / School Nutrition):** Hot cooked nutritious meal served on all school working days for Classes 1 to 10 following prescribed diet menus including eggs/substitutes and chikki.",
            "te": "సమగ్ర శిక్ష మరియు పౌష్టికాహార పథకం ప్రయోజనాలు:\n\n• **ద్విభాషా పాఠ్యపుస్తకాలు**: 1 నుండి 10వ తరగతి విద్యార్థులందరికీ ఉచిత ద్విభాషా (తెలుగు-ఇంగ్లీష్) పాఠ్యపుస్తకాలు మరియు నోట్‌బుక్స్ పంపిణీ.\n• **యూనిఫారాలు & స్కూల్ కిట్లు**: మూడు జతల యూనిఫాంలు, స్కూల్ బ్యాగ్, బూట్లు, సాక్సులు, బెల్ట్ ఉచిత పంపిణీ.\n• **మధ్యాహ్న భోజనం (పీఎం పోషణ్)**: పాఠశాల పనిదినాల్లో ప్రతిరోజూ వేడివేడి పౌష్టికాహారం, కోడిగుడ్లు, చిక్కీలతో కూడిన భోజనం.",
        },
    },

    "agri_soil_health_card_polam_badi": {
        "title_en": "Soil Health Card & Polam Badi",
        "title_te": "భూసార పరీక్ష కార్డు మరియు పొలం బడి",
        "portals": ["https://soilhealth.dac.gov.in", "https://apagrisnet.gov.in"],
        "helplines": ["155251", "1800-180-1551", "1902"],
        "overview": {
            "en": "The Soil Health Card scheme assesses soil nutrient status across 12 parameters and provides customized crop-specific fertilizer recommendations periodically (typically on a biennial cycle), while Polam Badi farmer field schools impart practical ecological crop management training.",
            "te": "భూసార పరీక్ష కార్డు పథకం రైతుల పొలాల్లోని నేల సారాన్ని 12 రకాల పోషకాల ఆధారంగా పరీక్షించి తగిన ఎరువుల వినియోగానికి సిఫార్సులు చేస్తుంది. పొలం బడి కార్యక్రమం ద్వారా రైతులకు సమగ్ర సస్యరక్షణ మరియు సాగు మెళకువలపై శిక్షణ ఇస్తారు.",
        },
        "application": {
            "en": "How to obtain Soil Health Card and attend Polam Badi:\n\n• **Contact VAA at RSK/RBK:** Contact your Village Agriculture Assistant (VAA) at the local Rythu Seva Kendram (RSK/RBK) or Grama Sachivalayam.\n• **Soil Sample Collection:** Department staff collect representative GPS-tagged soil samples from agricultural holdings.\n• **Testing & Card Issuance:** Samples are analyzed at soil testing laboratories and printed Soil Health Cards with customized nutrient advice are issued to farmers.\n• **Portal & Helpline:** Check test records at https://soilhealth.dac.gov.in or contact helpline 155251 / 1800-180-1551 / 1902.",
            "te": "భూసార పరీక్ష కార్డు పొందే విధానం:\n\n• **రైతు సేవా కేంద్రంలో సంప్రదింపు**: మీ స్థానిక రైతు సేవా కేంద్రం (RSK/RBK) లో గ్రామ వ్యవసాయ సహాయకుడిని (VAA) సంప్రదించండి.\n• **నమూనా సేకరణ**: వ్యవసాయ సిబ్బంది పొలం నుండి మట్టి నమూనాలను శాస్త్రీయంగా సేకరించి ప్రయోగశాలలో పరీక్షిస్తారు.\n• **కార్డు జారీ**: పరీక్షించిన పోషకాల ఆధారంగా సిఫార్సులతో కూడిన భూసార కార్డు రైతుకు అందజేయబడుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://soilhealth.dac.gov.in చూడండి లేదా 155251 / 1800-180-1551 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Soil Health Card:\n\n• **Aadhaar Card:** Aadhaar Card of the farmer.\n• **Land Proof:** Land Pattadar passbook, 1-B revenue document, or land survey numbers.\n• **Mobile Number:** Active mobile number to receive test status SMS alerts.",
            "te": "భూసార పరీక్ష కార్డుకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: రైతు ఆధార్ కార్డు.\n• **భూమి పత్రాలు**: పట్టాదారు పాస్‌బుక్ లేదా సర్వే నంబర్ వివరాలు.\n• **మొబైల్ నంబర్**: ఎస్ఎంఎస్ సమాచారం కొరకు మొబైల్ నంబర్.",
        },
        "eligibility": {
            "en": "Eligibility for Soil Health Card & Polam Badi:\n\n• All landholding and tenant farmers cultivating agricultural holdings in Andhra Pradesh.",
            "te": "భూసార పరీక్ష కార్డు అర్హత:\n\n• ఆంధ్రప్రదేశ్‌లో వ్యవసాయం చేస్తున్న భూ యజమానులు మరియు కౌలు రైతులందరూ అర్హులు.",
        },
        "benefits": {
            "en": "Benefits of Soil Health Card & Polam Badi:\n\n• **12 Nutrient Parameters:** Testing covers primary macro-nutrients (N, P, K), secondary (S), micronutrients (Zn, Fe, Cu, Mn, B), and physical-chemical properties (pH, EC, OC).\n• **Customized Fertilizer Dosages:** Crop-specific recommendations prevent excessive chemical fertilizer use and reduce input costs.\n• **Polam Badi Farmer Field Schools:** Weekly participatory village field sessions on Integrated Pest Management (IPM), bio-fertilizers, and sustainable cultivation.",
            "te": "భూసార పరీక్ష కార్డు మరియు పొలం బడి ప్రయోజనాలు:\n\n• **12 రకాల పోషకాల పరీక్ష**: ప్రధాన పోషకాలు (ఎన్, పి, కె), సూక్ష్మ పోషకాలు (జింక్, ఐరన్ మొదలైనవి) మరియు నేల లక్షణాలు పరీక్షించబడతాయి.\n• **ఎరువుల ఖర్చు ఆదా**: శాస్త్రీయ సిఫార్సుల వల్ల అనవసర రసాయన ఎరువుల ఖర్చు తగ్గి భూసారం పరిరక్షించబడుతుంది.\n• **పొలం బడి శిక్షణ**: ఆర్ఎస్కే పరిధిలో ప్రతి వారం రైతులకు సమగ్ర సస్యరక్షణ, సేంద్రియ సాగు మరియు తెగుళ్ళ నివారణపై క్షేత్రస్థాయిలో శిక్షణ.",
        },
    },
}


def synthesize_scheme_answer(
    query: str,
    doc_id: str,
    intent: str,
    language: LanguageCode,
    state: Optional[str] = "Andhra Pradesh",
    district: Optional[str] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Synthesizes a natural, grounded, language-appropriate answer for a specific scheme and intent.
    Strictly follows bilingual requirements:
    - Telugu: 100% natural Telugu, zero English paragraphs. Official scheme names, portal URLs, technical terms and helplines preserved.
    - English: 100% clean English, ZERO Telugu script.
    - Word count: 100–180 words.
    Prefers actual retrieved bilingual evidence from chunks over hardcoded profiles.
    Falls back to audited scheme profiles when chunks lack intent-specific evidence.
    """
    profile = SCHEME_PROFILES.get(doc_id)
    is_te = (language == LanguageCode.TE)

    title = profile["title_te"] if (profile and is_te) else (profile["title_en"] if profile else "")

    # 1. First priority: Extract verified evidence directly from retrieved chunks!
    if chunks:
        extracted = extract_bilingual_evidence_from_chunks(
            chunks=chunks,
            intent=intent,
            language=language,
            doc_id=doc_id,
        )
        if extracted and len(extracted.split()) >= 25:
            location_prefix = _build_location_prefix(title, state, district, is_te)
            resp = f"{location_prefix}{extracted}".strip()
            return sanitize_telugu_text(resp) if is_te else sanitize_english_text(resp)

    # 2. Fall back to audited SCHEME_PROFILES
    if not profile:
        return ""

    content = ""
    if intent == INTENT_COMPARISON and "comparison" in profile:
        content = profile["comparison"]["te"] if is_te else profile["comparison"]["en"]
    elif intent == INTENT_APPLICATION and "application" in profile:
        content = profile["application"]["te"] if is_te else profile["application"]["en"]
    elif intent == INTENT_DOCUMENTS and "documents" in profile:
        content = profile["documents"]["te"] if is_te else profile["documents"]["en"]
    elif intent == INTENT_ELIGIBILITY and "eligibility" in profile:
        content = profile["eligibility"]["te"] if is_te else profile["eligibility"]["en"]
    elif intent == INTENT_BENEFITS and "benefits" in profile:
        content = profile["benefits"]["te"] if is_te else profile["benefits"]["en"]
    elif intent == INTENT_OVERVIEW and "overview" in profile:
        content = profile["overview"]["te"] if is_te else profile["overview"]["en"]
    else:
        # Default fallback to overview + application brief
        if is_te:
            content = profile.get("overview", {}).get("te", "")
            if "application" in profile:
                app_brief = profile["application"]["te"]
                content = f"{content}\n\n{app_brief}"
        else:
            content = profile.get("overview", {}).get("en", "")
            if "application" in profile:
                app_brief = profile["application"]["en"]
                content = f"{content}\n\n{app_brief}"

    location_prefix = _build_location_prefix(title, state, district, is_te)
    final_resp = f"{location_prefix}{content}".strip()

    # Enforce strict language sanitization
    if not is_te:
        final_resp = sanitize_english_text(final_resp)
    else:
        final_resp = sanitize_telugu_text(final_resp)

    return final_resp
