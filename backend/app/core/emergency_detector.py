import re
from typing import Any, Dict, List, Optional
from app.schemas.common import LanguageCode

# Prominent emergency responses in English and Telugu
# Strictly adheres to public-service safety:
# - Advises immediate emergency medical assistance.
# - Directs user to call 108 in Andhra Pradesh or seek nearest emergency department.
# - Never directs user to a Grama Sachivalayam for emergencies.
# - Avoids definitive diagnoses or unsupported treatment instructions.
# - Preserves the standard ChatResponse schema.

EMERGENCY_DATA: Dict[str, Dict[str, Any]] = {
    "en": {
        "answer": (
            "EMERGENCY MEDICAL ADVISORY: The symptoms you described indicate a potential life-threatening "
            "medical emergency that requires immediate medical evaluation and urgent care.\n\n"
            "Please take the following actions immediately:\n"
            "1. Call 108 immediately for free emergency ambulance assistance across Andhra Pradesh.\n"
            "2. If an ambulance is not immediately available, proceed at once to the emergency department / casualty ward of the nearest hospital or community health center.\n"
            "3. Keep the person calm, resting in a comfortable position, and avoid physical exertion.\n"
            "4. Do not take or administer unprescribed medications without professional medical supervision.\n\n"
            "Time is critical. Please call 108 or reach the nearest emergency hospital now."
        ),
        "follow_up_questions": [
            "Have you dialed 108 for emergency ambulance assistance in Andhra Pradesh?",
            "Do you need directions to the nearest hospital emergency department?",
        ],
        "safety_notice": (
            "CRITICAL EMERGENCY NOTICE: For life-threatening emergencies, immediately call 108 or "
            "visit the nearest hospital casualty/emergency ward. Do not delay seeking emergency medical care."
        ),
    },
    "te": {
        "answer": (
            "అత్యవసర వైద్య హెచ్చరిక: మీరు పేర్కొన్న లక్షణాలు ప్రాణాంతకమైన తీవ్ర వైద్య అత్యవసర పరిస్థితిని "
            "సూచిస్తున్నాయి. వీటికి తక్షణ అత్యవసర వైద్య చికిత్స అవసరం.\n\n"
            "దయచేసి ఏమాత్రం ఆలస్యం చేయకుండా వెంటనే ఈ క్రింది చర్యలు తీసుకోండి:\n"
            "1. ఆంధ్రప్రదేశ్ ఉచిత అత్యవసర అంబులెన్స్ సేవ కోసం వెంటనే 108 నంబర్‌కు కాల్ చేయండి.\n"
            "2. అంబులెన్స్ ఆలస్యమైతే, వెంటనే రోగిని సమీపంలోని ప్రభుత్వ లేదా ప్రైవేట్ ఆసుపత్రి అత్యవసర విభాగానికి (Emergency / Casualty Ward) తీసుకెళ్లండి.\n"
            "3. రోగిని విశ్రాంతిగా, ప్రశాంతమైన భంగిమలో ఉంచండి, శారీరక శ్రమ చేయనివ్వవద్దు.\n"
            "4. వైద్యుని పర్యవేక్షణ లేకుండా ఎలాంటి అనధికార మందులు లేదా ఇంజెక్షన్లు ఇవ్వవద్దు.\n\n"
            "సమయం అత్యంత విలువైనది. ఏమాత్రం ఆలస్యం చేయకుండా వెంటనే 108 కు కాల్ చేయండి లేదా సమీప అత్యవసర ఆసుపత్రికి వెళ్లండి."
        ),
        "follow_up_questions": [
            "మీరు ఆంధ్రప్రదేశ్ అత్యవసర అంబులెన్స్ సహాయం కొరకు 108 కు కాల్ చేశారా?",
            "సమీపంలోని ఆసుపత్రి అత్యవసర విభాగానికి వెంటనే చేరుకోగలరా?",
        ],
        "safety_notice": (
            "అత్యవసర వైద్య హెచ్చరిక: ప్రాణాంతక అత్యవసర పరిస్థితుల్లో వెంటనే 108 కు డయల్ చేయండి లేదా "
            "సమీప ఆసుపత్రి అత్యవసర విభాగాన్ని సంప్రదించండి. చికిత్సను ఏమాత్రం ఆలస్యం చేయవద్దు."
        ),
    },
}

# Compiled regex patterns for English emergency conditions
EMERGENCY_PATTERNS_EN: List[re.Pattern] = [
    # Severe chest pain & cardiac events
    re.compile(
        r"\b(?:severe|acute|crushing|sharp|heavy|intense|radiating)?\s*(?:chest\s*pain|chest\s*pressure|chest\s*tightness|heart\s*attack|cardiac\s*arrest)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bpain\s+(?:in|across)\s+(?:the\s+)?chest\b", re.IGNORECASE),
    re.compile(r"\bchest\s+hurts?\s+(?:severely|badly|a\s+lot)\b", re.IGNORECASE),
    # Difficulty breathing & respiratory distress
    re.compile(
        r"\b(?:severe|acute)?\s*(?:difficulty\s*(?:in\s*)?breathing|shortness\s*of\s*breath|trouble\s*breathing|cannot\s*breathe|can't\s*breathe|unable\s*to\s*breathe|struggling\s*to\s*breathe|gasping\s*for\s*(?:breath|air)|severe\s*breathlessness|respiratory\s*(?:distress|failure)|suffocating|choking)\b",
        re.IGNORECASE,
    ),
    # Stroke symptoms
    re.compile(
        r"\b(?:stroke|brain\s*stroke|paralys(?:is|ed)|facial\s*droop(?:ing)?|face\s*droop(?:ing)?|slurred\s*speech|speech\s*difficulty|loss\s*of\s*speech|sudden\s*(?:weakness|numbness)\s*(?:in|of)?\s*(?:arm|face|leg|one\s*side)|hemiplegia)\b",
        re.IGNORECASE,
    ),
    # Unconsciousness & coma
    re.compile(
        r"\b(?:unconscious(?:ness)?|passed\s*out|fainted|loss\s*of\s*consciousness|unresponsive|collapsed\s*and\s*not\s*waking|in\s*a\s*coma|sudden\s*collapse)\b",
        re.IGNORECASE,
    ),
    # Severe bleeding
    re.compile(
        r"\b(?:severe\s*bleeding|heavy\s*bleeding|bleeding\s*profusely|uncontrolled\s*bleeding|profuse\s*bleeding|massive\s*hemorrhage|massive\s*haemorrhage|vomiting\s*blood|coughing\s*(?:up\s*)?blood|blood\s*won't\s*stop)\b",
        re.IGNORECASE,
    ),
    # Poisoning & toxic ingestion
    re.compile(
        r"\b(?:poisoning|drank\s*poison|swallowed\s*poison|consumed\s*poison|consumed\s*pesticide|drank\s*pesticide|pesticide\s*poisoning|chemical\s*poisoning|snake\s*bite|snakebite|insecticide\s*ingestion)\b",
        re.IGNORECASE,
    ),
    # Other urgent trauma / life threats
    re.compile(
        r"\b(?:severe\s*head\s*injury|anaphylaxis|severe\s*allergic\s*reaction|electric\s*shock)\b",
        re.IGNORECASE,
    ),
]

# Compiled regex patterns for Telugu emergency conditions
EMERGENCY_PATTERNS_TE: List[re.Pattern] = [
    # Severe chest pain & cardiac events
    re.compile(r"తీవ్రమైన\s*(?:ఛాతి|ఛాతీ)\s*నొప్పి"),
    re.compile(r"(?:ఛాతి|ఛాతీ)\s*నొప్పి"),
    re.compile(r"(?:ఛాతి|ఛాతీ)లో\s*(?:తీవ్రమైన\s*)?నొప్పి"),
    re.compile(r"గుండెపోటు|గుండె\s*పోటు|గుండెనొప్పి|గుండె\s*ఆగిపోయింది"),
    # Difficulty breathing & respiratory distress
    re.compile(r"శ్వాస\s*(?:తీసుకోవడంలో\s*)?ఇబ్బంది"),
    re.compile(r"శ్వాస\s*(?:తీసుకోవడం\s*)?కష్ట"),
    re.compile(r"శ్వాస\s*(?:ఆడటం|ఆడట్లేదు|అందడం|అందట్లేదు)\s*లేదు"),
    re.compile(r"శ్వాస\s*(?:ఆడట్లేదు|అందట్లేదు)"),
    re.compile(r"ఊపిరి\s*(?:ఆడటం|ఆడట్లేదు|అందడం|అందట్లేదు)\s*లేదు"),
    re.compile(r"తీవ్రమైన\s*ఆయాసం|ఆయాసంగా\s*ఉంది"),
    # Stroke symptoms
    re.compile(r"పక్షవాతం|పక్షవాత\s*లక్షణాలు|పక్షవాతపు"),
    re.compile(r"ముఖం\s*వంకర(?:పోవడం|పోయింది|పోయిన)"),
    re.compile(r"మాట\s*తడబడ|మాట\s*పడిపోయింది|మాట\s*రావడం\s*లేదు"),
    re.compile(r"ఒక\s*వైపు\s*చచ్చుబడిపో"),
    re.compile(r"(?:చేయి|కాలు|చెయ్యి)\s*పడిపో"),
    # Unconsciousness
    re.compile(r"స్పృహ\s*(?:కోల్పో|తప్ప|తప్పి\s*పడిపో|తప్పిపోయింది|తప్పిపోయాడు)"),
    re.compile(r"స్పృహ\s*లేదు"),
    re.compile(r"మూర్ఛ|మూర్ఛ\s*వచ్చింది"),
    re.compile(r"కళ్ళు\s*తిరిగి\s*పడిపో"),
    re.compile(r"అపస్మారక\s*స్థితి"),
    # Severe bleeding
    re.compile(r"తీవ్రమైన\s*రక్తస్రావం|విపరీతమైన\s*రక్తస్రావం|తీవ్రమైన\s*రక్తస్రావ|విపరీతమైన\s*రక్తస్రావ"),
    re.compile(r"రక్తం\s*ఆగ(?:డం\s*లేదు|ట్లేదు)"),
    re.compile(r"రక్తపు\s*వాంతులు|రక్తం\s*కక్కుకో"),
    re.compile(r"విపరీతంగా\s*రక్తం\s*కారు"),
    # Poisoning & bites
    re.compile(r"విషం\s*(?:తాగ|మింగ)|విషప్రయోగం"),
    re.compile(r"పురుగుల?\s*మందు\s*(?:తాగ)"),
    re.compile(r"పాము\s*(?:కాటు|కరిచి)"),
    # Other urgent trauma
    re.compile(r"తీవ్రమైన\s*తల\s*గాయం|తీవ్రమైన\s*తల\s*గాయ|విద్యుత్\s*షాక్|షాక్\s*కొట్టింది"),
]

# Patterns for Negation in English
# e.g., "no chest pain", "without difficulty breathing", "has not passed out"
NEGATION_PATTERNS_EN: List[re.Pattern] = [
    re.compile(
        r"\b(?:no|not|without|denies|denied|hasn't|has\s*not|had\s*no|rule(?:d)?\s*out|negative\s*for|neither|never\s*had)\b\s+(?:\w+\s+){0,4}?(?:chest\s*pain|chest\s*pressure|chest\s*tightness|heart\s*attack|cardiac\s*arrest|shortness\s*of\s*breath|difficulty\s*breathing|trouble\s*breathing|bleeding|stroke|unconscious|unresponsiv|faint|poison|snake\s*bite)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:chest\s*pain|difficulty\s*breathing|shortness\s*of\s*breath|bleeding|stroke|unconsciousness)\s+(?:is\s+)?(?:absent|negative|resolved|gone|ruled\s*out)\b",
        re.IGNORECASE,
    ),
]

# Patterns for Historical / Past mentions in English
# e.g., "had chest pain 2 years ago", "history of heart attack in 2018"
HISTORICAL_PATTERNS_EN: List[re.Pattern] = [
    re.compile(
        r"\b(?:years?|months?|weeks?|days?)\s+ago\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:in\s+)?(?:19\d\d|20[0-1]\d|202[0-5])\b",  # specific past years up to 2025
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:history\s+of|past\s+history|previous\s+history|prior\s+history|historically|in\s+the\s+past|previously|when\s+I\s+was\s+(?:young|a\s+child|a\s+kid)|years\s+back|long\s+ago|recovered\s+from|treated\s+for)\b",
        re.IGNORECASE,
    ),
]

# Patterns for Negation in Telugu
# e.g., "ఛాతి నొప్పి లేదు", "శ్వాస ఇబ్బంది లేదు", "రక్తస్రావం లేదు", "స్పృహ కోల్పోలేదు"
NEGATION_PATTERNS_TE: List[re.Pattern] = [
    re.compile(r"(?:ఛాతి|ఛాతీ)\s*నొప్పి\s*లేదు"),
    re.compile(r"(?:ఛాతి|ఛాతీ)లో\s*నొప్పి\s*లేదు"),
    re.compile(r"గుండెపోటు\s*(?:రాలేదు|లేదు)"),
    re.compile(r"శ్వాస\s*(?:తీసుకోవడంలో\s*)?ఇబ్బంది\s*లేదు"),
    re.compile(r"శ్వాస\s*సమస్య\s*లేదు"),
    re.compile(r"రక్తస్రావం\s*లేదు"),
    re.compile(r"స్పృహ\s*కోల్పోలేదు"),
    re.compile(r"పక్షవాతం\s*రాలేదు"),
    re.compile(r"నొప్పి\s*(?:ఏమీ\s*)?లేదు"),
    re.compile(r"ఏ\s*సమస్యా\s*లేదు"),
]

# Patterns for Historical / Past in Telugu
# e.g., "గతంలో ఛాతీ నొప్పి వచ్చింది", "రెండేళ్ల క్రితం గుండెపోటు"
HISTORICAL_PATTERNS_TE: List[re.Pattern] = [
    re.compile(r"గతంలో"),
    re.compile(r"పూర్వం"),
    re.compile(r"(?:సంవత్సరాల|సంవత్సరం|ఏళ్ల|నెలల|రోజుల)\s*(?:క్రితం|కిందట)"),
    re.compile(r"గత\s*సంవత్సరం"),
    re.compile(r"చిన్నప్పుడు"),
    re.compile(r"పూర్వపు"),
    re.compile(r"(?:నయమైంది|రికవర్\s*అయ్యారు|కోలుకున్నారు)"),
]


def _is_clause_active_emergency(clause: str, language: LanguageCode) -> bool:
    """
    Checks if a single clause contains an active, un-negated, non-historical emergency.
    """
    clause_clean = clause.strip()
    if not clause_clean:
        return False

    # 1. Match Telugu emergency patterns
    has_te_emergency = any(p.search(clause_clean) for p in EMERGENCY_PATTERNS_TE)
    # 2. Match English emergency patterns
    has_en_emergency = any(p.search(clause_clean) for p in EMERGENCY_PATTERNS_EN)

    if not (has_te_emergency or has_en_emergency):
        return False

    # Check Telugu negation / history: if negated or historical, this clause is not an active emergency
    if has_te_emergency:
        is_negated_te = any(p.search(clause_clean) for p in NEGATION_PATTERNS_TE)
        is_historical_te = any(p.search(clause_clean) for p in HISTORICAL_PATTERNS_TE)
        if is_negated_te or is_historical_te:
            return False

    # Check English negation / history: if negated or historical, this clause is not an active emergency
    if has_en_emergency:
        is_negated_en = any(p.search(clause_clean) for p in NEGATION_PATTERNS_EN)
        is_historical_en = any(p.search(clause_clean) for p in HISTORICAL_PATTERNS_EN)
        if is_negated_en or is_historical_en:
            return False

    return True


def check_clinical_emergency(
    query: str,
    language: LanguageCode,
) -> Optional[Dict[str, Any]]:
    """
    Deterministic clinical emergency safety guard.
    Operates before RAG retrieval or generic no-results fallbacks.

    Recognizes high-risk emergency expressions in English and Telugu:
    - Severe chest pain / తీవ్రమైన ఛాతి నొప్పి
    - Difficulty breathing / శ్వాస తీసుకోవడంలో ఇబ్బంది
    - Stroke symptoms
    - Unconsciousness
    - Severe bleeding
    - Poisoning
    - Other clearly urgent symptoms

    Conservative and testable:
    - Filters out negated symptoms ("no chest pain", "ఛాతి నొప్పి లేదు").
    - Filters out purely historical mentions ("had chest pain 2 years ago", "గతంలో ఛాతీ నొప్పి").

    Returns None if not an active emergency.
    Returns structured emergency dict preserving ChatResponse schema if active emergency.
    """
    if not query or not query.strip():
        return None

    query_text = query.strip()

    # Split into clauses/sentences to isolate negations and past mentions
    # Delimiters: punctuation (. , ; ! ? \n) and coordinating contrasting conjunctions (but, however, అయితే, కానీ)
    clauses = re.split(r"[.!?,;\n\r]+|\b(?:but|however|although|whereas)\b|కానీ|అయితే", query_text, flags=re.IGNORECASE)

    active_emergency_found = False
    for clause in clauses:
        if _is_clause_active_emergency(clause, language):
            active_emergency_found = True
            break

    # If clause splitting did not catch it, test the full query as a whole
    if not active_emergency_found:
        if _is_clause_active_emergency(query_text, language):
            active_emergency_found = True

    if not active_emergency_found:
        return None

    # Determine response language
    lang_key = "te" if language == LanguageCode.TE else "en"
    emergency_content = EMERGENCY_DATA[lang_key]

    return {
        "is_emergency": True,
        "answer": emergency_content["answer"],
        "sources": [],
        "needs_follow_up": False,
        "follow_up_questions": emergency_content["follow_up_questions"],
        "safety_notice": emergency_content["safety_notice"],
    }
