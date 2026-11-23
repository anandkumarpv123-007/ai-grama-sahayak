import re
from typing import Any, Dict, List, Optional
from app.schemas.common import LanguageCode

# Detailed clarification responses when citizen asks about "the scheme" without specifying which one
SCHEME_CLARIFICATION_DATA: Dict[str, Dict[str, Any]] = {
    "en": {
        "answer": (
            "There are several government welfare schemes available in Andhra Pradesh across different sectors. "
            "Please specify which scheme or sector you would like information about:\n\n"
            "• Social Security Pensions: NTR Bharosa\n"
            "• Agriculture & Farmer Support: Annadata Sukhibhava – PM KISAN\n"
            "• Healthcare: Dr. NTR Vaidya Seva\n"
            "• Education: Thalliki Vandanam\n"
            "• Food Security & Civil Supplies: Ration Card Services\n"
            "• Housing Assistance\n\n"
            "Please reply with the scheme name or category of interest to receive verified information."
        ),
        "follow_up_questions": [
            "Would you like details on Social Security Pensions (NTR Bharosa)?",
            "Would you like details on Farmer Support (Annadata Sukhibhava – PM KISAN)?",
            "Would you like details on Healthcare assistance (Dr. NTR Vaidya Seva)?",
        ],
        "safety_notice": (
            "Public Schemes Advisory: Welfare scheme eligibility thresholds, required documentation, and benefit "
            "disbursements are subject to official government guidelines and periodic beneficiary verification. "
            "Always submit applications directly through your local Grama / Ward Sachivalayam or official government portals. "
            "Never pay money to unauthorized intermediaries."
        ),
    },
    "te": {
        "answer": (
            "ఆంధ్రప్రదేశ్‌లో వివిధ వర్గాల ప్రజల కోసం పలు ప్రభుత్వ సంక్షేమ పథకాలు అమలులో ఉన్నాయి. "
            "మీరు ఏ పథకం లేదా రంగానికి సంబంధించిన సమాచారం కోరుకుంటున్నారో దయచేసి స్పష్టం చేయగలరా?\n\n"
            "• సామాజిక భద్రత పింఛన్లు: ఎన్టీఆర్ భరోసా\n"
            "• వ్యవసాయం & రైతు సహాయం: అన్నదాత సుఖీభవ – పీఎం కిసాన్\n"
            "• వైద్యం & ఆరోగ్యం: డా. ఎన్టీఆర్ వైద్య సేవ\n"
            "• విద్య & విద్యార్థి సహాయం: తల్లికి వందనం\n"
            "• ఆహార భద్రత: రేషన్ కార్డు సేవలు\n"
            "• గృహ నిర్మాణం\n\n"
            "మీకు కావలసిన పథకం పేరు లేదా విభాగాన్ని తెలిపితే, దానికి సంబంధించిన ధృవీకరించిన సమాచారాన్ని తెలియజేస్తాను."
        ),
        "follow_up_questions": [
            "ఎన్టీఆర్ భరోసా పింఛన్ వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
            "అన్నదాత సుఖీభవ – పీఎం కిసాన్ వివరాలు కావాలా?",
            "డా. ఎన్టీఆర్ వైద్య సేవ పథకం వివరాలు కావాలా?",
        ],
        "safety_notice": (
            "పథకాల సలహా: ప్రభుత్వ సంక్షేమ పథకాల మార్గదర్శకాలు, ఆదాయ పరిమితులు మరియు లబ్ధిదారుల ఎంపిక నిబంధనలు "
            "ప్రభుత్వ జీవోలకు (GOs) లోబడి ఉంటాయి. దరఖాస్తును మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో మాత్రమే సమర్పించండి. "
            "మధ్యవర్తులను నమ్మవద్దు."
        ),
    },
}

# Specific scheme tokens and names across English and Telugu.
# If a query contains ANY of these, it is specific and should proceed with normal retrieval.
SPECIFIC_SCHEME_PATTERNS: List[re.Pattern] = [
    # Pensions
    re.compile(r"\b(?:pension|oap|widow|disabled|disability|kanuka|ntr\s*bharosa|bharosa|ysr\s*pension)\b", re.IGNORECASE),
    re.compile(r"పింఛన్|పెన్షన్|కానుక|వృద్ధాప్య|వితంతు|దివ్యాంగుల|ఎన్టీఆర్\s*భరోసా|భరోసా"),
    # Agriculture
    re.compile(r"\b(?:annadata|sukhibhava|rythu|pm-?kisan|kisan|crop\s*loan|crop\s*insurance|fasal\s*bima|kcc|kisan\s*credit\s*card|e-?panta|sunna\s*vaddi|seed\s*subsidy|fertilizer\s*subsidy)\b", re.IGNORECASE),
    re.compile(r"అన్నదాత|సుఖీభవ|రైతు|పీఎం\s*కిసాన్|కిసాన్|పంటల\s*బీమా|ఈ-?పంట|సున్నా\s*వడ్డీ|పంట\s*రుణం"),
    # Healthcare
    re.compile(r"\b(?:vaidya\s*seva|dr\s*ntr|aarogyasri|ayushman|pm-?jay|aarogya|asara|phc|chc|health\s*card|108|104|ambulance)\b", re.IGNORECASE),
    re.compile(r"వైద్య\s*సేవ|ఎన్టీఆర్|ఆరోగ్యశ్రీ|ఆయుష్మాన్|ఆరోగ్య\s*ఆసరా|ఆరోగ్యం|అంబులెన్స్"),
    # Education
    re.compile(r"\b(?:thalliki\s*vandanam|vandanam|amma\s*vodi|vidya\s*deevena|vasathi\s*deevena|jnanabhumi|scholarship|fee\s*reimbursement|hostel\s*fee)\b", re.IGNORECASE),
    re.compile(r"తల్లికి\s*వందనం|వందనం|అమ్మ\s*ఒడి|విద్యా\s*దీవెన|వసతి\s*దీవెన|జ్ఞానభూమి|స్కాలర్\u200c?షిప్|ఫీజు|విద్యార్థి"),
    # Women & Livelihood
    re.compile(r"\b(?:cheyutha|aasara|kapu\s*nestham|vahana\s*mitra|nethanna|chedodu|matsyakara|dwakra|dwcra|shg)\b", re.IGNORECASE),
    re.compile(r"చేయూత|ఆసరా|కాపు\s*నేస్తం|వాహన\s*మిత్ర|నేతన్న|చేదోడు|మత్స్యకార|డ్వాక్రా"),
    # Housing & Civil Supplies
    re.compile(r"\b(?:pedalandariki\s*illu|housing|house\s*site|patta|rice\s*card|ration\s*card|ysr\s*bima)\b", re.IGNORECASE),
    re.compile(r"గృహ|గృహ\s*నిర్మాణం|ఇల్లు|ఇళ్లు|ఇళ్ల\s*పట్టా|పేదలందరికీ\s*ఇళ్లు|రేషన్\s*కార్డు|బియ్యం\s*కార్డు|వైఎస్సార్\s*బీమా|రేషన్"),
    # Employment & Sachivalayam Services
    re.compile(r"\b(?:mgnregs|nrega|mgnrega|employment\s*guarantee|wage\s*employment|100\s*days|sachivalayam|grama\s*sachivalayam|ward\s*sachivalayam)\b", re.IGNORECASE),
    re.compile(r"ఉపాధి\s*హామీ|సచివాలయం|గ్రామ\s*సచివాలయం|వార్డు\s*సచివాలయం"),
]

# Generic/Ambiguous scheme patterns that indicate the user is asking about "the scheme" without naming one.
# Evaluated ONLY when no specific scheme from SPECIFIC_SCHEME_PATTERNS is mentioned.
AMBIGUOUS_SCHEME_PATTERNS: List[re.Pattern] = [
    # English: Determiner / preposition phrases ("the scheme", "this scheme", "for the scheme", etc.)
    re.compile(r"\b(?:the|this|that|a|any|which|all|our|govt|government|welfare|state|social)\s+schemes?\b", re.IGNORECASE),
    re.compile(r"\b(?:for|under|in|of|to|about|regarding)\s+(?:the|this|that|a|any|govt|government|welfare|state)?\s*schemes?\b", re.IGNORECASE),

    # English: Semantic aspect queries mentioning generic scheme(s)
    # Documents / certificates / paperwork
    re.compile(r"\b(?:documents?|documentation|paperwork|papers?|certificates?|proofs?|records?)\b.*\b(?:schemes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:schemes?)\b.*\b(?:documents?|documentation|paperwork|papers?|certificates?|proofs?|records?)\b", re.IGNORECASE),
    # Eligibility / criteria / rules / age / income limit
    re.compile(r"\b(?:eligibility|eligible|criteria|rules?|qualify|qualification|age\s+limit|income\s+limit|conditions?)\b.*\b(?:schemes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:schemes?)\b.*\b(?:eligibility|eligible|criteria|rules?|qualify|qualification|age\s+limit|income\s+limit|conditions?)\b", re.IGNORECASE),
    # Benefits / money / amount / assistance
    re.compile(r"\b(?:benefits?|assistance|amount|money|funds?|grant|payout|financial\s+aid|financial\s+assistance)\b.*\b(?:schemes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:schemes?)\b.*\b(?:benefits?|assistance|amount|money|funds?|grant|payout|financial\s+aid|financial\s+assistance)\b", re.IGNORECASE),
    # Application / registration / submission / form / portal
    re.compile(r"\b(?:apply|application|register|registration|enroll|enrollment|submit|procedure|process|status|form|portal)\b.*\b(?:schemes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:schemes?)\b.*\b(?:apply|application|register|registration|enroll|enrollment|submit|procedure|process|status|form|portal)\b", re.IGNORECASE),
    # Details / info / overview / explain
    re.compile(r"\b(?:details|information|info|about|explain|tell\s+me|know\s+about|guidelines?)\b.*\b(?:schemes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:schemes?)\b.*\b(?:details|information|info|guidelines?)\b", re.IGNORECASE),
    # Listing / options / questions
    re.compile(r"\b(?:which\s+scheme|what\s+schemes?|list\s+(?:of\s+)?schemes?|how\s+many\s+schemes?)\b", re.IGNORECASE),
    re.compile(r"^(?:the\s+)?(?:govt\s+|government\s+|welfare\s+|state\s+)?schemes?[?!.]*$", re.IGNORECASE),

    # Telugu: Determiner phrases ("ఆ పథకం", "ఈ పథకం", "ప్రభుత్వ పథకం", etc.)
    re.compile(r"(?:ఆ|ఈ|ఏ|ఏయే|ప్రభుత్వ|సంక్షేమ|రాష్ట్ర)\s*పథక(?:ం|ానికి|ంలో|ాన్ని|ాల|ాలు|ాలకు|ాలకి|ల)?"),

    # Telugu: Semantic aspect queries mentioning generic scheme(s)
    # Documents / certificates
    re.compile(r"(?:పత్రాలు|డాక్యుమెంట్లు|సర్టిఫికెట్లు|ధృవపత్రాలు).*(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల)"),
    re.compile(r"(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల).*(?:పత్రాలు|డాక్యుమెంట్లు|సర్టిఫికెట్లు|ధృవపత్రాలు)"),
    # Eligibility / criteria / rules
    re.compile(r"(?:అర్హత|అర్హతలు|అర్హులు|నిబంధనలు|వయోపరిమితి|ఆదాయ\s*పరిమితి).*(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల)"),
    re.compile(r"(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల).*(?:అర్హత|అర్హతలు|అర్హులు|నిబంధనలు|వయోపరిమితి|ఆదాయ\s*పరిమితి)"),
    # Benefits / money / assistance
    re.compile(r"(?:ప్రయోజనాలు|సహాయం|ఆర్థిక\s*సహాయం|డబ్బు|మొత్తం|లబ్ధి).*(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల)"),
    re.compile(r"(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల).*(?:ప్రయోజనాలు|సహాయం|ఆర్థిక\s*సహాయం|డబ్బు|మొత్తం|లబ్ధి)"),
    # Application / registration / submission
    re.compile(r"(?:దరఖాస్తు|దరఖాస్తులు|నమోదు|రిజిస్ట్రేషన్|సమర్పణ|విధానం|ఫారమ్).*(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల)"),
    re.compile(r"(?:పథక|పథకం|పథకానికి|పథకాలు|పథకాల).*(?:దరఖాస్తు|దరఖాస్తులు|నమోదు|రిజిస్ట్రేషన్|సమర్పణ|విధానం|ఫారమ్)"),
    # Details / info / overview / explain
    re.compile(r"పథకం\s*(?:గురించి|వివరాలు|సమాచారం|చెప్పండి|ఏమిటి|ఏంటి|ఎలా)"),
    re.compile(r"పథకాలు\s*(?:ఏమిటి|ఏంటి|చెప్పండి|వివరాలు|జాబితా|ఎన్ని)"),
    re.compile(r"(?:పథక|పథకం|పథకాలు)\s*గురించి"),
    re.compile(r"^పథక(?:ం|ాలు)[?!.]*$"),
]


def is_ambiguous_scheme_query(query: str, language: LanguageCode) -> bool:
    """
    Detects whether a user is asking about 'the scheme' or generic schemes without identifying which one.
    Uses pattern-based and semantic matching rather than an arbitrary word-count ceiling.
    Preserves normal retrieval for sufficiently specific or named-scheme questions.
    """
    if not query or not query.strip():
        return False

    q = query.strip()

    # 1. If any specific named scheme or program is identified, it is NOT ambiguous
    if any(p.search(q) for p in SPECIFIC_SCHEME_PATTERNS):
        return False

    # 2. Check for the presence of generic scheme indicators in English or Telugu
    has_english_scheme_term = bool(re.search(r"\b(?:schemes?)\b", q, re.IGNORECASE))
    has_telugu_scheme_term = bool(re.search(r"పథక(?:ం|ానికి|ంలో|ాన్ని|ాల|ాలు|ాలకు|ాలకి|ల)?", q))

    if not has_english_scheme_term and not has_telugu_scheme_term:
        return False

    # 3. Check semantic ambiguity patterns
    if any(p.search(q) for p in AMBIGUOUS_SCHEME_PATTERNS):
        return True

    # 4. Fallback: Any query that mentions generic 'scheme(s)' / 'పథకం' but contains no specific scheme
    # and directly questions it (starts with question words like what, which, how, can, tell, etc.)
    if re.search(r"\b(?:what|which|how|where|who|can|tell|give|list|explain)\b", q, re.IGNORECASE) and has_english_scheme_term:
        return True
    if re.search(r"(?:ఏమిటి|ఏంటి|ఎలా|ఎక్కడ|ఎవరు|ఎంత|చెప్పండి|తెలపండి|ఇవ్వండి)", q) and has_telugu_scheme_term:
        return True

    return False


def get_scheme_clarification_response(language: LanguageCode) -> Dict[str, Any]:
    """
    Returns a structured clarification response prompting the citizen to specify
    which scheme they need assistance with.
    """
    lang_key = "te" if language == LanguageCode.TE else "en"
    content = SCHEME_CLARIFICATION_DATA[lang_key]

    return {
        "answer": content["answer"],
        "sources": [],
        "needs_follow_up": True,
        "follow_up_questions": content["follow_up_questions"],
        "safety_notice": content["safety_notice"],
    }
