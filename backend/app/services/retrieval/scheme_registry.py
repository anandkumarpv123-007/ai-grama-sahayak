"""
Canonical Scheme Registry for AI Grama Sahayak Knowledge Base.
Maps Telugu and English scheme aliases to authoritative knowledge base document IDs and domains.
Enables cross-domain scheme awareness, historical predecessor mapping, and intent disambiguation.
"""

from typing import Any, Dict, List, Optional, Set
import re
import unicodedata

# 14 Canonical verified knowledge base documents
SCHEME_REGISTRY: Dict[str, Dict[str, Any]] = {
    "agri_annadata_sukhibhava_pmkisan": {
        "doc_id": "agri_annadata_sukhibhava_pmkisan",
        "title": "Annadata Sukhibhava – PM Kisan Scheme Guidelines",
        "current_name": "Annadata Sukhibhava",
        "domain": "agriculture",
        "portal_url": "https://annadathasukhibhava.ap.gov.in",
        "aliases": [
            "annadata sukhibhava",
            "annadata",
            "sukhibhava",
            "annadatha sukhibhava",
            "annadatha",
            "annadatasukhibhava",
            "annadathasukhibhava",
            "pm kisan",
            "pm-kisan",
            "pmkisan",
            "rythu bharosa",
            "ysr rythu bharosa",
            "rythubharosa",
            "అన్నదాత సుఖీభవ",
            "అన్నదాత",
            "సుఖీభవ",
            "అన్నదాతసుఖీభవ",
            "పీఎం కిసాన్",
            "పిఎం కిసాన్",
            "పీఎంకిసాన్",
            "పిఎంకిసాన్",
            "పీఎమ్ కిసాన్",
            "రైతు భరోసా",
            "రైతుభరోసా",
            "వైఎస్సార్ రైతు భరోసా",
        ],
        "historical_aliases": [
            "rythu bharosa",
            "ysr rythu bharosa",
            "rythubharosa",
            "రైతు భరోసా",
            "రైతుభరోసా",
            "వైఎస్సార్ రైతు భరోసా",
        ],
        "historical_note_en": (
            "Rythu Bharosa was the predecessor farmer financial assistance program in Andhra Pradesh, "
            "now succeeded and implemented under the reformed Annadata Sukhibhava scheme in convergence with PM-KISAN."
        ),
        "historical_note_te": (
            "గతంలో అమలులో ఉన్న వైఎస్సార్ రైతు భరోసా పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వం ద్వారా పీఎం కిసాన్ "
            "పథకంతో అనుసంధానించి అన్నదాత సుఖీభవ పథకంగా సంస్కరించబడి అమలు చేయబడుతోంది."
        ),
    },
    "agri_kisan_credit_card": {
        "doc_id": "agri_kisan_credit_card",
        "title": "Kisan Credit Card (KCC) Scheme Rules and Institutional Credit",
        "current_name": "Kisan Credit Card",
        "domain": "agriculture",
        "portal_url": "https://agricoop.nic.in",
        "aliases": [
            "kisan credit card",
            "kcc",
            "kisan credit",
            "kisan card",
            "kisancreditcard",
            "crop loan credit card",
            "కిసాన్ క్రెడిట్ కార్డు",
            "కిసాన్ క్రెడిట్ కార్డ్",
            "కిసాన్ క్రెడిట్",
            "కేసీసీ",
            "కిసాన్ కార్డు",
            "కిసాన్‌క్రెడిట్‌కార్డు",
        ],
        "historical_aliases": [],
    },
    "agri_pm_crop_insurance_ap": {
        "doc_id": "agri_pm_crop_insurance_ap",
        "title": "Pradhan Mantri Fasal Bima Yojana and AP Free Crop Insurance",
        "current_name": "PM Fasal Bima Yojana & AP Crop Insurance",
        "domain": "agriculture",
        "portal_url": "https://pmfby.gov.in",
        "aliases": [
            "crop insurance",
            "fasal bima",
            "pmfby",
            "pm fasal bima",
            "e-crop",
            "e-panta",
            "free crop insurance",
            "ap free crop insurance",
            "cropinsurance",
            "fasalbima",
            "ecrop",
            "epanta",
            "పంటల బీమా",
            "ఉచిత పంటల బీమా",
            "ఫసల్ బీమా",
            "ఈ-పంట",
            "ఈ పంట",
            "ఈపంట",
            "పంటలబీమా",
            "ఫసల్‌బీమా",
            "పీఎం ఎఫ్‌బీవై",
        ],
        "historical_aliases": [],
    },
    "agri_soil_health_card_polam_badi": {
        "doc_id": "agri_soil_health_card_polam_badi",
        "title": "Soil Health Card Scheme and Polam Badi Program",
        "current_name": "Soil Health Card & Polam Badi",
        "domain": "agriculture",
        "portal_url": "https://soilhealth.dac.gov.in",
        "aliases": [
            "soil health card",
            "polam badi",
            "soil health",
            "polambadi",
            "soil testing card",
            "soil testing",
            "soilhealthcard",
            "సాయిల్ హెల్త్ కార్డు",
            "సాయిల్ హెల్త్ కార్డ్",
            "నేల ఆరోగ్య కార్డు",
            "పొలం బడి",
            "పొలంబడి",
            "సాయిల్‌హెల్త్‌కార్డు",
            "భూసార కార్డు",
            "భూసార పరీక్ష",
        ],
        "historical_aliases": [],
    },
    "edu_samagra_shiksha_ap": {
        "doc_id": "edu_samagra_shiksha_ap",
        "title": "Samagra Shiksha Andhra Pradesh School Education Initiatives",
        "current_name": "Samagra Shiksha AP",
        "domain": "education",
        "portal_url": "https://samagrashiksha.ap.gov.in",
        "aliases": [
            "samagra shiksha",
            "samagrashiksha",
            "school education",
            "mid day meal",
            "pm poshan",
            "pmposhan",
            "mana badi nadu nedu",
            "nadu nedu",
            "nadunedu",
            "gorumudha",
            "jagananna gorumudha",
            "school textbooks",
            "school uniforms",
            "సమగ్ర శిక్ష",
            "సమగ్రశిక్ష",
            "పాఠశాల విద్య",
            "మధ్యాహ్న భోజనం",
            "గోరుముద్ద",
            "నాడు నేడు",
            "నాడునేడు",
            "మన బడి నాడు నేడు",
        ],
        "historical_aliases": [],
    },
    "edu_thalliki_vandanam_scheme": {
        "doc_id": "edu_thalliki_vandanam_scheme",
        "title": "Thalliki Vandanam Scheme Guidelines",
        "current_name": "Thalliki Vandanam",
        "domain": "education",
        "portal_url": "https://schooledu.ap.gov.in",
        "aliases": [
            "thalliki vandanam",
            "talliki vandanam",
            "thallikivandanam",
            "tallikivandanam",
            "amma vodi",
            "ammavodi",
            "amma odi",
            "ammaodi",
            "తల్లికి వందనం",
            "తల్లికివందనం",
            "అమ్మ ఒడి",
            "అమ్మఒడి",
        ],
        "historical_aliases": [
            "amma vodi",
            "ammavodi",
            "amma odi",
            "ammaodi",
            "అమ్మ ఒడి",
            "అమ్మఒడి",
        ],
        "historical_note_en": (
            "Amma Vodi is the predecessor school education financial support initiative in Andhra Pradesh, "
            "succeeded and reformed under the Thalliki Vandanam scheme guidelines."
        ),
        "historical_note_te": (
            "గతంలో అమలులో ఉన్న అమ్మ ఒడి పాఠశాల విద్యా ప్రోత్సాహక పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వ "
            "తల్లికి వందనం పథకం మార్గదర్శకాల ప్రకారం సంస్కరించబడి అమలు చేయబడుతోంది."
        ),
    },
    "edu_vidya_deevena_vasathi_deevena": {
        "doc_id": "edu_vidya_deevena_vasathi_deevena",
        "title": "Jagananna Vidya Deevena (RTF) and Vasathi Deevena (MTF) Post-Matric Scholarships",
        "current_name": "Vidya Deevena & Vasathi Deevena",
        "domain": "education",
        "portal_url": "https://jnanabhumi.ap.gov.in",
        "aliases": [
            "vidya deevena",
            "vasathi deevena",
            "jagananna vidya deevena",
            "jagananna vasathi deevena",
            "vidyadeevena",
            "vasathideevena",
            "fee reimbursement",
            "jnanabhumi",
            "post matric scholarship",
            "post-matric scholarship",
            "rtf",
            "mtf",
            "విద్యా దీవెన",
            "వసతి దీవెన",
            "విద్యాదీవెన",
            "వసతిదీవెన",
            "జ్ఞానభూమి",
            "ఫీజు రీయింబర్స్‌మెంట్",
            "ఫీజు రీయింబర్స్మెంట్",
            "పోస్ట్ మెట్రిక్ స్కాలర్‌షిప్",
        ],
        "historical_aliases": [],
    },
    "health_104_108_emergency_health_services": {
        "doc_id": "health_104_108_emergency_health_services",
        "title": "104 and 108 Emergency and Mobile Health Services",
        "current_name": "104 & 108 Emergency Services",
        "domain": "healthcare",
        "portal_url": "https://hmfw.ap.gov.in",
        "aliases": [
            "104",
            "108",
            "emergency health",
            "mobile medical unit",
            "ambulance",
            "emergency ambulance",
            "108 ambulance",
            "104 medical service",
            "అంబులెన్స్",
            "అత్యవసర ఆరోగ్య సేవలు",
            "మొబైల్ మెడికల్ యూనిట్",
            "108 అంబులెన్స్",
            "104 సేవలు",
        ],
        "historical_aliases": [],
    },
    "health_ayushman_bharat_pmjay_ap": {
        "doc_id": "health_ayushman_bharat_pmjay_ap",
        "title": "Ayushman Bharat – Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) in Andhra Pradesh",
        "current_name": "Ayushman Bharat PM-JAY",
        "domain": "healthcare",
        "portal_url": "https://pmjay.gov.in",
        "aliases": [
            "ayushman bharat",
            "ayushmanbharat",
            "pmjay",
            "pm-jay",
            "ab-pmjay",
            "ab pmjay",
            "golden card",
            "ఆయుష్మాన్ భారత్",
            "ఆయుష్మాన్‌భారత్",
            "పీఎంజేఏవై",
            "పీఎం-జేఏవై",
            "ఆయుష్మాన్ కార్డ్",
            "ఆయుష్మాన్ కార్డు",
        ],
        "historical_aliases": [],
    },
    "health_dr_ntr_vaidya_seva_aarogyasri": {
        "doc_id": "health_dr_ntr_vaidya_seva_aarogyasri",
        "title": "Dr. NTR Vaidya Seva (Aarogyasri) Health Insurance Scheme",
        "current_name": "Dr. NTR Vaidya Seva",
        "domain": "healthcare",
        "portal_url": "https://ysraarogyasri.ap.gov.in",
        "aliases": [
            "dr ntr vaidya seva",
            "ntr vaidya seva",
            "vaidya seva",
            "vaidyaseva",
            "dr. ntr vaidya seva",
            "aarogyasri",
            "arogyasri",
            "aarogya sri",
            "arogya sri",
            "ysr aarogyasri",
            "ntr arogya seva",
            "వైద్య సేవ",
            "వైద్యసేవ",
            "ఎన్టీఆర్ వైద్య సేవ",
            "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ",
            "ఆరోగ్యశ్రీ",
            "ఆరోగ్య శ్రీ",
            "వైఎస్సార్ ఆరోగ్యశ్రీ",
        ],
        "historical_aliases": [
            "aarogyasri",
            "arogyasri",
            "aarogya sri",
            "arogya sri",
            "ysr aarogyasri",
            "ఆరోగ్యశ్రీ",
            "ఆరోగ్య శ్రీ",
            "వైఎస్సార్ ఆరోగ్యశ్రీ",
        ],
        "historical_note_en": (
            "Aarogyasri is co-branded and administered under the Dr. NTR Vaidya Seva health insurance framework in Andhra Pradesh."
        ),
        "historical_note_te": (
            "ఆరోగ్యశ్రీ ఆరోగ్య రక్షణ పథకం ఆంధ్రప్రదేశ్ ప్రభుత్వంలో డాక్టర్ ఎన్టీఆర్ వైద్య సేవ పథకంతో కలిపి సమగ్రంగా అమలు చేయబడుతోంది."
        ),
    },
    "schemes_pedalandariki_illu_housing": {
        "doc_id": "schemes_pedalandariki_illu_housing",
        "title": "Pedalandariki Illu Housing Scheme Guidelines and Construction Subsidies",
        "current_name": "Pedalandariki Illu Housing",
        "domain": "schemes",
        "portal_url": "https://housing.ap.gov.in",
        "aliases": [
            "pedalandariki illu",
            "pedalandarikiillu",
            "housing scheme",
            "house site",
            "house site patta",
            "apshcl",
            "navaratnalu pedalandariki illu",
            "housing subsidy",
            "housing assistance",
            "పేదలందరికీ ఇళ్లు",
            "పేదలందరికీ ఇల్లు",
            "పేదలందరికీఇళ్లు",
            "ఇళ్ల స్థలాలు",
            "ఇళ్ల స్థలాల",
            "ఇళ్ల పట్టాలు",
            "ఇళ్ల స్థలాల పట్టాలు",
            "గృహ నిర్మాణం",
            "గృహ నిర్మాణ",
            "గృహ నిర్మాణ రాయితీ",
            "హౌసింగ్ స్కీమ్",
        ],
        "historical_aliases": [],
    },
    "schemes_ntr_bharosa_pension": {
        "doc_id": "schemes_ntr_bharosa_pension",
        "title": "NTR Bharosa Social Security Pension Scheme Guidelines",
        "current_name": "NTR Bharosa Pension",
        "domain": "schemes",
        "portal_url": "https://sspensions.ap.gov.in",
        "aliases": [
            "ntr bharosa",
            "ntrbharosa",
            "bharosa pension",
            "social security pension",
            "pension kanuka",
            "ysr pension kanuka",
            "pensionkanuka",
            "old age pension",
            "widow pension",
            "disability pension",
            "pension",
            "pensions",
            "పింఛన్",
            "పెన్షన్",
            "భరోసా పెన్షన్",
            "వృద్ధాప్య పింఛన్",
            "వితంతు పింఛన్",
            "దివ్యాంగుల పింఛన్",
            "ఎన్టీఆర్ భరోసా",
            "ఎన్టీఆర్భరోసా",
            "పింఛన్ కానుక",
            "పెన్షన్ కానుక",
            "పెన్షన్‌కానుక",
            "వైఎస్సార్ పెన్షన్ కానుక",
        ],
        "historical_aliases": [
            "pension kanuka",
            "ysr pension kanuka",
            "pensionkanuka",
            "పింఛన్ కానుక",
            "పెన్షన్ కానుక",
            "పెన్షన్‌కానుక",
            "వైఎస్సార్ పెన్షన్ కానుక",
        ],
        "historical_note_en": (
            "YSR Pension Kanuka was the predecessor social security pension scheme in Andhra Pradesh, "
            "restructured and enhanced under the NTR Bharosa Social Security Pension guidelines."
        ),
        "historical_note_te": (
            "గతంలో అమలులో ఉన్న వైఎస్సార్ పెన్షన్ కానుక పథకం ప్రస్తుతం ఆంధ్రప్రదేశ్ ప్రభుత్వం ద్వారా "
            "ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛన్ పథకంగా సంస్కరించబడి అమలు చేయబడుతోంది."
        ),
    },
    "schemes_mgnregs_andhra_pradesh": {
        "doc_id": "schemes_mgnregs_andhra_pradesh",
        "title": "MGNREGS Andhra Pradesh Guidelines and Wage Rights",
        "current_name": "MGNREGS",
        "domain": "schemes",
        "portal_url": "https://nrega.nic.in",
        "aliases": [
            "mgnregs",
            "nrega",
            "mgnrega",
            "job card",
            "100 days wage employment",
            "100 days employment",
            "rural employment guarantee",
            "rozgar",
            "ఉపాధి హామీ",
            "ఉపాధి హామీ పథకం",
            "ఉపాధిహామీ",
            "జాబ్ కార్డు",
            "జాబ్ కార్డ్",
            "జాబ్‌కార్డు",
            "100 రోజుల ఉపాధి",
            "గ్రామీణ ఉపాధి హామీ",
        ],
        "historical_aliases": [],
    },
    "schemes_grama_ward_sachivalayam": {
        "doc_id": "schemes_grama_ward_sachivalayam",
        "title": "Grama and Ward Sachivalayam Citizen Service Delivery System",
        "current_name": "Grama and Ward Sachivalayam",
        "domain": "schemes",
        "portal_url": "https://gramawardsachivalayam.ap.gov.in",
        "aliases": [
            "grama sachivalayam",
            "ward sachivalayam",
            "grama ward sachivalayam",
            "village secretariat",
            "ward secretariat",
            "sachivalayam",
            "gramasachivalayam",
            "wardsachivalayam",
            "గ్రామ సచివాలయం",
            "వార్డు సచివాలయం",
            "గ్రామ వార్డు సచివాలయం",
            "సచివాలయం",
            "గ్రామసచివాలయం",
            "వార్డుసచివాలయం",
        ],
        "historical_aliases": [],
    },
}

# Precedence order: Specific welfare schemes have higher priority than generic delivery channels
# This prevents a question like "Annadata Sukhibhava at Grama Sachivalayam" from routing to Grama Sachivalayam doc
SCHEME_PRECEDENCE: List[str] = [
    "agri_annadata_sukhibhava_pmkisan",
    "agri_kisan_credit_card",
    "agri_pm_crop_insurance_ap",
    "agri_soil_health_card_polam_badi",
    "edu_thalliki_vandanam_scheme",
    "edu_vidya_deevena_vasathi_deevena",
    "edu_samagra_shiksha_ap",
    "health_dr_ntr_vaidya_seva_aarogyasri",
    "health_ayushman_bharat_pmjay_ap",
    "health_104_108_emergency_health_services",
    "schemes_pedalandariki_illu_housing",
    "schemes_ntr_bharosa_pension",
    "schemes_mgnregs_andhra_pradesh",
    "schemes_grama_ward_sachivalayam",
]

# Generic administrative tokens that must NEVER match a scheme by themselves
GENERIC_DISALLOWED_TOKENS: Set[str] = {
    "ap", "andhra", "pradesh", "government", "govt", "scheme", "schemes",
    "yojana", "pathakam", "prabhutvam", "details", "guidelines", "status",
    "apply", "application", "subsidy", "assistance", "benefit", "services",
    "portal", "official", "rules", "amma", "ntr", "illu", "kisan", "bharosa",
    "పథకం", "పథకాలు", "పథకానికి", "ప్రభుత్వం", "ఆంధ్రప్రదేశ్", "వివరాలు", "సేవలు",
}


def normalize_text(text: str) -> str:
    """
    Normalizes user text for reliable comparison:
    - Unicode NFKC normalization
    - Lowercasing
    - Replacing punctuation with spaces (preserving Telugu range \u0C00-\u0C7F and alphanumeric)
    - Collapsing excess whitespace
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^\w\s\u0C00-\u0C7F]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_ambiguous_ntr_query(query: str) -> bool:
    """
    Checks if query mentions 'NTR' in isolation without clarifying whether it refers
    to NTR Bharosa Pension (schemes) or Dr. NTR Vaidya Seva (healthcare).
    """
    norm = normalize_text(query)
    words = set(norm.split())
    has_ntr = "ntr" in words or "ఎన్టీఆర్" in words or "ఎన్టీఆర" in words

    if not has_ntr:
        return False

    has_pension_context = any(
        w in norm for w in [
            "bharosa", "pension", "pensions", "భరోసా", "పింఛన్", "పెన్షన్",
            "వృద్ధాప్య", "వితంతు", "దివ్యాంగుల", "old age", "widow", "disability",
        ]
    )
    has_health_context = any(
        w in norm for w in [
            "vaidya", "seva", "aarogya", "arogya", "aarogyasri", "hospital",
            "health", "medical", "treatment", "వైద్య", "సేవ", "ఆరోగ్య",
            "ఆరోగ్యశ్రీ", "ఆసుపత్రి", "చికిత్స",
        ]
    )

    # It is ambiguous ONLY if it mentions NTR in isolation with NEITHER pension nor health context.
    # If both contexts are present (e.g. comparison between NTR Bharosa and Dr NTR Vaidya Seva), both schemes are known.
    return has_ntr and not has_pension_context and not has_health_context


def detect_named_schemes(query: str) -> List[str]:
    """
    Identifies whether any official scheme is explicitly named in the query.
    Supports spaced and unspaced representations (e.g. 'Ammavodi' vs 'Amma Vodi', 'అమ్మఒడి' vs 'అమ్మ ఒడి').
    Returns ordered list of matched canonical document IDs, respecting scheme precedence.
    """
    if not query or not query.strip():
        return []

    norm_q = normalize_text(query)
    if not norm_q:
        return []

    unspaced_q = re.sub(r"\s+", "", norm_q)
    spaced_q_with_pads = f" {norm_q} "
    q_words = set(norm_q.split())

    # Special check: If query is purely ambiguous NTR, do not lock into one scheme
    if is_ambiguous_ntr_query(query):
        return []

    matched_ids: List[str] = []

    for doc_id in SCHEME_PRECEDENCE:
        info = SCHEME_REGISTRY.get(doc_id)
        if not info:
            continue

        aliases = info.get("aliases", [])
        matched = False

        for alias in aliases:
            norm_alias = normalize_text(alias)
            if not norm_alias:
                continue

            # Disallow matching generic standalone tokens
            if norm_alias in GENERIC_DISALLOWED_TOKENS:
                continue

            # Check 1: Spaced match (whole phrase or word boundary)
            if " " in norm_alias:
                if f" {norm_alias} " in spaced_q_with_pads:
                    matched = True
                    break
            else:
                # Single-word token:
                # For short acronyms (e.g. '104', '108', 'kcc', 'rtf', 'mtf', 'pmfby', 'pmjay')
                if len(norm_alias) <= 5:
                    if norm_alias in q_words:
                        matched = True
                        break
                else:
                    # Longer single-word (e.g. 'annadata', 'sukhibhava', 'polambadi', 'sachivalayam', 'mgnregs', 'ఉపాధిహామీ')
                    if norm_alias in q_words or f" {norm_alias} " in spaced_q_with_pads:
                        matched = True
                        break

            # Check 2: Unspaced / joined compound word match
            # Applicable for multi-word or compound aliases of substantial length (>= 6 chars English, >= 5 chars Telugu)
            unspaced_alias = re.sub(r"\s+", "", norm_alias)
            is_telugu = any('\u0C00' <= c <= '\u0C7F' for c in unspaced_alias)
            min_unspaced_len = 5 if is_telugu else 6

            if len(unspaced_alias) >= min_unspaced_len and unspaced_alias not in GENERIC_DISALLOWED_TOKENS:
                if unspaced_alias in unspaced_q:
                    matched = True
                    break

        if matched and doc_id not in matched_ids:
            matched_ids.append(doc_id)

    # Precedence resolution: If a specific scheme was matched alongside Grama Sachivalayam,
    # prioritize the specific scheme and drop the generic delivery channel
    if len(matched_ids) > 1 and "schemes_grama_ward_sachivalayam" in matched_ids:
        matched_ids = [m for m in matched_ids if m != "schemes_grama_ward_sachivalayam"]

    return matched_ids


def detect_scheme_details(query: str) -> Dict[str, Any]:
    """
    Returns rich detection details:
    - matched_doc_ids: List of canonical doc IDs
    - primary_doc_id: Top matched doc ID
    - is_historical: Whether the user referred to a historical/predecessor scheme
    - historical_name: Predecessor name if matched
    - current_name: Current official scheme name
    - historical_note_en: Contextual explanation in English
    - historical_note_te: Contextual explanation in Telugu
    - is_ambiguous_ntr: Whether query has ambiguous NTR mention
    """
    result: Dict[str, Any] = {
        "matched_doc_ids": [],
        "primary_doc_id": None,
        "is_historical": False,
        "historical_name": None,
        "current_name": None,
        "historical_note_en": None,
        "historical_note_te": None,
        "is_ambiguous_ntr": is_ambiguous_ntr_query(query),
    }

    if result["is_ambiguous_ntr"]:
        return result

    matched = detect_named_schemes(query)
    result["matched_doc_ids"] = matched

    if not matched:
        return result

    primary_id = matched[0]
    result["primary_doc_id"] = primary_id
    info = SCHEME_REGISTRY.get(primary_id, {})
    result["current_name"] = info.get("current_name")

    # Check if matched via a historical alias
    norm_q = normalize_text(query)
    unspaced_q = re.sub(r"\s+", "", norm_q)
    spaced_q = f" {norm_q} "

    for hist_alias in info.get("historical_aliases", []):
        norm_h = normalize_text(hist_alias)
        unspaced_h = re.sub(r"\s+", "", norm_h)
        if f" {norm_h} " in spaced_q or (len(unspaced_h) >= 5 and unspaced_h in unspaced_q):
            result["is_historical"] = True
            result["historical_name"] = hist_alias
            result["historical_note_en"] = info.get("historical_note_en")
            result["historical_note_te"] = info.get("historical_note_te")
            break

    return result
