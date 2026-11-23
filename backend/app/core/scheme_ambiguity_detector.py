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
    re.compile(r"\b(?:pension|oap|widow|disabled|disability|kanuka|ntr\s*bharosa|bharosa)\b", re.IGNORECASE),
    re.compile(r"పింఛన్|పెన్షన్|కానుక|వృద్ధాప్య|వితంతు|దివ్యాంగుల|ఎన్టీఆర్\s*భరోసా|భరోసా"),
    # Agriculture
    re.compile(r"\b(?:annadata|sukhibhava|rythu|pm-?kisan|kisan|crop\s*loan|crop\s*insurance|e-?panta|sunna\s*vaddi|seed\s*subsidy|fertilizer\s*subsidy)\b", re.IGNORECASE),
    re.compile(r"అన్నదాత|సుఖీభవ|రైతు|పీఎం\s*కిసాన్|కిసాన్|పంటల\s*బీమా|ఈ-?పంట|సున్నా\s*వడ్డీ"),
    # Healthcare
    re.compile(r"\b(?:vaidya\s*seva|dr\s*ntr|aarogyasri|ayushman|aarogya|asara|phc|chc|health\s*card)\b", re.IGNORECASE),
    re.compile(r"వైద్య\s*సేవ|ఎన్టీఆర్|ఆరోగ్యశ్రీ|ఆయుష్మాన్|ఆరోగ్య\s*ఆసరా|ఆరోగ్యం"),
    # Education
    re.compile(r"\b(?:thalliki\s*vandanam|vandanam|amma\s*vodi|vidya\s*deevena|vasathi\s*deevena|jnanabhumi|scholarship|fee\s*reimbursement|hostel\s*fee)\b", re.IGNORECASE),
    re.compile(r"తల్లికి\s*వందనం|వందనం|అమ్మ\s*ఒడి|విద్యా\s*దీవెన|వసతి\s*దీవెన|జ్ఞానభూమి|స్కాలర్‌షిప్|ఫీజు"),
    # Women & Livelihood
    re.compile(r"\b(?:cheyutha|aasara|kapu\s*nestham|vahana\s*mitra|nethanna|chedodu|matsyakara|dwakra|dwcra|shg)\b", re.IGNORECASE),
    re.compile(r"చేయూత|ఆసరా|కాపు\s*నేస్తం|వాహన\s*మిత్ర|నేతన్న|చేదోడు|మత్స్యకార|డ్వాక్రా"),
    # Housing & Civil Supplies
    re.compile(r"\b(?:pedalandariki\s*illu|housing|house\s*site|patta|rice\s*card|ration\s*card|bima|insurance)\b", re.IGNORECASE),
    re.compile(r"ఇల్లు|ఇళ్లు|ఇళ్ల\s*పట్టా|పేదలందరికీ\s*ఇళ్లు|రేషన్\s*కార్డు|బియ్యం\s*కార్డు|బీమా|రేషన్"),
]

# Generic/Ambiguous scheme patterns that indicate the user is asking about "the scheme" without naming one
AMBIGUOUS_SCHEME_PATTERNS: List[re.Pattern] = [
    # English ambiguous expressions
    re.compile(r"\b(?:tell\s+me\s+about\s+(?:the\s+)?scheme|what\s+is\s+the\s+scheme|what\s+are\s+the\s+schemes)\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+to\s+apply\s+for\s+(?:the\s+)?scheme|details\s+of\s+(?:the\s+)?scheme|explain\s+(?:the\s+)?scheme)\b", re.IGNORECASE),
    re.compile(r"\b(?:information\s+about\s+(?:the\s+)?scheme|information\s+on\s+(?:the\s+)?scheme)\b", re.IGNORECASE),
    re.compile(r"\b(?:which\s+scheme\s+is\s+available|what\s+schemes\s+are\s+there|list\s+(?:of\s+)?schemes)\b", re.IGNORECASE),
    re.compile(r"^(?:the\s+scheme|scheme|schemes|govt\s+schemes?|government\s+schemes?|welfare\s+schemes?|state\s+schemes?)[?!.]*$", re.IGNORECASE),
    re.compile(r"\b(?:about\s+the\s+scheme|about\s+schemes|regarding\s+the\s+scheme)\b", re.IGNORECASE),
    # Telugu ambiguous expressions
    re.compile(r"పథకం\s*గురించి\s*చెప్పండి"),
    re.compile(r"పథకాలు\s*(?:ఏమిటి|ఏంటి|చెప్పండి|వివరాలు)"),
    re.compile(r"ప్రభుత్వ\s*పథకాలు"),
    re.compile(r"పథకం\s*వివరాలు"),
    re.compile(r"పథకం\s*ఎలా\s*దరఖాస్తు\s*చేయాలి"),
    re.compile(r"ఆ\s*పథకం\s*ఏమిటి"),
    re.compile(r"ఈ\s*పథకం\s*(?:గురించి)?"),
    re.compile(r"పథకాల\s*జాబితా"),
    re.compile(r"సంక్షేమ\s*పథకాలు"),
    re.compile(r"^పథకం[?!.]*$"),
    re.compile(r"^పథకాలు[?!.]*$"),
]


def is_ambiguous_scheme_query(query: str, language: LanguageCode) -> bool:
    """
    Detects whether a user is asking about 'the scheme' without identifying which scheme.
    Preserves normal retrieval for sufficiently specific questions.
    """
    if not query or not query.strip():
        return False

    q = query.strip()

    # 1. If any specific scheme keyword is present, it is NOT ambiguous
    if any(p.search(q) for p in SPECIFIC_SCHEME_PATTERNS):
        return False

    # 2. Check if any ambiguous pattern matches
    if any(p.search(q) for p in AMBIGUOUS_SCHEME_PATTERNS):
        return True

    # 3. Short queries containing generic words like 'scheme' or 'పథకం' without specifics
    words = re.findall(r"\w+", q.lower())
    if len(words) <= 6:
        if any(w in ("scheme", "schemes", "పథకం", "పథకాలు") for w in words):
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
