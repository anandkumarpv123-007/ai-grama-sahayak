"""Grievance Drafter Module for AI Grama Sahayak.

Generates respectful, structured formal complaint drafts for citizens
in English and Telugu, along with verified official Andhra Pradesh submission
guidance.

Guardrails:
- Never claims a complaint has been submitted to government authorities.
- Never claims live tracking without authorized integration.
- Sources reference official AP Government portals only.
"""

from typing import Dict, Any, List

OFFICIAL_AP_GRIEVANCE_LINKS: List[Dict[str, str]] = [
    {
        "title": "AP Spandana Public Grievance Redressal Portal",
        "url": "https://spandana.ap.gov.in",
        "publisher": "Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
    },
    {
        "title": "Andhra Pradesh Grama / Ward Sachivalayam Portal",
        "url": "https://gramawardsachivalayam.ap.gov.in",
        "publisher": "Department of Gram Volunteers/Ward Volunteers and Village Secretariats/Ward Secretariats, AP",
        "verified_at": "2026-11-21",
    },
    {
        "title": "Meeseva Citizen Portal Andhra Pradesh",
        "url": "https://meeseva.gov.in",
        "publisher": "Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
    },
]

CATEGORY_LABELS = {
    "water_supply": {
        "en": "Drinking Water Supply Issue",
        "te": "తాగునీటి సరఫరా సమస్య",
    },
    "electricity": {
        "en": "Electricity & Power Supply Interruption",
        "te": "విద్యుత్ సరఫరా అంతరాయం",
    },
    "roads": {
        "en": "Road Repair & Infrastructure Maintenance",
        "te": "రహదారుల మరమ్మత్తు మరియు మౌలిక వసతులు",
    },
    "sanitation": {
        "en": "Sanitation & Drainage Management",
        "te": "పారిశుధ్యం మరియు డ్రైనేజీ నిర్వహణ",
    },
    "ration": {
        "en": "Public Distribution System (PDS / Rice Card)",
        "te": "ప్రజా పంపిణీ వ్యవస్థ (రేషన్ / బియ్యం కార్డు)",
    },
    "pension": {
        "en": "Social Security Pension Services",
        "te": "సామాజిక భద్రతా పెన్షన్ సేవలు",
    },
    "revenue": {
        "en": "Land Records & Revenue Services",
        "te": "భూ రికార్డులు మరియు రెవెన్యూ సేవలు",
    },
    "agriculture": {
        "en": "Agriculture & Farmer Welfare Support",
        "te": "వ్యవసాయం మరియు రైతు సంక్షేమ సహాయం",
    },
    "health": {
        "en": "Public Health & Medical Services",
        "te": "ప్రజా ఆరోగ్యం మరియు వైద్య సేవలు",
    },
    "education": {
        "en": "School & Educational Facilities",
        "te": "పాఠశాల మరియు విద్యా వసతులు",
    },
}


def _get_category_label(category: str, language: str) -> str:
    key = category.strip().lower().replace(" ", "_")
    if key in CATEGORY_LABELS:
        return CATEGORY_LABELS[key].get(language, category)
    # Generic fallback
    if language == "te":
        return f"{category} సమస్య"
    return f"{category.replace('_', ' ').title()} Issue"


def draft_grievance(
    category: str,
    description: str,
    district: str,
    mandal: str,
    language: str = "en",
) -> Dict[str, Any]:
    """Draft a respectful and formal citizen grievance letter.

    Parameters:
        category: Category of grievance (e.g., 'water_supply', 'electricity', 'roads').
        description: Citizen's description of the problem.
        district: District in Andhra Pradesh.
        mandal: Mandal within the district.
        language: 'en' for English or 'te' for Telugu.

    Returns:
        Dictionary matching the API contract:
        {
            "subject": str,
            "complaint_body": str,
            "recommended_next_steps": List[str],
            "official_links": List[Dict[str, str]]
        }
    """
    if not category or not category.strip():
        raise ValueError("Grievance category must not be empty.")
    if not description or not description.strip():
        raise ValueError("Grievance description must not be empty.")
    if not district or not district.strip():
        raise ValueError("District must not be empty.")
    if not mandal or not mandal.strip():
        raise ValueError("Mandal must not be empty.")

    clean_lang = language.strip().lower()
    if clean_lang not in ("en", "te"):
        raise ValueError("Language must be 'en' (English) or 'te' (Telugu).")

    clean_category = category.strip()
    clean_desc = description.strip()
    clean_district = district.strip()
    clean_mandal = mandal.strip()

    category_title = _get_category_label(clean_category, clean_lang)

    if clean_lang == "te":
        subject = f"విజ్ఞప్తి: {clean_mandal} మండలం, {clean_district} జిల్లాలో {category_title} పరిష్కారం కొరకు దరఖాస్తు"

        complaint_body = (
            f"గౌరవనీయులైన ప్రజా ఫిర్యాదుల పరిష్కార అధికారి గారికి,\n"
            f"{clean_mandal} మండలం, {clean_district} జిల్లా,\n"
            f"ఆంధ్రప్రదేశ్ ప్రభుత్వం.\n\n"
            f"విషయం: {subject}\n\n"
            f"ఆర్యా / నమస్కారం,\n\n"
            f"నేను ఆంధ్రప్రదేశ్ రాష్ట్రం, {clean_district} జిల్లా, {clean_mandal} మండల నివాసిని. "
            f"మా ప్రాంతంలో నెలకొన్న {category_title}ను మీ దృష్టికి తీసుకువచ్చి, తగిన పరిష్కారం కోరుతూ ఈ క్రింది వివరాలను సమర్పిస్తున్నాను.\n\n"
            f"సమస్య వివరాలు:\n"
            f"{clean_desc}\n\n"
            f"ప్రాంత వివరాలు:\n"
            f"- మండలం: {clean_mandal}\n"
            f"- జిల్లా: {clean_district}\n"
            f"- రాష్ట్రం: ఆంధ్రప్రదేశ్\n\n"
            f"సమస్య తీవ్రతను దృష్టిలో ఉంచుకొని, సంబంధిత శాఖాధికారులు వెంటనే క్షేత్రస్థాయి పరిశీలన జరిపి, "
            f"సమస్యను సత్వరమే పరిష్కరించాలని మరియు తగిన నివారణ చర్యలు చేపట్టాలని గౌరవపూర్వకంగా కోరుతున్నాను.\n\n"
            f"ధన్యవాదములతో,\n"
            f"భవదీయుడు / భవదీయురాలు,\n"
            f"బాధిత పౌరుడు / పౌరురాలు"
        )

        recommended_next_steps = [
            "ఈ ఫిర్యాదు ముసాయిదాలోని వ్యక్తిగత వివరాలు, గ్రామం/వీధి పేరు మరియు తేదీలను సరిచూసుకోండి.",
            "ఈ దరఖాస్తును ఆంధ్రప్రదేశ్ ప్రభుత్వ అధికారిక స్పందన పోర్టల్ (https://spandana.ap.gov.in) ద్వారా సమర్పించండి లేదా 1902 టోల్-ఫ్రీ నంబర్‌కు కాల్ చేసి నమోదు చేయించండి.",
            "ప్రత్యామ్నాయంగా, ఈ ముసాయిదా కాపీని మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో లేదా ప్రతి సోమవారం కలెక్టరేట్/తహశీల్దార్ కార్యాలయంలో జరిగే స్పందన గ్రీవెన్స్ కార్యక్రమంలో సమర్పించవచ్చు.",
            "ఫిర్యాదు సమర్పించిన తర్వాత లభించే అధికారిక గ్రీవెన్స్ ఐడీని (Grievance Registration Number) భవిష్యత్తు ట్రాకింగ్ కొరకు భద్రపరచుకోండి.",
            "ముఖ్య గమనిక: ఇది పౌరుల సౌలభ్యం కొరకు రూపొందించిన ముసాయిదా మాత్రమే. ఇది ఏ ప్రభుత్వ కార్యాలయానికీ స్వయంచాలకంగా సమర్పించబడలేదు.",
        ]
    else:
        subject = f"Representation regarding {category_title} in {clean_mandal} Mandal, {clean_district} District"

        complaint_body = (
            f"To,\n"
            f"The Grievance Redressal Officer / Competent Authority,\n"
            f"{clean_mandal} Mandal, {clean_district} District,\n"
            f"Government of Andhra Pradesh.\n\n"
            f"Subject: {subject}\n\n"
            f"Respected Sir/Madam,\n\n"
            f"I am a resident of {clean_mandal} Mandal, {clean_district} District, Andhra Pradesh. "
            f"I am writing this formal representation to bring the following grievance regarding {category_title} "
            f"to your immediate attention for necessary intervention and resolution.\n\n"
            f"Grievance Details:\n"
            f"{clean_desc}\n\n"
            f"Location Details:\n"
            f"- Mandal: {clean_mandal}\n"
            f"- District: {clean_district}\n"
            f"- State: Andhra Pradesh\n\n"
            f"Given the hardship caused to residents, I earnestly request the concerned authorities to conduct "
            f"a field inspection and initiate prompt remedial measures to resolve this issue at the earliest.\n\n"
            f"Thanking you,\n\n"
            f"Yours sincerely,\n"
            f"A Concerned Citizen"
        )

        recommended_next_steps = [
            "Review this draft to ensure all specific dates, landmark details, and personal contact info are accurate.",
            "Submit the grievance via the official AP Spandana portal (https://spandana.ap.gov.in) or call the toll-free helpline at 1902.",
            "Alternatively, present a physical copy at your local Grama / Ward Sachivalayam or during the weekly Monday Spandana redressal forum at the Mandal Revenue Office or Collectorate.",
            "Preserve your official Grievance Registration Number provided upon submission for status tracking.",
            "Note: This is an advisory draft generated to assist you in preparing your grievance. It has NOT been submitted automatically to any government office.",
        ]

    return {
        "subject": subject,
        "complaint_body": complaint_body,
        "recommended_next_steps": recommended_next_steps,
        "official_links": OFFICIAL_AP_GRIEVANCE_LINKS,
    }
