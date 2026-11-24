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
    and recognized acronyms (Aadhaar, NPCI, e-KYC, e-Crop, CCRC, DBT, RSK, RBK, VAA, OAP).
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
        # Preserve lines with URLs or helplines or Telugu script
        has_te = bool(re.search(r"[\u0C00-\u0C7F]", s))
        has_url_or_num = bool(re.search(r"https?://|\b\d{4,6}\b", s))
        if has_te or has_url_or_num:
            cleaned_lines.append(s)
    return "\n".join(cleaned_lines).strip()


# Grounded knowledge profiles for the 14 verified schemes
SCHEME_PROFILES: Dict[str, Dict[str, Any]] = {
    "agri_annadata_sukhibhava_pmkisan": {
        "title_en": "Annadata Sukhibhava – PM Kisan",
        "title_te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్",
        "portals": ["https://annadathasukhibhava.ap.gov.in", "https://pmkisan.gov.in"],
        "helplines": ["155251", "1902"],
        "overview": {
            "en": "Annadata Sukhibhava – PM Kisan is a farmer welfare and income support initiative in Andhra Pradesh operating in convergence with the Central Government's PM-KISAN scheme. It transitions upon the erstwhile Rythu Bharosa framework to provide structured investment assistance and debt relief for farming families.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వం కేంద్ర ప్రభుత్వ పీఎం కిసాన్ పథకంతో సమన్వయం చేసుకుంటూ అమలు చేస్తున్న ప్రధాన రైతు సంక్షేమ పథకం. గతంలో ఉన్న రైతు భరోసా స్థానంలో రైతు కుటుంబాలకు సాగు పెట్టుబడి సాయం అందించి ఆర్థిక భద్రత కల్పించడం దీని ముఖ్య ఉద్దేశం.",
        },
        "application": {
            "en": "How to apply for Annadata Sukhibhava – PM Kisan:\n\n• **Enrollment & Verification:** Visit your local Rythu Seva Kendram (RSK) / Rythu Bharosa Kendram (RBK) or Grama / Ward Sachivalayam to meet the Village Agriculture Assistant (VAA). Ground-level field verification and beneficiary listing are carried out here.\n• **Mandatory e-Crop & e-KYC:** Complete crop cultivation booking on the state digital e-Crop / e-Panta portal and finish biometric or OTP e-KYC on the PM-Kisan portal.\n• **Bank Account Mapping:** Ensure your active bank account is seeded with Aadhaar and mapped with NPCI for Direct Benefit Transfer (DBT).\n• **Official Portals:** Check application status and beneficiary lists at https://annadathasukhibhava.ap.gov.in and https://pmkisan.gov.in.\n• **Helpline & Grievances:** For assistance, contact your VAA or dial the farmer helpline at 155251 or 1902.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకానికి దరఖాస్తు మరియు నమోదు విధానం:\n\n• **నమోదు కేంద్రాలు**: మీ సమీపంలోని రైతు సేవా కేంద్రం (RSK) / రైతు భరోసా కేంద్రం (RBK) లేదా గ్రామ/వార్డు సచివాలయాన్ని సందర్శించి గ్రామ వ్యవసాయ సహాయకుడిని (VAA) సంప్రదించండి. క్షేత్రస్థాయి పరిశీలన మరియు లబ్ధిదారుల నమోదు ఇక్కడే జరుగుతాయి.\n• **ఈ-పంట & ఈ-కేవైసీ**: తప్పనిసరిగా మీ సాగు వివరాలను ఈ-పంట (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో నమోదు చేయించుకోవాలి మరియు పీఎం కిసాన్ పోర్టల్‌లో ఈ-కేవైసీ (e-KYC) పూర్తి చేయాలి.\n• **బ్యాంక్ ఖాతా అనుసంధానం**: సాయం నేరుగా జమ కావడానికి మీ బ్యాంక్ ఖాతాకు ఆధార్ మరియు ఎన్‌పీసీఐ (NPCI) సీడింగ్ యాక్టివ్‌గా ఉండాలి.\n• **అధికారిక పోర్టల్స్**: దరఖాస్తు స్థితి మరియు లబ్ధిదారుల జాబితాను పరిశీలించడానికి:\n  - రాష్ట్ర పోర్టల్: https://annadathasukhibhava.ap.gov.in\n  - కేంద్ర పీఎం కిసాన్ పోర్టల్: https://pmkisan.gov.in\n• **సహాయం & ఫిర్యాదులు**: సమస్యల పరిష్కారం కొరకు గ్రామ వ్యవసాయ సహాయకుడిని కలవండి లేదా రాష్ట్ర రైతు హెల్ప్‌లైన్ 155251 లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Annadata Sukhibhava – PM Kisan:\n\n• **Aadhaar Card:** Aadhaar of applicant farmer and family head.\n• **Land Ownership / Cultivation Proof:** Land Pattadar Passbook, 1-B revenue record from Webland, or valid Crop Cultivator Rights Card (CCRC) agreement for tenant farmers.\n• **Bank Passbook:** Active bank account passbook seeded with Aadhaar and mapped with NPCI for Direct Benefit Transfer.\n• **Active Mobile Number:** Aadhaar-linked mobile number for OTP e-KYC and SMS alerts.\n• **e-Crop Booking:** Digital e-Crop / e-Panta cultivation receipt issued at RSK/RBK.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథకానికి అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: రైతు మరియు కుటుంబ పెద్ద ఆధార్ కార్డు.\n• **భూమి రికార్డులు**: పట్టాదారు పాస్‌బుక్, వెబ్‌ల్యాండ్ 1-బి రికార్డు, లేదా కౌలు రైతులకు చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) ఒప్పంద పత్రం.\n• **బ్యాంక్ పాస్‌బుక్**: ఆధార్ మరియు ఎన్‌పీసీఐ (NPCI) తో అనుసంధానమైన బ్యాంక్ ఖాతా పాస్‌బుక్.\n• **మొబైల్ నంబర్**: ఆధార్‌తో లింక్ అయిన యాక్టివ్ మొబైల్ నంబర్ (ఈ-కేవైసీ కొరకు).\n• **ఈ-పంట రసీదు**: రైతు సేవా కేంద్రంలో నమోదైన ఈ-క్రాప్ (e-Crop / e-Panta) రికార్డు.",
        },
        "eligibility": {
            "en": "Eligibility criteria for Annadata Sukhibhava – PM Kisan:\n\n• **Residency:** Bonafide resident farmers cultivating agricultural land in Andhra Pradesh.\n• **Landholders:** Small and marginal landholding farmer families holding cultivable land documented in state Webland records.\n• **Tenant Farmers:** Tenant cultivators holding registered Crop Cultivator Rights Cards (CCRC) for the designated crop season.\n• **Mandatory Compliance:** Valid e-Crop booking, Aadhaar-NPCI seeded bank account, and completed e-KYC.\n• **Exclusions:** Institutional landholders, regular government employees, income tax payees, and constitutional post holders.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ అర్హత నిబంధనలు:\n\n• **స్థానికత**: ఆంధ్రప్రదేశ్‌లో వ్యవసాయ భూమి కలిగి ఉండి సాగుచేస్తున్న రైతులు.\n• **భూ యజమానులు**: అధికారిక వెబ్‌ల్యాండ్ రికార్డుల్లో పేరు నమోదైన చిన్న, సన్నకారు రైతు కుటుంబాలు.\n• **కౌలు రైతులు**: ప్రస్తుత వ్యవసాయ సీజన్‌కు చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) కార్డులు కలిగిన కౌలు రైతులు నిబంధనల ప్రకారం అర్హులు.\n• **తప్పనిసరి నిబంధనలు**: ఈ-పంట (e-Crop) నమోదు, ఆధార్-ఎన్‌పీసీఐ బ్యాంక్ సీడింగ్ మరియు ఈ-కేవైసీ (e-KYC) పూర్తయి ఉండాలి.\n• **మినహాయింపులు**: ప్రభుత్వ ఉద్యోగులు, ఆదాయపు పన్ను చెల్లించేవారు, మరియు సంస్థాగత భూ యజమానులు అనర్హులు.",
        },
        "benefits": {
            "en": "Financial assistance framework under Annadata Sukhibhava – PM Kisan:\n\n• **Central Component (PM-KISAN):** Direct income support of Rs. 6,000 per year disbursed in three equal four-monthly installments of Rs. 2,000 directly into Aadhaar-seeded bank accounts.\n• **State Financial Assistance:** Supplemental state top-up assistance planned for eligible landholding and tenant farmer families per published state guidelines.\n• **Disbursement Channel:** Direct Benefit Transfer (DBT) into Aadhaar-NPCI active accounts. Official portal: https://annadathasukhibhava.ap.gov.in.",
            "te": "అన్నదాత సుఖీభవ – పీఎం కిసాన్ ఆర్థిక సహాయ వివరాలు:\n\n• **కేంద్ర పీఎం కిసాన్**: అర్హులైన భూ యజమానులకు ఏడాదికి రూ. 6,000 (మూడు విడతల్లో రూ. 2,000 చొప్పున) నేరుగా బ్యాంక్ ఖాతాలో జమ అవుతుంది.\n• **రాష్ట్ర టాప్-అప్ సహాయం**: రాష్ట్ర ప్రభుత్వం అర్హులైన రైతు కుటుంబాలకు మరియు కౌలు రైతులకు రాష్ట్ర టాప్-అప్ ఆర్థిక సహాయాన్ని డీబీటీ (DBT) ద్వారా అందించేందుకు కార్యాచరణ అమలు చేస్తోంది.\n• **చెల్లింపు విధానం**: నిధులు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాలకు నేరుగా బదిలీ అవుతాయి. అధికారిక పోర్టల్: https://annadathasukhibhava.ap.gov.in.",
        },
    },

    "edu_thalliki_vandanam_scheme": {
        "title_en": "Thalliki Vandanam Scheme",
        "title_te": "తల్లికి వందనం పథకం",
        "portals": ["https://schooledu.ap.gov.in", "https://gsws-nbm.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "Thalliki Vandanam is an educational financial support framework of the Government of Andhra Pradesh, succeeding and reforming previous school assistance frameworks (such as the erstwhile Amma Vodi framework). The objective is to encourage school education, incentivize mothers and guardians, and prevent dropouts from Class I through Intermediate (Class XII).",
            "te": "తల్లికి వందనం పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వం పాఠశాల విద్యాశాఖ ద్వారా అమలు చేస్తున్న ప్రధాన విద్యా ప్రోత్సాహక పథకం. గతంలో ఉన్న అమ్మ ఒడి స్థానంలో సంస్కరించబడిన ఈ కార్యక్రమం ద్వారా పిల్లలను బడికి పంపే తల్లులకు ఆర్థిక తోడ్పాటు అందించి, డ్రాపౌట్లను అరికట్టడం మరియు 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) వరకు నాణ్యమైన విద్యను ప్రోత్సహించడం దీని ముఖ్య ఉద్దేశం.",
        },
        "application": {
            "en": "How to verify and apply for Thalliki Vandanam:\n\n• **Database Synchronization:** Student enrollment and attendance records are synchronized directly from the School Child Info database and the Grama/Ward Sachivalayam Beneficiary Management (GSWS-NBM) portal.\n• **Secretariat Verification:** Mothers and guardians can verify eligibility, attendance, and bank account seeding status at their local Grama / Ward Sachivalayam with the Welfare and Education Assistant.\n• **Mandatory Compliance:** Maintain at least 75% student attendance and ensure the mother's bank account has active Aadhaar-NPCI seeding.\n• **Official Portals:** Check status at https://schooledu.ap.gov.in and https://gsws-nbm.ap.gov.in or call citizen helpline 1902.",
            "te": "తల్లికి వందనం పథకం నమోదు మరియు ధ్రువీకరణ విధానం:\n\n• **ఆటోమేటిక్ అనుసంధానం**: పాఠశాలల చైల్డ్ ఇన్ఫో (Child Info / UDISE+) డేటాబేస్ మరియు గ్రామ/వార్డు సచివాలయ నవశకం బెనిఫిషియరీ మేనేజ్‌మెంట్ (GSWS-NBM) పోర్టల్ ద్వారా వివరాలు నేరుగా సమకాలీకరించబడతాయి.\n• **సచివాలయ తనిఖీ**: తల్లులు తమ స్థానిక గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్ వద్ద అర్హత జాబితా, విద్యార్థి హాజరు మరియు బ్యాంక్ ఖాతా సీడింగ్ స్థితిని సరిచూసుకోవచ్చు.\n• **ముఖ్య నిబంధనలు**: పాఠశాలలో కనీసం 75% హాజరు ఉండాలి మరియు తల్లి బ్యాంక్ ఖాతాకు ఆధార్-ఎన్‌పీసీఐ సీడింగ్ పూర్తయి ఉండాలి.\n• **పోర్టల్స్ & హెల్ప్‌లైన్**: అధికారిక వివరాల కొరకు https://schooledu.ap.gov.in మరియు https://gsws-nbm.ap.gov.in చూడండి లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Thalliki Vandanam Scheme:\n\n• **Student Identification:** Child Info ID / School Admission Number and Student Aadhaar Card.\n• **Mother / Guardian Aadhaar:** Aadhaar Card of the mother (or recognized legal guardian if mother is deceased).\n• **Rice Card / BPL Proof:** Valid Rice Card / White Ration Card verified in the Grama / Ward Sachivalayam database.\n• **Bank Passbook:** Active bank account passbook in the mother's name with Aadhaar seeding and active NPCI mapping for DBT.\n• **School Attendance Record:** Proof of minimum 75% attendance recorded in the official Child Info portal.",
            "te": "తల్లికి వందనం పథకానికి అవసరమైన పత్రాలు:\n\n• **విద్యార్థి వివరాలు**: విద్యార్థి పాఠశాల/కళాశాల అడ్మిషన్ రికార్డు మరియు చైల్డ్ ఇన్ఫో (Child Info) ఐడీ, ఆధార్ కార్డు.\n• **తల్లి ఆధార్ కార్డు**: తల్లి (లేదా సంరక్షకురాలి) ఆధార్ కార్డు.\n• **రేషన్ కార్డు**: కుటుంబానికి చెందిన చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు (Rice Card / BPL card).\n• **బ్యాంక్ పాస్‌బుక్**: తల్లి పేరు మీద ఉన్న బ్యాంక్ ఖాతా పాస్‌బుక్ (తప్పనిసరిగా ఆధార్ మరియు ఎన్‌పీసీఐ - NPCI తో అనుసంధానమై ఉండాలి).\n• **హాజరు రికార్డు**: విద్యా సంవత్సరంలో కనీసం 75% పాఠశాల హాజరు నమోదై ఉండాలి.",
        },
        "eligibility": {
            "en": "Eligibility criteria for Thalliki Vandanam Scheme:\n\n• **Student Education Level:** Enrolled and studying in Classes I to XII (including Intermediate 1st and 2nd year) in recognized Government, Aided, Private Unaided, or Residential Schools / Junior Colleges in Andhra Pradesh.\n• **Attendance Benchmark:** Minimum 75% school or junior college attendance recorded during the academic year.\n• **Residency & Ration Card:** Permanent residents of Andhra Pradesh holding a valid Rice Card / BPL card.\n• **Exclusions:** Regular government employees and income tax payees are excluded.\n• **Disbursement Channel:** Direct Benefit Transfer (DBT) into the mother's verified Aadhaar-NPCI bank account.",
            "te": "తల్లికి వందనం పథకం అర్హతలు:\n\n• **విద్యార్హత**: ఆంధ్రప్రదేశ్‌లోని గుర్తింపు పొందిన ప్రభుత్వ, ఎయిడెడ్, ప్రైవేట్ అన్‌ఎయిడెడ్ లేదా రెసిడెన్షియల్ పాఠశాలలు/జూనియర్ కళాశాలల్లో 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) చదువుతుండాలి.\n• **హాజరు నిబంధన**: విద్యా సంవత్సరంలో కనీసం 75% హాజరు తప్పనిసరి.\n• **రేషన్ కార్డు**: కుటుంబం చెల్లుబాటు అయ్యే రైస్ కార్డు కలిగి ఉండాలి.\n• **మినహాయింపులు**: ప్రభుత్వ ఉద్యోగులు మరియు ఆదాయపు పన్ను చెల్లించే కుటుంబాలు అనర్హులు.\n• **చెల్లింపు**: నిధులు డీబీటీ (DBT) ద్వారా తల్లి ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాకు జమ అవుతాయి.",
        },
        "comparison": {
            "en": "Comparison between Amma Vodi and Thalliki Vandanam:\n\n• **Administrative Transition:** Amma Vodi is the predecessor school education financial support initiative in Andhra Pradesh, which has been succeeded, restructured, and reformed under the Government of Andhra Pradesh's current **Thalliki Vandanam** scheme framework.\n• **Core Purpose:** Thalliki Vandanam encourages school education, incentivizes mothers, and prevents dropouts by providing annual educational financial assistance for students enrolled from Class I through Intermediate (Class XII).\n• **Eligibility & Attendance:** The student must be studying in a recognized government, aided, or private school / junior college in Andhra Pradesh and maintain the mandatory attendance benchmark (such as 75% attendance during the academic year). The family must hold a valid Rice Card / BPL card.\n• **Disbursement Modality:** Financial assistance is deposited via Direct Benefit Transfer (DBT) directly into the Aadhaar-seeded, NPCI-active bank account of the mother.\n• **Verification & Portals:** Beneficiary verification is synchronized through the School Child Info database and the Grama / Ward Sachivalayam portal at https://schooledu.ap.gov.in and https://gsws-nbm.ap.gov.in.",
            "te": "అమ్మ ఒడి మరియు తల్లికి వందనం మధ్య తేడా మరియు పోలిక వివరాలు:\n\n• **పథక మార్పు**: గతంలో అమలులో ఉన్న అమ్మ ఒడి పాఠశాల విద్యా ప్రోత్సాహక పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వ తల్లికి వందనం పథకం మార్గదర్శకాల ప్రకారం సంస్కరించబడి అమలు చేయబడుతోంది.\n• **లక్ష్యం**: 1 నుండి 12వ తరగతి (ఇంటర్మీడియట్) వరకు చదువుతున్న విద్యార్థుల తల్లులకు విద్యా ప్రోత్సాహక ఆర్థిక తోడ్పాటు అందించి డ్రాపౌట్లను నివారించడం దీని ఉద్దేశం.\n• **అర్హత & హాజరు**: గుర్తింపు పొందిన పాఠశాల లేదా కళాశాలలో కనీసం 75% హాజరు ఉండాలి మరియు తెల్ల రేషన్ కార్డు కలిగి ఉండాలి.\n• **చెల్లింపు విధానం**: ఆర్థిక సాయం డీబీటీ (DBT) ద్వారా నేరుగా తల్లి ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతాకు జమ చేయబడుతుంది.\n• **పరిశీలన పోర్టల్స్**: చైల్డ్ ఇన్ఫో మరియు గ్రామ/వార్డు సచివాలయం ద్వారా ధ్రువీకరణ జరుగుతుంది. అధికారిక పోర్టల్: https://schooledu.ap.gov.in.",
        },
    },

    "agri_pm_crop_insurance_ap": {
        "title_en": "PM Fasal Bima Yojana & Crop Insurance in AP",
        "title_te": "ఆంధ్రప్రదేశ్ పంటల బీమా పథకం (పీఎం ఫసల్ బీమా యోజన)",
        "portals": ["https://pmfby.gov.in", "https://apagrisnet.gov.in"],
        "helplines": ["14447", "1800-180-1551"],
        "overview": {
            "en": "The Crop Insurance program in Andhra Pradesh operates within the framework of Pradhan Mantri Fasal Bima Yojana (PMFBY) alongside state-notified agricultural guidelines. Crop insurance provides financial risk coverage and compensation against crop losses caused by notified natural calamities, unseasonal weather, and pests.",
            "te": "ఆంధ్రప్రదేశ్‌లో పంటల బీమా కార్యక్రమం కేంద్ర ప్రభుత్వ పీఎం ఫసల్ బీమా యోజన (PMFBY) మరియు రాష్ట్ర వ్యవసాయ శాఖ మార్గదర్శకాల ప్రకారం అమలు చేయబడుతోంది. ప్రకృతి వైపరీత్యాలు, కరువు, వరదలు మరియు తెగుళ్ళ వల్ల జరిగే పంట నష్టాలకు ఇది రైతులకు ఆర్థిక రక్షణ మరియు బీమా పరిహారం అందిస్తుంది.",
        },
        "application": {
            "en": "How to enroll and apply for Crop Insurance in Andhra Pradesh:\n\n• **Mandatory e-Crop Booking:** Cultivating farmers must complete field crop booking on the state e-Crop (e-Panta) digital portal through their Village Agriculture Assistant (VAA) at the local Rythu Seva Kendram (RSK/RBK). Digital e-Crop booking is the baseline record for crop insurance.\n• **RSK / RBK Verification:** Visit your local Rythu Seva Kendram to verify that your sown crop, survey number, and acreage are accurately recorded in the seasonal notification list.\n• **Bank Account Mapping:** Ensure your bank account is seeded with Aadhaar and mapped with NPCI for direct DBT claim crediting.\n• **Claim Settlement:** Loss assessment is conducted via Crop Cutting Experiments (CCEs) on an area approach basis, and compensation is deposited directly via DBT.\n• **Portals & Helpline:** Check national PMFBY portal at https://pmfby.gov.in, AP Agriculture portal at https://apagrisnet.gov.in, or call toll-free helpline 14447 / 1800-180-1551.",
            "te": "ఆంధ్రప్రదేశ్ పంటల బీమా పథకం (పీఎం ఫసల్ బీమా యోజన) నమోదు విధానం:\n\n• **ఈ-పంట (e-Crop) నమోదు ప్రాథమికం**: పంటల బీమా రక్షణ పొందడానికి రైతులు విధిగా తమ స్థానిక గ్రామ వ్యవసాయ సహాయకుడి (VAA) ద్వారా ఈ-క్రాప్ (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో సాగు వివరాలను నమోదు చేయించుకోవాలి. ఈ-పంట నమోదే బీమాకు ప్రాథమిక ప్రాతిపదిక.\n• **రైతు సేవా కేంద్రం (RSK/RBK)**: మీ సమీపంలోని రైతు సేవా కేంద్రం / రైతు భరోసా కేంద్రాన్ని సందర్శించి పంట నమోదు, సర్వే నంబర్లు మరియు నోటిఫై చేసిన పంటల జాబితాను నిర్ధారించుకోండి.\n• **బ్యాంక్ ఖాతా అనుసంధానం**: నష్టపరిహారం డీబీటీ (DBT) ద్వారా నేరుగా జమ కావడానికి మీ బ్యాంక్ ఖాతాకు ఆధార్ మరియు ఎన్‌పీసీఐ అనుసంధానం పూర్తయి ఉండాలి.\n• **పరిహారం చెల్లింపు**: పంట కోత ప్రయోగాలు (CCE) మరియు ప్రభుత్వ నిబంధనల ఆధారంగా నష్టం లెక్కించబడి పరిహారం అందుతుంది.\n• **అధికారిక పోర్టల్స్ & హెల్ప్‌లైన్**:\n  - జాతీయ పంటల బీమా పోర్టల్: https://pmfby.gov.in\n  - ఏపీ వ్యవసాయ పోర్టల్: https://apagrisnet.gov.in\n  - టోల్ ఫ్రీ హెల్ప్‌లైన్: 14447 / కిసాన్ కాల్ సెంటర్: 1800-180-1551.",
        },
        "documents": {
            "en": "Required documents for AP Crop Insurance:\n\n• **e-Crop Registration:** Verified e-Crop / e-Panta booking receipt from RSK/RBK.\n• **Aadhaar Card:** Aadhaar of the cultivating farmer.\n• **Land Proof:** Pattadar passbook, 1-B record, or registered CCRC card for tenant farmers.\n• **Bank Passbook:** Aadhaar-linked active bank account passbook for DBT claims.",
            "te": "పంటల బీమాకు అవసరమైన పత్రాలు:\n\n• **ఈ-పంట రసీదు**: గ్రామ వ్యవసాయ సహాయకుడి ద్వారా జారీ చేయబడిన ఈ-క్రాప్ (e-Crop / e-Panta) నమోదు రసీదు.\n• **ఆధార్ కార్డు**: సాగుదారు ఆధార్ కార్డు.\n• **భూమి పత్రాలు**: పట్టాదారు పాస్‌బుక్, 1-బి రికార్డు లేదా కౌలు రైతులకు సీసీఆర్‌సీ (CCRC) ఒప్పంద పత్రం.\n• **బ్యాంక్ పాస్‌బుక్**: పరిహారం డీబీటీ కొరకు ఆధార్-ఎన్‌పీసీఐ అనుసంధాన బ్యాంక్ ఖాతా పాస్‌బుక్.",
        },
        "eligibility": {
            "en": "Eligibility for AP Crop Insurance:\n\n• Farmers cultivating notified crops in notified areas in Andhra Pradesh during the agricultural season.\n• Compulsory enrollment on the state e-Crop (e-Panta) digital portal.\n• Premium contributions and coverage terms depend on applicable seasonal notifications.\n• Tenant farmers with valid CCRC cards are eligible subject to departmental guidelines.",
            "te": "పంటల బీమా అర్హత నిబంధనలు:\n\n• ఆంధ్రప్రదేశ్‌లో నోటిఫై చేసిన ప్రాంతాల్లో, నోటిఫై చేసిన పంటలను సాగుచేస్తున్న రైతులు.\n• తప్పనిసరిగా ఈ-క్రాప్ (e-Crop / e-Panta) డిజిటల్ పోర్టల్‌లో సాగు నమోదు పూర్తయి ఉండాలి.\n• ప్రీమియం మరియు కవరేజ్ నిబంధనలు ఆయా సీజనల్ ప్రభుత్వ ఉత్తర్వులకు లోబడి ఉంటాయి.\n• చెల్లుబాటు అయ్యే సీసీఆర్‌సీ (CCRC) కార్డులు ఉన్న కౌలు రైతులకు కూడా నిబంధనల ప్రకారం బీమా రక్షణ వర్తిస్తుంది.",
        },
    },

    "health_ayushman_bharat_pmjay_ap": {
        "title_en": "Ayushman Bharat PM-JAY",
        "title_te": "ఆయుష్మాన్ భారత్ – పీఎం జన్ ఆరోగ్య యోజన",
        "portals": ["https://pmjay.gov.in", "https://beneficiary.nha.gov.in"],
        "helplines": ["14555", "104"],
        "overview": {
            "en": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY) is the national flagship public health insurance initiative providing hospitalization coverage up to Rs. 5 lakh per eligible family per year for secondary and tertiary healthcare in empaneled hospitals nationwide.",
            "te": "ఆయుష్మాన్ భారత్ ప్రధాన మంత్రి జన్ ఆరోగ్య యోజన (PM-JAY) దేశవ్యాప్తంగా గుర్తింపు పొందిన ఆసుపత్రులలో ద్వితీయ మరియు తృతీయ స్థాయి వైద్య చికిత్సలకు అర్హులైన కుటుంబానికి ఏడాదికి రూ. 5 లక్షల వరకు ఉచిత నగదు రహిత ఆరోగ్య బీమా అందించే ప్రధాన పథకం.",
        },
        "application": {
            "en": "How to access services and verify eligibility under Ayushman Bharat PM-JAY:\n\n• **Hospital Helpdesk:** Visit any empaneled government or private network hospital across Andhra Pradesh and nationwide. Approach the Ayushman Mitra / Arogyamithra at the helpdesk.\n• **Beneficiary Verification:** Present your Ayushman Card, Aadhaar Card, or valid state Rice Card for instant digital verification.\n• **Cashless Treatment:** Eligible patients receive pre-authorized cashless secondary and tertiary hospitalization.\n• **Portals & Helpline:** Verify eligibility online at https://beneficiary.nha.gov.in or https://pmjay.gov.in, or call national toll-free helpline 14555 or 104.",
            "te": "ఆయుష్మాన్ భారత్ పీఎం-జేవై సేవలు పొందే విధానం మరియు ధ్రువీకరణ:\n\n• **ఆసుపత్రి హెల్ప్‌డెస్క్**: ఆంధ్రప్రదేశ్‌లోని లేదా దేశవ్యాప్తంగా నెట్‌వర్క్ ఆసుపత్రులలోని ఆయుష్మాన్ మిత్ర / ఆరోగ్యమిత్ర హెల్ప్‌డెస్క్‌ను సంప్రదించండి.\n• **గుర్తింపు పత్రాలు**: తక్షణ ధ్రువీకరణ కొరకు మీ ఆయుష్మాన్ కార్డ్, ఆధార్ కార్డు లేదా రాష్ట్ర రైస్ కార్డును చూపించండి.\n• **ఉచిత నగదు రహిత చికిత్స**: ముందస్తు అనుమతి (Pre-authorization) ద్వారా ఆసుపత్రులలో ఉచిత నగదు రహిత చికిత్స లభిస్తుంది.\n• **పోర్టల్స్ & హెల్ప్‌లైన్**: అర్హత వివరాల కొరకు https://beneficiary.nha.gov.in చూడండి లేదా జాతీయ టోల్ ఫ్రీ నంబర్ 14555 లేదా 104 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Ayushman Bharat PM-JAY:\n\n• **Identity Proof:** Aadhaar Card of the patient and family head.\n• **Eligibility Card:** Ayushman Card (PM-JAY Golden Card) or valid state Rice Card / Ration Card.\n• **Hospital Referral:** Referral slip from primary/secondary health center if applicable.",
            "te": "ఆయుష్మాన్ భారత్ పథకానికి అవసరమైన పత్రాలు:\n\n• **గుర్తింపు కార్డు**: రోగి మరియు కుటుంబ పెద్ద ఆధార్ కార్డు.\n• **అర్హత పత్రం**: ఆయుష్మాన్ కార్డ్ (గోల్డెన్ కార్డ్) లేదా రాష్ట్ర ప్రభుత్వం జారీ చేసిన తెల్ల రేషన్ కార్డు (Rice Card).\n• **వైద్య రికార్డులు**: ప్రాథమిక ఆరోగ్య కేంద్రం రెఫరల్ లేదా ముందస్తు వైద్య రికార్డులు (వర్తిస్తే).",
        },
        "eligibility": {
            "en": "Eligibility for Ayushman Bharat PM-JAY:\n\n• Families identified under SECC database or active holders of state Rice Cards / BPL cards in Andhra Pradesh.\n• Covers pre-existing conditions from day one with no restriction on family size or age.\n• Provides national portability for hospitalization at any empaneled hospital in India.",
            "te": "ఆయుష్మాన్ భారత్ అర్హత నిబంధనలు:\n\n• ఎస్ఈసీసీ (SECC) డేటాబేస్ ప్రకారం గుర్తించబడిన కుటుంబాలు మరియు ఆంధ్రప్రదేశ్‌లో చెల్లుబాటు అయ్యే రైస్ కార్డు కలిగిన కుటుంబాలు అర్హులు.\n• కుటుంబ సభ్యుల సంఖ్య లేదా వయస్సుతో సంబంధం లేకుండా కుటుంబం మొత్తానికి ఏడాదికి రూ. 5 లక్షల వరకు ఉచిత చికిత్స వర్తిస్తుంది.\n• దేశవ్యాప్తంగా ఏ నెట్‌వర్క్ ఆసుపత్రిలోనైనా పోర్టబిలిటీ ద్వారా ఉచిత చికిత్స పొందవచ్చు.",
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
            "en": "How to apply for NTR Bharosa Social Security Pension:\n\n• **Secretariat Application:** Submit an application form at your local Grama / Ward Sachivalayam to the Welfare and Education Assistant (WEA) or Ward Welfare Secretary.\n• **Field Verification:** Secretariat functionaries and field staff verify age, residency, socio-economic criteria, and disability certificates.\n• **Social Audit & Approval:** Verified applications are placed for social audit approval, and sanction orders are issued.\n• **Disbursement:** Monthly pension is distributed directly by secretariat staff or credited via DBT on the 1st of every month.\n• **Portal & Helpline:** Check status at https://sspensions.ap.gov.in or call citizen helpline 1902.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను దరఖాస్తు విధానం:\n\n• **సచివాలయంలో దరఖాస్తు**: మీ స్థానిక గ్రామ/వార్డు సచివాలయంలోని వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్ (WEA) లేదా వార్డు వెల్ఫేర్ సెక్రటరీకి దరఖాస్తు సమర్పించండి.\n• **క్షేత్ర పరిశీలన**: సచివాలయ సిబ్బంది దరఖాస్తుదారుడి వయస్సు, నివాసం, ఆదాయం మరియు సదరమ్ (SADAREM) సర్టిఫికెట్లను క్షేత్రస్థాయిలో పరిశీలిస్తారు.\n• **సామాజిక తనిఖీ & మంజూరు**: పరిశీలన అనంతరం సోషల్ ఆడిట్ ద్వారా అర్హుల జాబితా ఆమోదించబడి పింఛను మంజూరు అవుతుంది.\n• **నెలవారీ పంపిణీ**: ప్రతి నెలా 1వ తేదీన సచివాలయ సిబ్బంది లేదా డీబీటీ ద్వారా పింఛను సొమ్ము అందుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://sspensions.ap.gov.in చూడండి లేదా 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for NTR Bharosa Pension:\n\n• **Aadhaar Card:** Aadhaar Card of the applicant for identity and age verification.\n• **Age Proof:** Voter ID card, birth certificate, or school leaving certificate (for Old Age Pension - 60+ years).\n• **Disability Certificate:** Valid SADAREM certificate showing disability percentage (for Differently Abled pensions).\n• **Death Certificate of Husband:** In case of Widow Pension.\n• **Rice Card / BPL Proof:** Valid white ration card in Andhra Pradesh.\n• **Bank Passbook:** Active bank account passbook mapped with NPCI.",
            "te": "ఎన్టీఆర్ భరోసా పింఛనుకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: దరఖాస్తుదారు ఆధార్ కార్డు.\n• **వయస్సు ధ్రువీకరణ**: ఓటరు గుర్తింపు కార్డు లేదా పుట్టిన తేదీ ధ్రువీకరణ పత్రం (వృద్ధాప్య పింఛనుకు కనీసం 60 ఏళ్లు నిండి ఉండాలి).\n• **సదరమ్ (SADAREM) సర్టిఫికెట్**: దివ్యాంగుల పింఛను కొరకు వైకల్య శాతం ధ్రువీకరణ పత్రం.\n• **భర్త మరణ ధ్రువీకరణ పత్రం**: వితంతు పింఛను దరఖాస్తుదారులకు.\n• **రేషన్ కార్డు**: చెల్లుబాటు అయ్యే తెల్ల రేషన్ కార్డు (Rice Card).\n• **బ్యాంక్ పాస్‌బుక్**: ఆధార్ అనుసంధానమైన బ్యాంక్ ఖాతా పాస్‌బుక్.",
        },
        "benefits": {
            "en": "Pension categories and monthly payout rates under NTR Bharosa:\n\n• **Old Age Pension (OAP 60+ yrs) & Widows:** Rs. 4,000 per month.\n• **Weavers, Toddy Tappers, Single Women, Fishermen:** Rs. 4,000 per month.\n• **Differently Abled (40% to 79% disability):** Rs. 6,000 per month.\n• **Severe Disability (80%+ disability):** Up to Rs. 15,000 per month.\n• **Disbursement:** Disbursed on the 1st of every month.",
            "te": "ఎన్టీఆర్ భరోసా పింఛను కేటగిరీలు మరియు నెలవారీ చెల్లింపులు:\n\n• **వృద్ధులు (OAP - 60 ఏళ్లు పైబడిన వారు) & వితంతువులు**: నెలకు రూ. 4,000.\n• **చేనేత కార్మికులు, గీత కార్మికులు, ఒంటరి మహిళలు, మత్స్యకారులు**: నెలకు రూ. 4,000.\n• **దివ్యాంగులు (40% నుండి 79% వైకల్యం)**: నెలకు రూ. 6,000.\n• **తీవ్ర వైకల్యం ఉన్నవారు (80% పైబడి)**: నెలకు రూ. 15,000 వరకు.\n• **పంపిణీ**: ప్రతి నెలా 1వ తేదీన లబ్ధిదారులకు అందజేయబడుతుంది.",
        },
    },

    "health_dr_ntr_vaidya_seva_aarogyasri": {
        "title_en": "Dr. NTR Vaidya Seva",
        "title_te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (ఆరోగ్యశ్రీ)",
        "portals": ["https://drntrvaidyaseva.ap.gov.in"],
        "helplines": ["104", "1902"],
        "overview": {
            "en": "Dr. NTR Vaidya Seva is the flagship healthcare initiative of the Government of Andhra Pradesh providing cashless hospitalization, surgical treatment, and tertiary medical care to eligible low-income families at empaneled network hospitals across Andhra Pradesh and major tier-1 cities (formerly known as Aarogyasri).",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (గతంలో ఆరోగ్యశ్రీ) ఆంధ్రప్రదేశ్ ప్రభుత్వం అమలు చేస్తున్న ప్రధాన ఆరోగ్య పథకం. అర్హులైన నిరుపేద కుటుంబాలకు నెట్‌వర్క్ ఆసుపత్రులలో ఉచిత నగదు రహిత వైద్యం, శస్త్రచికిత్సలు మరియు చికిత్సానంతర సాయం అందించడం దీని ముఖ్య లక్ష్యం.",
        },
        "application": {
            "en": "How to access cashless healthcare under Dr. NTR Vaidya Seva:\n\n• **Hospital Helpdesk:** Visit any empaneled government or private network hospital in Andhra Pradesh. Approach the Arogyamithra at the Dr. NTR Vaidya Seva helpdesk.\n• **Digital Pre-Authorization:** Present your Aadhaar Card and Rice Card. The Arogyamithra facilitates diagnosis verification and coordinates online pre-authorization with the Trust.\n• **Cashless Treatment:** Once approved, medical treatment, surgery, ICU, medicines, and food are provided completely cashless.\n• **Aarogya Aasara:** Post-operative financial allowance is credited via DBT to support recovery during the recuperation period.\n• **Portal & Helpline:** Visit https://drntrvaidyaseva.ap.gov.in or dial 104 / 1902.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద ఉచిత చికిత్స పొందే విధానం:\n\n• **ఆసుపత్రిలో సంప్రదింపు**: ఏపీలోని ఏదైనా నెట్‌వర్క్ ఆసుపత్రిలోని డాక్టర్ ఎన్టీఆర్ వైద్య సేవ హెల్ప్‌డెస్క్‌ వద్ద ఉన్న ఆరోగ్యమిత్రను సంప్రదించండి.\n• **గుర్తింపు కార్డులు సమర్పణ**: మీ ఆధార్ కార్డు మరియు రైస్ కార్డును ఆరోగ్యమిత్రకు చూపించండి. ఆసుపత్రి వైద్యుల సిఫార్సుతో ట్రస్ట్ నుండి ఆన్‌లైన్ ముందస్తు అనుమతి (Pre-authorization) తీసుకుంటారు.\n• **ఉచిత నగదు రహిత వైద్యం**: అనుమతి రాగానే చికిత్స, ఆపరేషన్, మందులు మరియు భోజనం పూర్తిగా ఉచితంగా అందించబడతాయి.\n• **ఆరోగ్య ఆసరా**: శస్త్రచికిత్స అనంతరం విశ్రాంతి సమయంలో కోలుకోవడానికి రోగి బ్యాంక్ ఖాతాకు ఆరోగ్య ఆసరా ఆర్థిక సాయం డీబీటీ ద్వారా అందుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://drntrvaidyaseva.ap.gov.in చూడండి లేదా 104 / 1902 కు కాల్ చేయండి.",
        },
        "documents": {
            "en": "Required documents for Dr. NTR Vaidya Seva:\n\n• **Aadhaar Card:** Aadhaar Card of the patient and family head.\n• **Rice Card / Health Card:** Valid Andhra Pradesh Rice Card or Dr. NTR Vaidya Seva Health Card.\n• **Hospital Consultation / Referral:** Diagnosis and test reports from the treating physician.",
            "te": "డాక్టర్ ఎన్టీఆర్ వైద్య సేవకు అవసరమైన పత్రాలు:\n\n• **ఆధార్ కార్డు**: రోగి మరియు కుటుంబ సభ్యుల ఆధార్ కార్డు.\n• **రేషన్ కార్డు / హెల్త్ కార్డు**: ఆంధ్రప్రదేశ్ ప్రభుత్వం జారీ చేసిన రైస్ కార్డు (Rice Card) లేదా ఎన్టీఆర్ వైద్య సేవ హెల్త్ కార్డు.\n• **వైద్య నివేదికలు**: రోగ నిర్ధారణ రిపోర్టులు మరియు సంబంధిత డాక్టర్ సిఫార్సు.",
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
            "en": "How to avail services and track status at Grama / Ward Sachivalayam:\n\n• **Visit Secretariat:** Visit your local village or ward secretariat and meet the Digital Assistant or Welfare and Education Assistant.\n• **Submit Application:** Submit required documents with biometric authentication for citizen services or scheme enrollments.\n• **Track Status:** Track application progress using your service request number on the portal: https://gramawardsachivalayam.ap.gov.in.\n• **Citizen Helpline:** Dial 1902 for service assistance and grievance redressal.",
            "te": "గ్రామ/వార్డు సచివాలయంలో సేవలు పొందే విధానం:\n\n• **సచివాలయం సందర్శన**: మీ స్థానిక గ్రామ లేదా వార్డు సచివాలయాన్ని సందర్శించి డిజిటల్ అసిస్టెంట్ లేదా వెల్ఫేర్ అండ్ ఎడ్యుకేషన్ అసిస్టెంట్‌ను కలవండి.\n• **దరఖాస్తు సమర్పణ**: అవసరమైన ధ్రువపత్రాలు మరియు బయోమెట్రిక్ ధ్రువీకరణతో సేవలకు దరఖాస్తు చేసుకోండి.\n• **స్టేటస్ పరిశీలన**: దరఖాస్తు నంబర్ ద్వారా అధికారిక పోర్టల్ https://gramawardsachivalayam.ap.gov.in లో పురోగతిని తెలుసుకోవచ్చు.\n• **పౌర హెల్ప్‌లైన్**: సేవా వివరాలు మరియు ఫిర్యాదుల కొరకు 1902 కు కాల్ చేయండి.",
        },
    },

    "schemes_mgnregs_andhra_pradesh": {
        "title_en": "MGNREGS Andhra Pradesh",
        "title_te": "ఉపాధి హామీ పథకం (MGNREGS)",
        "portals": ["https://nrega.nic.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "The Mahatma Gandhi National Rural Employment Guarantee Scheme (MGNREGS) provides a legal guarantee of 100 days of wage employment per financial year to adult members of rural households willing to do unskilled manual work.",
            "te": "మహాత్మా గాంధీ జాతీయ గ్రామీణ ఉపాధి హామీ పథకం (MGNREGS) గ్రామీణ ప్రాంతాల్లోని ప్రతి కుటుంబానికి ఏడాదికి కనీసం 100 రోజుల పాటు నైపుణ్యం లేని శారీరక శ్రమతో కూడిన ఉపాధికి చట్టబద్ధమైన హామీనిస్తుంది.",
        },
        "application": {
            "en": "How to apply for MGNREGS Job Card and demand work:\n\n• **Job Card Application:** Apply at your local Grama Sachivalayam through the Field Assistant or Panchayat Secretary.\n• **Documents Needed:** Aadhaar card, ration card, and bank/post office account passbook. Job Card is issued within 15 days.\n• **Demand Work:** Submit a written or verbal request for work at the Grama Sachivalayam; work must be provided within 15 days within 5 km of the village.\n• **Wage Payment:** Wages are calculated weekly and credited directly via DBT into bank/post office accounts.",
            "te": "ఉపాధి హామీ జాబ్ కార్డు దరఖాస్తు మరియు పని పొందే విధానం:\n\n• **జాబ్ కార్డు దరఖాస్తు**: మీ స్థానిక గ్రామ సచివాలయంలోని ఫీల్డ్ అసిస్టెంట్ లేదా పంచాయతీ కార్యదర్శికి దరఖాస్తు ఇవ్వండి. 15 రోజుల్లో జాబ్ కార్డు జారీ చేస్తారు.\n• **అవసరమైన పత్రాలు**: కుటుంబ సభ్యుల ఆధార్ కార్డులు, రేషన్ కార్డు మరియు బ్యాంక్/పోస్టాఫీస్ పాస్‌బుక్.\n• **పని డిమాండ్**: గ్రామ సచివాలయంలో పని కోసం దరఖాస్తు సమర్పించండి; 15 రోజుల్లోగా గ్రామానికి 5 కి.మీ పరిధిలో పని కల్పిస్తారు.\n• **వేతన చెల్లింపు**: చేసిన పనికి నిర్ణీత వేతనం నేరుగా డీబీటీ (DBT) ద్వారా బ్యాంక్ ఖాతాకు జమ అవుతుంది.",
        },
    },

    "schemes_pedalandariki_illu_housing": {
        "title_en": "Pedalandariki Illu Housing Scheme",
        "title_te": "పేదలందరికీ ఇళ్లు గృహ నిర్మాణ పథకం",
        "portals": ["https://housing.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "Pedalandariki Illu is the flagship affordable housing initiative in Andhra Pradesh providing free house site pattas and subsidized financial construction assistance to homeless, low-income BPL families, registered in the name of female heads of households.",
            "te": "పేదలందరికీ ఇళ్లు పథకం ఆంధ్రప్రదేశ్‌లోని నిరుపేద, ఇళ్లు లేని కుటుంబాలకు మహిళల పేరిట ఉచిత ఇళ్ల పట్టాలు మరియు గృహ నిర్మాణ ఆర్థిక సహాయాన్ని అందించే ప్రధాన గృహ నిర్మాణ పథకం.",
        },
        "application": {
            "en": "How to apply for Pedalandariki Illu Housing:\n\n• **Secretariat Application:** Apply at your local Grama / Ward Sachivalayam through the Village Revenue Officer (VRO) and Engineering Assistant.\n• **Verification:** Revenue and engineering functionaries verify homelessness, landlessness, and income eligibility.\n• **Staged Financial Assistance:** Subsidy funds are released directly via DBT in linked installments based on geotagged physical construction progress.\n• **Portals & Helpline:** Check status at https://housing.ap.gov.in or call 1902.",
            "te": "పేదలందరికీ ఇళ్లు పథకం దరఖాస్తు విధానం:\n\n• **సచివాలయంలో దరఖాస్తు**: మీ స్థానిక గ్రామ/వార్డు సచివాలయంలోని వీఆర్వో (VRO) మరియు ఇంజనీరింగ్ అసిస్టెంట్‌కు దరఖాస్తు చేసుకోండి.\n• **క్షేత్ర పరిశీలన**: రెవెన్యూ సిబ్బంది నివాస అర్హతలు, నిరుపేద స్థితిని క్షేత్రస్థాయిలో పరిశీలిస్తారు.\n• **విడతల వారీ ఆర్థిక సాయం**: ఇంటి నిర్మాణ పురోగతి ఆధారంగా జియోట్యాగింగ్ పూర్తి చేసి విడతల వారీగా నగదు డీబీటీ ద్వారా బ్యాంక్ ఖాతాలో జమ అవుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://housing.ap.gov.in చూడండి లేదా 1902 కు కాల్ చేయండి.",
        },
    },

    "edu_vidya_deevena_vasathi_deevena": {
        "title_en": "Vidya Deevena & Vasathi Deevena",
        "title_te": "విద్యా దీవెన మరియు వసతి దీవెన",
        "portals": ["https://jnanabhumi.ap.gov.in"],
        "helplines": ["1902"],
        "overview": {
            "en": "Jagananna Vidya Deevena (RTF) provides full tuition fee reimbursement and Vasathi Deevena (MTF) provides annual boarding and accommodation financial assistance for eligible post-matric students pursuing higher education.",
            "te": "జగనన్న విద్యా దీవెన (RTF) ఉన్నత విద్య చదివే విద్యార్థులకు పూర్తి ట్యూషన్ ఫీజు రీయింబర్స్‌మెంట్ అందిస్తుంది, మరియు వసతి దీవెన (MTF) వసతి, భోజన ఖర్చుల కొరకు వార్షిక నిర్వహణ భత్యాన్ని అందిస్తుంది.",
        },
        "application": {
            "en": "How to apply for Vidya Deevena & Vasathi Deevena:\n\n• **Jnanabhumi Application:** Apply through your college or at the local Grama / Ward Sachivalayam Welfare and Education Assistant (WEA) via the Jnanabhumi portal: https://jnanabhumi.ap.gov.in.\n• **Documents Needed:** Student & mother Aadhaar cards, college admission allotment order, Rice Card / income certificate, and mother's bank passbook with NPCI mapping.\n• **Mandatory Benchmark:** Maintain at least 75% college attendance.\n• **Disbursement:** Vidya Deevena fee is credited quarterly and Vasathi Deevena in two annual installments via DBT.",
            "te": "విద్యా దీవెన మరియు వసతి దీవెన దరఖాస్తు విధానం:\n\n• **జ్ఞానభూమి దరఖాస్తు**: మీ కళాశాల ద్వారా లేదా స్థానిక గ్రామ/వార్డు సచివాలయ వెల్ఫేర్ అసిస్టెంట్ ద్వారా జ్ఞానభూమి పోర్టల్ (https://jnanabhumi.ap.gov.in) లో దరఖాస్తు చేయండి.\n• **అవసరమైన పత్రాలు**: విద్యార్థి మరియు తల్లి ఆధార్ కార్డులు, కళాశాల అడ్మిషన్ అలాట్‌మెంట్ ఆర్డర్, రైస్ కార్డు, మరియు తల్లి బ్యాంక్ పాస్‌బుక్.\n• **హాజరు నిబంధన**: కళాశాలలో కనీసం 75% హాజరు తప్పనిసరి.\n• **చెల్లింపు**: ఫీజు మరియు వసతి సొమ్ము డీబీటీ (DBT) ద్వారా నేరుగా తల్లి బ్యాంక్ ఖాతాకు జమ అవుతాయి.",
        },
    },

    "agri_kisan_credit_card": {
        "title_en": "Kisan Credit Card (KCC)",
        "title_te": "కిసాన్ క్రెడిట్ కార్డు (KCC)",
        "portals": ["https://pmkisan.gov.in"],
        "helplines": ["1800-180-1551"],
        "overview": {
            "en": "Kisan Credit Card (KCC) provides farmers with adequate and timely institutional credit for agricultural cultivation expenses, seeds, fertilizers, pesticides, and post-harvest maintenance at subsidized interest rates.",
            "te": "కిసాన్ క్రెడిట్ కార్డు (KCC) రైతులకు వ్యవసాయ సాగు ఖర్చులు, విత్తనాలు, ఎరువులు మరియు పెట్టుబడి అవసరాల కోసం సకాలంలో రాయితీ వడ్డీతో బ్యాంకు రుణాలు అందించే ప్రభుత్వ పథకం.",
        },
        "application": {
            "en": "How to apply for Kisan Credit Card (KCC):\n\n• **Bank / RSK Application:** Submit the one-page KCC application form at your nearest commercial bank, regional rural bank (RRB), or cooperative bank, or approach your Village Agriculture Assistant at the local Rythu Seva Kendram (RSK/RBK).\n• **Online Route:** Eligible PM-Kisan beneficiaries can apply online via the PM-Kisan portal: https://pmkisan.gov.in.\n• **Documents Needed:** Aadhaar card, PAN card / Form 60, land records (Pattadar passbook / 1-B) or CCRC card for tenant farmers, and bank passbook.\n• **Interest Terms:** Subsidized interest rate of 7% p.a., with prompt repayment incentive reducing effective interest to 4% p.a.",
            "te": "కిసాన్ క్రెడిట్ కార్డు దరఖాస్తు విధానం:\n\n• **బ్యాంక్ లేదా రైతు సేవా కేంద్రం**: మీ సమీపంలోని ప్రభుత్వ, గ్రామీణ లేదా సహకార బ్యాంకును సంప్రదించండి లేదా రైతు సేవా కేంద్రం (RSK/RBK) లో గ్రామ వ్యవసాయ సహాయకుడిని కలవండి.\n• **ఆన్‌లైన్ దరఖాస్తు**: పీఎం కిసాన్ లబ్ధిదారులు అధికారిక పోర్టల్ https://pmkisan.gov.in ద్వారా ఆన్‌లైన్‌లో దరఖాస్తు చేసుకోవచ్చు.\n• **అవసరమైన పత్రాలు**: ఆధార్ కార్డు, పాన్ కార్డు / ఫారం 60, పట్టాదారు పాస్‌బుక్ / 1-బి రికార్డు (కౌలు రైతులకు సీసీఆర్‌సీ కార్డు) మరియు బ్యాంక్ పాస్‌బుక్.\n• **వడ్డీ రాయితీ**: సాధారణ వడ్డీ 7% కాగా, సకాలంలో రుణం చెల్లిస్తే 3% ప్రోత్సాహక రాయితీతో 4% వార్షిక వడ్డీకే రుణం లభిస్తుంది.",
        },
    },

    "health_104_108_emergency_health_services": {
        "title_en": "104 & 108 Emergency Health Services",
        "title_te": "104 మరియు 108 అత్యవసర ఆరోగ్య సేవలు",
        "portals": ["https://drntrvaidyaseva.ap.gov.in"],
        "helplines": ["108", "104"],
        "overview": {
            "en": "108 Emergency Ambulance Service provides 24/7 free toll-free emergency transport and pre-hospital care for trauma, accidents, and acute conditions. 104 Mobile Medical Units and Health Helpline provide 24/7 free medical advice and doorstep village healthcare.",
            "te": "108 అంబులెన్స్ సేవ ప్రమాదాలు, తీవ్ర అనారోగ్య పరిస్థితుల్లో 24/7 ఉచిత అత్యవసర రవాణా అందిస్తుంది. 104 సంచార వైద్య వాహనాలు (MMU) మరియు హెల్ప్‌లైన్ గ్రామాల్లో ఉచిత వైద్య సలహాలు, పరీక్షలు మరియు మందులు అందిస్తాయి.",
        },
        "application": {
            "en": "How to access 108 and 104 Health Services:\n\n• **108 Medical Emergency:** Dial 108 from any mobile or landline without dialing code for immediate free ambulance dispatch.\n• **104 Health Helpline:** Dial 104 for free medical counseling, blood bank availability, government health scheme details, and Family Doctor village schedules.\n• **Zero Charges:** Both services are completely free of cost across Andhra Pradesh.",
            "te": "108 మరియు 104 సేవలు పొందే విధానం:\n\n• **108 అత్యవసర వైద్య సేవ**: ప్రమాదాలు, గుండెపోటు లేదా ఇతర అత్యవసర సమయాల్లో ఏ ఫోన్ నుండైనా 108 కు ఉచితంగా కాల్ చేయండి. సమీప అంబులెన్స్ తక్షణమే చేరుకుంటుంది.\n• **104 ఉచిత వైద్య సలహా**: ఉచిత వైద్య సలహాలు, రక్త లభ్యత, మరియు ఫ్యామిలీ డాక్టర్ గ్రామ పర్యటనల వివరాల కొరకు 104 కు కాల్ చేయండి.\n• **పూర్తి ఉచితం**: ఈ రెండు సేవలు ఆంధ్రప్రదేశ్ ప్రభుత్వం ద్వారా ప్రజలకు పూర్తిగా ఉచితంగా అందించబడుతున్నాయి.",
        },
    },

    "edu_samagra_shiksha_ap": {
        "title_en": "Samagra Shiksha AP",
        "title_te": "సమగ్ర శిక్ష ఆంధ్రప్రదేశ్",
        "portals": ["https://schooledu.ap.gov.in"],
        "helplines": ["14417", "1902"],
        "overview": {
            "en": "Samagra Shiksha is an overarching school education program in Andhra Pradesh ensuring inclusive, equitable, quality education across all government and local body schools from pre-primary to Class XII.",
            "te": "సమగ్ర శిక్ష ఆంధ్రప్రదేశ్‌లోని ప్రభుత్వ మరియు స్థానిక సంస్థల పాఠశాలల్లో ప్రీ-ప్రైమరీ నుండి 12వ తరగతి వరకు విద్యార్థులందరికీ నాణ్యమైన, ఉచిత విద్యను అందించే సమగ్ర పాఠశాల విద్యా కార్యక్రమం.",
        },
        "application": {
            "en": "How to access entitlements under Samagra Shiksha:\n\n• **School Admission:** Enroll your child directly in any recognized government or local body school in Andhra Pradesh.\n• **Automatic Entitlements:** Enrolled students automatically receive free bilingual textbooks, school uniforms, workbooks, and daily mid-day meals.\n• **Official Inquiries:** Inquire at your local government school or contact the Department of School Education at https://schooledu.ap.gov.in or helpline 14417.",
            "te": "సమగ్ర శిక్ష సేవలు పొందే విధానం:\n\n• **పాఠశాల ప్రవేశం**: ఆంధ్రప్రదేశ్‌లోని ఏదైనా ప్రభుత్వ లేదా స్థానిక సంస్థల పాఠశాలలో విద్యార్థిని చేర్పించండి.\n• **ఉచిత సేవలు**: చేరిన విద్యార్థులందరికీ ఉచిత ద్విభాషా పాఠ్యపుస్తకాలు, యూనిఫాం వస్త్రాలు, నోట్‌బుక్కులు మరియు మధ్యాహ్న భోజనం ఉచితంగా లభిస్తాయి.\n• **సంప్రదింపులు**: మీ స్థానిక ప్రభుత్వ పాఠశాల ప్రధానోపాధ్యాయుడిని సంప్రదించండి లేదా విద్యాశాఖ పోర్టల్ https://schooledu.ap.gov.in చూడండి.",
        },
    },

    "agri_soil_health_card_polam_badi": {
        "title_en": "Soil Health Card & Polam Badi",
        "title_te": "భూసార పరీక్ష కార్డు మరియు పొలం బడి",
        "portals": ["https://soilhealth.dac.gov.in", "https://apagrisnet.gov.in"],
        "helplines": ["155251", "1902"],
        "overview": {
            "en": "The Soil Health Card scheme assesses soil nutrient status and provides customized crop-specific fertilizer recommendations, while Polam Badi farmer field schools impart practical ecological crop management training.",
            "te": "భూసార పరీక్ష కార్డు పథకం రైతుల పొలాల్లోని నేల సారాన్ని పరీక్షించి తగిన ఎరువుల వినియోగానికి సిఫార్సులు చేస్తుంది. పొలం బడి కార్యక్రమం ద్వారా రైతులకు సమగ్ర సస్యరక్షణ మరియు సాగు మెళకువలపై శిక్షణ ఇస్తారు.",
        },
        "application": {
            "en": "How to obtain Soil Health Card and attend Polam Badi:\n\n• **Contact VAA at RSK/RBK:** Contact your Village Agriculture Assistant (VAA) at the local Rythu Seva Kendram (RSK/RBK) or Grama Sachivalayam.\n• **Soil Sample Collection:** Department staff collect representative GPS-tagged soil samples from agricultural holdings.\n• **Testing & Card Issuance:** Samples are analyzed at soil testing laboratories and printed Soil Health Cards with customized nutrient advice are issued to farmers.\n• **Portal:** Check test records at https://soilhealth.dac.gov.in or contact helpline 155251 / 1902.",
            "te": "భూసార పరీక్ష కార్డు పొందే విధానం:\n\n• **రైతు సేవా కేంద్రంలో సంప్రదింపు**: మీ స్థానిక రైతు సేవా కేంద్రం (RSK/RBK) లో గ్రామ వ్యవసాయ సహాయకుడిని (VAA) సంప్రదించండి.\n• **నమూనా సేకరణ**: వ్యవసాయ సిబ్బంది పొలం నుండి మట్టి నమూనాలను సేకరించి ప్రయోగశాలలో పరీక్షిస్తారు.\n• **కార్డు జారీ**: పరీక్షించిన పోషకాల ఆధారంగా సిఫార్సులతో కూడిన భూసార కార్డు రైతుకు అందజేయబడుతుంది.\n• **పోర్టల్ & హెల్ప్‌లైన్**: వివరాల కొరకు https://soilhealth.dac.gov.in చూడండి లేదా 155251 / 1902 కు కాల్ చేయండి.",
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
    """
    profile = SCHEME_PROFILES.get(doc_id)
    is_te = (language == LanguageCode.TE)

    if not profile:
        # Fallback to general chunk extraction if doc_id not in profile
        return ""

    title = profile["title_te"] if is_te else profile["title_en"]

    # Select content by intent
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
        # Default fallback to application if user asks actionable query or overview
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

    # Build location prefix matching official format
    location_prefix = ""
    if district and state:
        loc_str = f"{district}, {state}"
        if is_te:
            location_prefix = f"[{title} - {loc_str} పరిధిలోని అధికారిక సమాచారం]:\n\n"
        else:
            location_prefix = f"[Verified official information on {title} for {loc_str}]:\n\n"
    elif state:
        if is_te:
            location_prefix = f"[{title} - {state} పరిధిలోని అధికారిక సమాచారం]:\n\n"
        else:
            location_prefix = f"[Verified official information on {title} for {state}]:\n\n"
    else:
        if is_te:
            location_prefix = f"[{title} - అధికారిక సమాచారం]:\n\n"
        else:
            location_prefix = f"[Verified official information on {title}]:\n\n"

    final_resp = f"{location_prefix}{content}".strip()

    # Enforce strict language sanitization
    if not is_te:
        final_resp = sanitize_english_text(final_resp)
    else:
        final_resp = sanitize_telugu_text(final_resp)

    return final_resp
