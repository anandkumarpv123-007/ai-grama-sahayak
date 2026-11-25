import logging
import uuid
import re
import time
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status
from app.schemas.chat import ChatRequest, ChatResponse, Source
from app.schemas.common import AssistantIdentifier, LanguageCode
from app.agents.router import agent_router
from app.core.retrieval_client import fetch_retrieval_context
from app.core.emergency_detector import check_clinical_emergency
from app.core.scheme_ambiguity_detector import (
    is_ambiguous_scheme_query,
    get_scheme_clarification_response,
)
from app.services.retrieval.scheme_registry import (
    detect_named_schemes,
    detect_scheme_details,
    is_ambiguous_ntr_query,
    normalize_text,
    SCHEME_REGISTRY,
)
from app.services.locations.service_finder import find_nearby_services
from app.core.exceptions import BadRequestException
from app.database.session import get_session_factory
from app.models.conversation import Conversation
from app.models.message import ChatMessage

logger = logging.getLogger("ai_grama_sahayak.api.chat")

router = APIRouter()


def _save_chat_interaction_safely(
    conv_id: str,
    request: ChatRequest,
    response: ChatResponse,
) -> None:
    """
    Safely records conversation and message in PostgreSQL if available.
    Never fails the user's chat request if database is unreachable.
    """
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            # Check if conversation exists
            conv = (
                session.query(Conversation)
                .filter(Conversation.conversation_id == conv_id)
                .first()
            )
            if not conv:
                conv = Conversation(
                    conversation_id=conv_id,
                    assistant=request.assistant.value,
                    language=request.language.value,
                    state=request.state,
                    district=request.district,
                )
                session.add(conv)
            else:
                conv.assistant = request.assistant.value
                conv.language = request.language.value
                if request.state:
                    conv.state = request.state
                if request.district:
                    conv.district = request.district

            # Record citizen query message
            user_msg = ChatMessage(
                conversation_id=conv_id,
                role="user",
                content=request.message,
                sources=None,
            )
            session.add(user_msg)

            # Record assistant response message
            sources_json = [s.model_dump() for s in response.sources]
            assistant_msg = ChatMessage(
                conversation_id=conv_id,
                role="assistant",
                content=response.answer,
                sources=sources_json if sources_json else None,
            )
            session.add(assistant_msg)
            session.commit()
    except Exception as exc:
        logger.debug("Database interaction persistence skipped/failed: %s", exc)


def _handle_ambiguous_ntr(language: LanguageCode) -> Dict[str, Any]:
    """
    Returns clarification response when citizen asks about 'NTR' in isolation.
    Distinguishes between NTR Bharosa Pension (schemes) and Dr. NTR Vaidya Seva (healthcare).
    """
    if language == LanguageCode.TE:
        answer = (
            "ఆంధ్రప్రదేశ్‌లో 'ఎన్టీఆర్' పేరుతో రెండు ప్రధాన ప్రజా సంక్షేమ కార్యక్రమాలు అమలులో ఉన్నాయి. "
            "మీరు ఏ కార్యక్రమం గురించి సమాచారం తెలుసుకోవాలనుకుంటున్నారో దయచేసి స్పష్టం చేయండి:\n\n"
            "1. **ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛను**: వృద్ధులు, వితంతువులు, దివ్యాంగులు మరియు చేతివృత్తుల వారికి అందించే నెలవారీ పింఛను పథకం.\n"
            "2. **డాక్టర్ ఎన్టీఆర్ వైద్య సేవ**: నెట్‌వర్క్ ఆసుపత్రులలో ఉచిత నగదు రహిత వైద్య చికిత్స మరియు శస్త్రచికిత్సలు అందించే ఆరోగ్య రక్షణ పథకం (గతంలో ఆరోగ్యశ్రీ).\n\n"
            "దయచేసి 'ఎన్టీఆర్ భరోసా పింఛన్' లేదా 'డాక్టర్ ఎన్టీఆర్ వైద్య సేవ' అని సమాధానం ఇవ్వండి."
        )
        follow_ups = [
            "ఎన్టీఆర్ భరోసా పింఛన్ అర్హతలు మరియు మార్గదర్శకాలు తెలుసుకోవాలనుకుంటున్నారా?",
            "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ ఉచిత చికిత్సల వివరాలు కావాలా?",
        ]
        safety_notice = (
            "పథకాల సలహా: ప్రభుత్వ సంక్షేమ పథకాల నిబంధనలు ప్రభుత్వం జారీ చేసిన అధికారిక ఉత్తర్వులకు (GOs) లోబడి ఉంటాయి. "
            "దరఖాస్తులను మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో మాత్రమే సమర్పించండి."
        )
    else:
        answer = (
            "In Andhra Pradesh, 'NTR' refers to two major distinct government welfare initiatives. "
            "Please specify which initiative you would like verified information about:\n\n"
            "1. **NTR Bharosa Social Security Pension**: Monthly welfare pension for senior citizens (OAP), widows, "
            "persons with disabilities, and traditional occupational beneficiaries.\n"
            "2. **Dr. NTR Vaidya Seva**: Government health insurance scheme providing cashless hospitalization and "
            "tertiary medical treatment at empaneled network hospitals (formerly known as Aarogyasri).\n\n"
            "Please reply with 'NTR Bharosa Pension' or 'Dr. NTR Vaidya Seva' for verified guidelines."
        )
        follow_ups = [
            "Would you like details on NTR Bharosa Pension eligibility and categories?",
            "Would you like details on Dr. NTR Vaidya Seva cashless hospital coverage?",
        ]
        safety_notice = (
            "Public Schemes Advisory: Welfare scheme eligibility thresholds and benefit modalities are subject to "
            "official government orders. Submit applications directly via your local Grama / Ward Sachivalayam."
        )

    return {
        "answer": answer,
        "follow_up_questions": follow_ups,
        "safety_notice": safety_notice,
    }


class BoundedConversationMemory:
    """
    Thread-safe, LRU-bounded in-memory store for multi-turn conversation scheme context.
    - Prevents unbounded memory growth in production by capping maximum tracked conversations (default 500).
    - Enforces TTL expiration (default 30 minutes / 1800s) on conversation entries.
    - Isolates conversation state across distinct conversation_ids.
    - Stores strictly minimal scheme context needed for resolution (zero citizen PII).
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 1800):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, conv_id: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not conv_id:
            return default
        with self._lock:
            if conv_id not in self._store:
                return default
            entry = self._store[conv_id]
            now = time.time()
            if now - entry.get("updated_at", 0) > self.ttl_seconds:
                del self._store[conv_id]
                return default
            self._store.move_to_end(conv_id)
            return {
                "last_scheme_id": entry.get("last_scheme_id"),
                "last_scheme_name": entry.get("last_scheme_name"),
                "last_assistant": entry.get("last_assistant"),
            }

    def set(
        self,
        conv_id: str,
        scheme_id: str,
        scheme_name: str,
        assistant: Optional[Any] = None,
    ) -> None:
        if not conv_id:
            return
        with self._lock:
            now = time.time()
            if conv_id in self._store:
                self._store.move_to_end(conv_id)
            self._store[conv_id] = {
                "last_scheme_id": scheme_id,
                "last_scheme_name": scheme_name,
                "last_assistant": assistant,
                "updated_at": now,
            }
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def cleanup_expired(self) -> int:
        """Removes expired entries and returns count of removed items."""
        now = time.time()
        pruned = 0
        with self._lock:
            expired_keys = [
                k for k, v in self._store.items()
                if now - v.get("updated_at", 0) > self.ttl_seconds
            ]
            for k in expired_keys:
                del self._store[k]
                pruned += 1
        return pruned

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __contains__(self, conv_id: str) -> bool:
        return self.get(conv_id) is not None

    def __getitem__(self, conv_id: str) -> Dict[str, Any]:
        val = self.get(conv_id)
        if val is None:
            raise KeyError(conv_id)
        return val

    def __setitem__(self, conv_id: str, value: Dict[str, Any]) -> None:
        self.set(
            conv_id=conv_id,
            scheme_id=value.get("last_scheme_id", ""),
            scheme_name=value.get("last_scheme_name", ""),
            assistant=value.get("last_assistant"),
        )

    def __len__(self) -> int:
        with self._lock:
            now = time.time()
            return sum(1 for v in self._store.values() if now - v.get("updated_at", 0) <= self.ttl_seconds)


# Bounded in-memory conversation state for multi-turn contextual queries
_CONVERSATION_MEMORY = BoundedConversationMemory(max_size=500, ttl_seconds=1800)
_CONVERSATION_HISTORY = _CONVERSATION_MEMORY

CONTEXT_PATTERNS = [
    re.compile(r"\b(?:this|the|that)\s+scheme\b", re.IGNORECASE),
    re.compile(r"\b(?:for\s+this|for\s+it|about\s+this|about\s+it)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:do\s+i|to|can\s+i)\s+apply(?:\s+for\s+(?:this|the|that)\s+scheme)?\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:are\s+the\s+)?(?:documents?|papers?|proofs?)\s+(?:needed|required|for\s+this)\b", re.IGNORECASE),
    re.compile(r"\b(?:who\s+is\s+eligible|eligibility\s+criteria|what\s+are\s+the\s+benefits)\b", re.IGNORECASE),
    re.compile(r"దీనికి|ఈ\s*పథక(?:ం|ానికి)|ఆ\s*పథక(?:ం|ానికి)|దీని\s*(?:గురించి|అర్హతలు|పత్రాలు|ప్రయోజనాలు)"),
    re.compile(r"ఎలా\s*దరఖాస్తు|కావాల్సిన\s*పత్రాలు|ఎవరు\s*అర్హులు|ప్రయోజనాలు\s*ఏమిటి"),
]


def _is_contextual_query(query: str) -> bool:
    return any(p.search(query) for p in CONTEXT_PATTERNS)


def _detect_unsupported_scheme(query: str) -> Optional[str]:
    """
    Detects whether user is querying a specific named scheme outside our verified KB.
    E.g. 'Explain about PMXYZ scheme.' -> 'PMXYZ'
    """
    if detect_named_schemes(query):
        return None
    # Match uppercase / acronym scheme names like PMXYZ scheme
    m = re.search(r"\b([A-Z0-9_\-]{3,})\s+(?:scheme|yojana|program|పథక|పథకం)\b", query)
    if m:
        cand = m.group(1).strip()
        if cand.upper() not in {"THE", "ANY", "OUR", "AP", "GOVT", "FOR"}:
            return cand
    return None


def _handle_unsupported_scheme(scheme_name: str, language: LanguageCode) -> Dict[str, Any]:
    if language == LanguageCode.TE:
        answer = (
            f"'{scheme_name}' పథకానికి సంబంధించి ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం AI గ్రామ సహాయక్ నాలెడ్జ్ బేస్‌లో అందుబాటులో లేదు.\n\n"
            "AI గ్రామ సహాయక్ ప్రస్తుతం ఆంధ్రప్రదేశ్ మరియు కేంద్ర ప్రభుత్వ సంక్షేమ పథకాలపై (అన్నదాత సుఖీభవ – పీఎం కిసాన్, తల్లికి వందనం, ఎన్టీఆర్ భరోసా పింఛన్, డాక్టర్ ఎన్టీఆర్ వైద్య సేవ, ఉపాధి హామీ) మాత్రమే ధృవీకరించిన సమాచారాన్ని అందిస్తుంది.\n\n"
            "ఇతర పథకాల అధికారిక వివరాల కొరకు:\n"
            "• ఆంధ్రప్రదేశ్ ప్రభుత్వ అధికారిక పోర్టల్ చూడండి: https://www.ap.gov.in\n"
            "• జాతీయ సేవల పోర్టల్ చూడండి: https://india.gov.in\n"
            "• లేదా మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
        )
        follow_ups = [
            "రైతుల కోసం అన్నదాత సుఖీభవ – పీఎం కిసాన్ వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
            "ఎన్టీఆర్ భరోసా సామాజిక భద్రత పింఛను వివరాలు కావాలా?",
            "విద్యార్థుల కోసం తల్లికి వందనం పథకం వివరాలు కావాలా?",
        ]
        safety_notice = (
            "పథకాల సలహా: ధృవీకరించబడిన ప్రభుత్వ పథకాల వివరాలు మాత్రమే ఇక్కడ అందించబడతాయి. "
            "ఏదైనా కొత్త పథకం దరఖాస్తుకు మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
        )
    else:
        answer = (
            f"Verified official information for '{scheme_name} Scheme' is currently unavailable in the verified knowledge base of AI Grama Sahayak.\n\n"
            "AI Grama Sahayak currently provides verified guidance exclusively on substantiated Andhra Pradesh and Central Government welfare schemes (including Annadata Sukhibhava – PM KISAN, Thalliki Vandanam, NTR Bharosa Pension, Dr. NTR Vaidya Seva, and MGNREGS).\n\n"
            "To check official guidelines for other schemes:\n"
            "• Visit the official Government of Andhra Pradesh portal: https://www.ap.gov.in\n"
            "• Visit the National Government Services Portal: https://india.gov.in\n"
            "• Inquire directly at your local Grama / Ward Sachivalayam for official government orders."
        )
        follow_ups = [
            "Would you like details on Farmer Support (Annadata Sukhibhava – PM KISAN)?",
            "Would you like details on Social Security Pensions (NTR Bharosa)?",
            "Would you like details on School Education Support (Thalliki Vandanam)?",
        ]
        safety_notice = (
            "Public Schemes Advisory: Information is provided only for verified government programs. "
            "Always consult official government portals or your local Grama / Ward Sachivalayam."
        )

    return {
        "answer": answer,
        "follow_up_questions": follow_ups,
        "safety_notice": safety_notice,
    }


def _handle_unspecified_scheme_application(language: LanguageCode) -> Dict[str, Any]:
    if language == LanguageCode.TE:
        answer = (
            "మీరు ఏ ప్రభుత్వ సంక్షేమ పథకానికి దరఖాస్తు చేసుకోవాలనుకుంటున్నారో దయచేసి ఆ పథకం పేరును తెలియజేయండి.\n\n"
            "ఉదాహరణకు:\n"
            "• అన్నదాత సుఖీభవ – పీఎం కిసాన్ (రైతులకు పెట్టుబడి సాయం)\n"
            "• తల్లికి వందనం (పాఠశాల విద్యార్థుల తల్లులకు విద్యా ప్రోత్సాహకం)\n"
            "• ఎన్టీఆర్ భరోసా పింఛన్ (వృద్ధులు, వితంతువులు, దివ్యాంగులకు నెలవారీ పింఛను)\n"
            "• డాక్టర్ ఎన్టీఆర్ వైద్య సేవ (నెట్‌వర్క్ ఆసుపత్రులలో ఉచిత నగదు రహిత చికిత్స)\n"
            "• ఉపాధి హామీ పథకం (MGNREGS జాబ్ కార్డు & కూలీ పనులు)\n\n"
            "మీకు కావలసిన పథకం పేరును తెలిపితే, ఖచ్చితమైన దరఖాస్తు విధానం, అవసరమైన పత్రాలు మరియు అధికారిక పోర్టల్స్ వివరాలను అందిస్తాను."
        )
        follow_ups = [
            "అన్నదాత సుఖీభవ దరఖాస్తు విధానం తెలుసుకోవాలనుకుంటున్నారా?",
            "తల్లికి వందనం దరఖాస్తు పద్ధతి కావాలా?",
            "ఎన్టీఆర్ భరోసా పింఛనుకు ఎలా దరఖాస్తు చేయాలో వివరాలు కావాలా?",
        ]
        safety_notice = "పథకాల సలహా: ప్రభుత్వ సంక్షేమ పథకాల దరఖాస్తులను మీ అధికారిక గ్రామ/వార్డు సచివాలయంలో మాత్రమే సమర్పించండి."
    else:
        answer = (
            "Which government welfare scheme would you like to apply for? "
            "Please specify the scheme name so that I can provide the verified step-by-step application procedure, required documents, and official portals.\n\n"
            "For example:\n"
            "• Annadata Sukhibhava – PM KISAN (Farmer investment support)\n"
            "• Thalliki Vandanam (School education financial assistance for mothers)\n"
            "• NTR Bharosa Pension (Monthly social security pension for senior citizens, widows, disabled)\n"
            "• Dr. NTR Vaidya Seva (Cashless hospitalization at empaneled network hospitals)\n"
            "• MGNREGS (Rural wage employment and Job Card enrollment)\n\n"
            "Please reply with the scheme name you are interested in applying for."
        )
        follow_ups = [
            "Would you like to know how to apply for Annadata Sukhibhava – PM KISAN?",
            "Would you like application steps for Thalliki Vandanam?",
            "Would you like details on applying for NTR Bharosa Pension?",
        ]
        safety_notice = "Public Schemes Advisory: Always submit welfare scheme applications through your local Grama / Ward Sachivalayam or official government portals."

    return {
        "answer": answer,
        "follow_up_questions": follow_ups,
        "safety_notice": safety_notice,
    }


def _detect_apssdc_query(query: str) -> bool:
    """Detects inquiries regarding APSSDC, technical skills, or vocational training."""
    q_lower = query.lower()
    q_norm = normalize_text(query)
    apssdc_terms = [
        "apssdc", "technical skill", "skill training", "skill development",
        "technical training", "vocational training", "skill program",
        "నైపుణ్యాభివృద్ధి", "స్కిల్ డెవలప్‌మెంట్", "సాంకేతిక శిక్షణ", "నైపుణ్య శిక్షణ",
    ]
    return any(t in q_lower or t in q_norm for t in apssdc_terms)


def _handle_apssdc_query(language: LanguageCode) -> Dict[str, Any]:
    """Provides honest, verified information about APSSDC technical skill programs."""
    if language == LanguageCode.TE:
        answer = (
            "ఆంధ్రప్రదేశ్ రాష్ట్ర నైపుణ్యాభివృద్ధి సంస్థ (APSSDC) రాష్ట్రంలోని విద్యార్థులు మరియు నిరుద్యోగ యువతకు ఉపాధి ఆధారిత సాంకేతిక మరియు వృత్తి నైపుణ్య శిక్షణ కార్యక్రమాలను సమన్వయం చేస్తుంది.\n\n"
            "**ముఖ్యమైన వ్యత్యాసం:**\n"
            "• **నైపుణ్య శిక్షణ vs. స్కాలర్‌షిప్‌లు:** APSSDC కార్యక్రమాలు పరిశ్రమలకు అవసరమైన సాంకేతిక శిక్షణ మరియు ఉపాధి అవకాశాలపై దృష్టి సారిస్తాయి; ఇవి నగదు లేదా విద్యా స్కాలర్‌షిప్‌లు కావు. అకడమిక్ చదువుల స్కాలర్‌షిప్‌ల కొరకు జగనన్న విద్యా దీవెన (ఫీజు రీయింబర్స్‌మెంట్), వసతి దీవెన లేదా తల్లికి వందనం పథకాలను పరిశీలించండి.\n\n"
            "**ధృవీకరించబడిన APSSDC వివరాలు:**\n"
            "• **శిక్షణా రంగాలు:** సాంకేతిక రంగాలు (IT, కంప్యూటర్ సైన్స్, ఎమర్జింగ్ టెక్నాలజీస్), పరిశ్రమల ఆధారిత వృత్తి నైపుణ్యాలు మరియు స్వయం ఉపాధి శిక్షణ.\n"
            "• **ప్రత్యక్ష వివరాలు:** నిర్దిష్ట కోర్సుల బ్యాచ్‌లు, ఫీజు మినహాయింపులు, తరగతుల ప్రారంభ తేదీలు మరియు శిక్షణా కేంద్రాల జాబితా జిల్లాల వారీగా మరియు అధికారిక నోటిఫికేషన్ల ఆధారంగా మారుతూ ఉంటాయి.\n"
            "• **అధికారికంగా దరఖాస్తు చేసుకునే విధానం:**\n"
            "  - APSSDC అధికారిక పోర్టల్ సందర్శించండి: https://www.apssdc.in\n"
            "  - AP స్కిల్ యూనివర్స్ (Skill Universe) పోర్టల్ ద్వారా ప్రస్తుత బ్యాచ్‌లలో నమోదు చేసుకోండి.\n"
            "  - మీ స్థానిక గ్రామ/వార్డు సచివాలయంలోని విద్య మరియు డేటా ప్రాసెసింగ్ కార్యదర్శిని (Education Assistant) సంప్రదించి స్కిల్ సెన్సస్ వివరాలు తెలుసుకోండి.\n\n"
            "మీ ప్రస్తుత విద్యార్హత (ఉదా: డిగ్రీ, ఇంజనీరింగ్, ఐటీఐ/డిప్లొమా) మరియు మీరు ఆసక్తి ఉన్న రంగాన్ని తెలియజేయండి."
        )
        follow_ups = [
            "విద్యా దీవెన మరియు వసతి దీవెన స్కాలర్‌షిప్ వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
            "గ్రామ సచివాలయంలో నైపుణ్య గణన (Skill Census) ప్రక్రియ గురించి సమాచారం కావాలా?",
            "విద్యార్థుల ఇంటర్న్‌షిప్‌ల కోసం చూస్తున్నారా లేక ఉద్యోగ నియామక శిక్షణ కోసమా?",
        ]
        safety_notice = (
            "నైపుణ్యాభివృద్ధి సలహా: శిక్షణా కోర్సులు మరియు బ్యాచ్‌ల వివరాల కోసం అధికారిక వెబ్‌సైట్ https://www.apssdc.in ను మాత్రమే సంప్రదించండి. అనధికార వ్యక్తులకు లేదా ప్రైవేట్ ఏజెంట్లకు ఎటువంటి రుసుములు చెల్లించవద్దు."
        )
    else:
        answer = (
            "The Andhra Pradesh State Skill Development Corporation (APSSDC) coordinates technical, employability, and vocational skill training programs for youth, students, and jobseekers across Andhra Pradesh.\n\n"
            "**Key Distinction:**\n"
            "• **Skill Training vs. Scholarships:** APSSDC programs focus on skill development, industry internships, and employment enablement; they do not provide direct academic financial scholarships. For academic scholarships, please consult state educational welfare programs like Jagananna Vidya Deevena (full tuition fee reimbursement) or Thalliki Vandanam.\n\n"
            "**Verified APSSDC Information:**\n"
            "• **Scope:** Technical domains (IT, computer software, emerging technologies), manufacturing/industrial trades, and self-employment skill workshops.\n"
            "• **Dynamic Batches:** Specific active course schedules, empanelled training centres, and eligibility criteria vary dynamically by district and official government notifications.\n"
            "• **How to Verify and Apply:**\n"
            "  - Visit the official APSSDC portal: https://www.apssdc.in\n"
            "  - Explore active training drives via the AP Skill Universe portal.\n"
            "  - Inquire with the Education & Data Processing Secretary at your local Grama / Ward Sachivalayam regarding local Skill Census and mobilization drives.\n\n"
            "What is your current educational qualification (e.g., Engineering, Degree, ITI/Diploma) and preferred domain of training?"
        )
        follow_ups = [
            "Would you like details on academic scholarships like Vidya Deevena and Vasathi Deevena?",
            "Would you like information on citizen skill enrollment at Grama Sachivalayam?",
            "Are you looking for student internships or jobseeker placement drives?",
        ]
        safety_notice = (
            "APSSDC Advisory: Skill training offerings, batch schedules, and empanelled centres are updated dynamically on https://www.apssdc.in. Never pay unauthorized agents for government skill registrations."
        )

    return {
        "answer": answer,
        "sources": [],
        "needs_follow_up": True,
        "follow_up_questions": follow_ups,
        "safety_notice": safety_notice,
    }


SCHOLARSHIP_TYPO_PATTERN = re.compile(
    r"\b(?:avail[a-z]*\s+)?(?:scholar\s*ships?|schoalr\s*ships?|scolar\s*ships?|skolar\s*ships?)\b|"
    r"స్కాలర్\s*షిప్|స్కాలర్‌షిప్|స్కాలర్‌షిప్‌లు|స్కాలర్షిప్‌లు",
    re.IGNORECASE,
)


def _detect_generic_scholarship_query(query: str) -> bool:
    """Detects general inquiries and typographical variants for scholarships."""
    q_lower = query.lower()
    if SCHOLARSHIP_TYPO_PATTERN.search(query):
        return True
    if any(p in q_lower for p in ["scholarship", "schoalrship", "scolarship"]):
        return True
    return False


def _handle_generic_scholarship_query(language: LanguageCode) -> Dict[str, Any]:
    """Provides structured, tiered scholarship options across school and higher education."""
    sources = [
        Source(
            title="Thalliki Vandanam Scheme",
            url="https://jnanabhumi.ap.gov.in",
            publisher="Department of School Education, Government of Andhra Pradesh",
            verified_at="2026-11-21",
        ),
        Source(
            title="Jagananna Vidya Deevena & Vasathi Deevena",
            url="https://jnanabhumi.ap.gov.in",
            publisher="Department of Higher Education, Government of Andhra Pradesh",
            verified_at="2026-11-21",
        ),
    ]

    if language == LanguageCode.TE:
        answer = (
            "ఆంధ్రప్రదేశ్‌లో విద్యార్థుల కోసం ప్రభుత్వం అందిస్తున్న ప్రధాన స్కాలర్‌షిప్‌లు మరియు విద్యా ప్రోత్సాహక పథకాలు ఇక్కడ ఉన్నాయి:\n\n"
            "1. **పాఠశాల విద్య (1 నుండి 12వ తరగతి):**\n"
            "   • **తల్లికి వందనం:** పాఠశాలకు వెళ్లే ప్రతి అర్హత గల విద్యార్థి తల్లి బ్యాంకు ఖాతాలో ఏటా రూ. 15,000 ఆర్థిక సాయం జమ చేయబడుతుంది (కనీసం 75% పాఠశాల హాజరు తప్పనిసరి).\n"
            "   • **సమగ్ర శిక్ష:** ప్రభుత్వ పాఠశాల విద్యార్థులకు ఉచిత పాఠ్యపుస్తకాలు, యూనిఫారాలు మరియు సమగ్ర విద్యా వనరులు.\n\n"
            "2. **పోస్ట్-మెట్రిక్ & ఉన్నత విద్య (పాలిటెక్నిక్, ఐటీఐ, డిగ్రీ, ఇంజనీరింగ్, మెడిసిన్, పీజీ):**\n"
            "   • **జగనన్న విద్యా దీవెన:** అర్హులైన ఉన్నత విద్యా విద్యార్థులకు పూర్తి కళాశాల ట్యూషన్ ఫీజు రీయింబర్స్‌మెంట్ తల్లుల ఖాతాలో జమ అవుతుంది (75% హాజరు మరియు వార్షిక కుటుంబ ఆదాయ నిబంధనల ప్రకారం).\n"
            "   • **జగనన్న వసతి దీవెన:** హాస్టల్ మరియు భోజన ఖర్చుల నిమిత్తం ఏటా రూ. 20,000 వరకు రెండు విడతల్లో ఆర్థిక సహాయం (ఐటీఐకి రూ. 10,000, పాలిటెక్నిక్‌కి రూ. 15,000, డిగ్రీ/ఇంజనీరింగ్‌కి రూ. 20,000).\n\n"
            "**ఖచ్చితమైన అర్హతలు మరియు దరఖాస్తు విధానం తెలపడానికి:**\n"
            "మీరు ఏ చదువు చదువుతున్నారు? (ఉదాహరణకు: 1-12వ తరగతి పాఠశాల చదువా, లేక పాలిటెక్నిక్ / ఐటీఐ / కాలేజీ డిగ్రీయా) తెలియజేయండి."
        )
        follow_ups = [
            "పాఠశాల విద్యార్థుల కోసం తల్లికి వందనం వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
            "కాలేజీ ఫీజు రీయింబర్స్‌మెంట్ కోసం జగనన్న విద్యా దీవెన అర్హతలు కావాలా?",
            "హాస్టల్ మరియు భోజన వసతి కోసం జగనన్న వసతి దీవెన వివరాలు కావాలా?",
        ]
        safety_notice = (
            "స్కాలర్‌షిప్ సలహా: విద్యా పథకాల నమోదు మరియు వివరాల కోసం అధికారిక జ్ఞానభూమి పోర్టల్ (https://jnanabhumi.ap.gov.in) లేదా మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
        )
    else:
        answer = (
            "In Andhra Pradesh, the state government provides comprehensive educational financial assistance and scholarship support across various levels of education:\n\n"
            "1. **School Education (Classes 1–12):**\n"
            "   • **Thalliki Vandanam:** Annual financial assistance of Rs 15,000 deposited into the bank account of the mother of every eligible school-going student (Class 1 to 12) maintaining at least 75% school attendance.\n"
            "   • **Samagra Shiksha:** Free textbooks, school uniforms, and inclusive educational resources for government school students.\n\n"
            "2. **Post-Matric & Higher Education (Polytechnic, ITI, Degree, Engineering, Medicine, PG):**\n"
            "   • **Jagananna Vidya Deevena:** Full tuition fee reimbursement for eligible post-matric students, credited directly to mothers' accounts to pay college fees (requires 75% attendance and family income eligibility within guidelines).\n"
            "   • **Jagananna Vasathi Deevena:** Boarding and mess maintenance assistance of up to Rs 20,000 per year (released in two installments) for ITI (Rs 10,000), Polytechnic (Rs 15,000), and Degree/Engineering/Professional students (Rs 20,000).\n\n"
            "**To guide you with the exact scheme requirements:**\n"
            "What is your current level of education (e.g., School student Class 1–12, Polytechnic/ITI, or College/University Degree)?"
        )
        follow_ups = [
            "Would you like details on Thalliki Vandanam for school students?",
            "Would you like eligibility criteria for Jagananna Vidya Deevena (college fee reimbursement)?",
            "Would you like details on Jagananna Vasathi Deevena (hostel/mess assistance)?",
        ]
        safety_notice = (
            "Scholarship Advisory: Always apply for education schemes through the official Jnanabhumi portal (https://jnanabhumi.ap.gov.in) or your local Grama / Ward Sachivalayam."
        )

    return {
        "answer": answer,
        "sources": sources,
        "needs_follow_up": True,
        "follow_up_questions": follow_ups,
        "safety_notice": safety_notice,
    }


def _handle_nearby_service_query(
    query: str,
    language: LanguageCode,
    state: Optional[str],
    district: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Detects nearby service discovery intent (Hospital/CHC, RBK, or Grama Sachivalayam).
    For Hospital/CHC: queries substantiated AP public health directories.
    For RBK/Sachivalayam: honestly explains directory scope and provides authoritative portals.
    Always includes an actionable service_action for frontend navigation.
    """
    q_norm = normalize_text(query)
    q_lower = query.lower()

    # Location intent indicators
    has_loc = any(w in q_lower or w in q_norm for w in [
        "near", "nearest", "nearby", "where", "location", "address", "find", "locate",
        "సమీప", "దగ్గర", "ఎక్కడ", "చిరునామా", "కేంద్రం ఎక్కడ", "ఆసుపత్రి ఎక్కడ",
    ])

    # Category indicators
    has_rbk = any(w in q_lower or w in q_norm for w in [
        "rbk", "rythu bharosa kendra", "rythu bharosa kendram",
        "ఆర్బీకే", "రైతు భరోసా కేంద్రం", "రైతు భరోసా కేంద్రాలు",
    ])
    has_sachivalayam = any(w in q_lower or w in q_norm for w in [
        "sachivalayam", "village secretariat", "ward secretariat",
        "సచివాలయం", "గ్రామ సచివాలయం", "వార్డు సచివాలయం",
    ])
    has_phc_chc = any(w in q_lower or w in q_norm for w in [
        "phc", "chc", "primary health", "community health",
        "ఆరోగ్య కేంద్రం", "ప్రాథమిక ఆరోగ్య కేంద్రం",
    ])
    has_hospital = any(w in q_lower or w in q_norm for w in [
        "hospital", "hospitals", "clinic", "health centre", "health center", "ggh", "kgh",
        "ఆసుపత్రి", "ఆసుపత్రులు", "హాస్పిటల్", "బోధనాసుపత్రి",
    ])
    is_scheme_q = any(w in q_lower or w in q_norm for w in [
        "vaidya seva", "aarogyasri", "pmjay", "ayushman bharat", "వైద్య సేవ", "ఆరోగ్యశ్రీ",
    ]) and not has_hospital

    if not has_loc and not any(w in q_lower for w in ["nearby", "where is", "nearest"]):
        return None

    if not (has_rbk or has_sachivalayam or has_phc_chc or has_hospital):
        return None

    if is_scheme_q:
        return None

    # Determine target category
    if has_rbk:
        target_type = "agriculture"
    elif has_sachivalayam:
        target_type = "secretariat"
    elif has_phc_chc:
        target_type = "community_health_centre"
    else:
        target_type = "hospital"

    # Identify target district from query or request parameter
    target_district = district
    ap_districts = [
        "Kakinada", "Visakhapatnam", "Guntur", "Krishna", "Chittoor",
        "Nellore", "Kurnool", "Anantapur", "Kadapa", "Prakasam",
        "Srikakulam", "Vizianagaram", "West Godavari", "East Godavari",
        "కాకినాడ", "విశాఖపట్నం", "గుంటూరు", "కృష్ణా", "చిత్తూరు",
        "నెల్లూరు", "కర్నూలు", "అనంతపురం", "కడప", "ప్రకాశం",
    ]
    for d in ap_districts:
        if d.lower() in q_lower:
            d_map = {
                "కాకినాడ": "Kakinada", "విశాఖపట్నం": "Visakhapatnam",
                "గుంటూరు": "Guntur", "కృష్ణా": "Krishna", "చిత్తూరు": "Chittoor",
                "నెల్లూరు": "Nellore", "కర్నూలు": "Kurnool", "అనంతపురం": "Anantapur",
                "కడప": "Kadapa", "ప్రకాశం": "Prakasam",
            }
            target_district = d_map.get(d, d.capitalize())
            break

    # 1. Handle Rythu Bharosa Kendra (RBK)
    if target_type == "agriculture":
        if language == LanguageCode.TE:
            answer = (
                "మీ సమీపంలోని రైతు భరోసా కేంద్రం (RBK) గ్రామ స్థాయిలో సేవలందిస్తుంది. ఖచ్చితమైన చిరునామా కోసం దయచేసి మీ జిల్లా, మండలం లేదా గ్రామం పేరును తెలియజేయండి:\n\n"
                "• **స్థానిక నెట్‌వర్క్:** ఆంధ్రప్రదేశ్‌లోని ప్రతి రెవెన్యూ గ్రామంలోనూ రైతు భరోసా కేంద్రాలు పనిచేస్తున్నాయి. రైతులందరికీ ఈ-పంట (e-Crop) నమోదు, నాణ్యమైన విత్తనాలు, ఎరువులు మరియు పంట బీమా సేవలను గ్రామ స్థాయిలోనే అందిస్తారు.\n"
                "• **డైరెక్టరీ పరిమితి:** రాష్ట్రవ్యాప్తంగా వేలాది గ్రామాలు ఉన్నందున, గ్రామ స్థాయి భౌగోళిక కోఆర్డినేట్లు (GPS) ఈ కేంద్రీకృత డైరెక్టరీలో నమోదు కాలేదు.\n"
                "• **సంప్రదించవలసిన అధికారిక మార్గాలు:**\n"
                "  - మీ గ్రామ సచివాలయంలోని గ్రామ వ్యవసాయ సహాయకుడిని (VAA) నేరుగా సంప్రదించండి.\n"
                "  - వ్యవసాయ శాఖ అధికారిక పోర్టల్ చూడండి: https://karshak.ap.gov.in\n"
                "  - గ్రామ/వార్డు సచివాలయం పోర్టల్ చూడండి: https://gramawardsachivalayam.ap.gov.in\n"
                "  - ఇతర ప్రభుత్వ సేవల డైరెక్టరీ కోసం క్రింది బటన్ తాకండి."
            )
            follow_ups = [
                "రైతు భరోసా కేంద్రంలో ఈ-పంట నమోదు ఎలా చేయాలో తెలుసుకోవాలనుకుంటున్నారా?",
                "గ్రామ వ్యవసాయ సహాయకుడి (VAA) సేవల గురించి సమాచారం కావాలా?",
                "అన్నదాత సుఖీభవ – పీఎం కిసాన్ పథక వివరాలు కావాలా?",
            ]
            safety_notice = "రైతు సలహా: పంట నమోదు మరియు వ్యవసాయ సేవల కోసం మీ స్థానిక RBK లేదా గ్రామ సచివాలయాన్ని మాత్రమే సంప్రదించండి."
        else:
            answer = (
                "Rythu Bharosa Kendrams (RBKs) operate at the village level across Andhra Pradesh. To locate your local center, please specify your district, mandal, or village:\n\n"
                "• **Village-Level Network:** An RBK is established in every revenue village in Andhra Pradesh, providing farmers with doorstep e-Crop registration, certified agricultural inputs, soil testing, and crop insurance assistance.\n"
                "• **Central Directory Scope:** Because RBKs operate at every individual village jurisdiction across the state, village-level GPS coordinates are not maintained in this central urban/district facility directory.\n"
                "• **How to Access Your RBK:**\n"
                "  - Visit your local Grama Sachivalayam and consult the Village Agriculture Assistant (VAA).\n"
                "  - Access the official agricultural portal: https://karshak.ap.gov.in\n"
                "  - Access the Grama / Ward Sachivalayam portal: https://gramawardsachivalayam.ap.gov.in\n"
                "  - Use the Nearby Services interface below to explore verified public service centers across AP districts."
            )
            follow_ups = [
                "Would you like details on e-Crop registration at your local RBK?",
                "Would you like information on PM Crop Insurance enrolment?",
                "Would you like details on Annadata Sukhibhava – PM KISAN benefits?",
            ]
            safety_notice = "Farmer Advisory: Always perform e-Crop registration and scheme enrollments through your authorized local RBK or Grama Sachivalayam."

        return {
            "answer": answer,
            "sources": [],
            "needs_follow_up": True,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
            "service_action": {
                "action": "open_nearby",
                "service_type": "agriculture",
                "district": target_district,
            },
        }

    # 2. Handle Grama / Ward Sachivalayam
    if target_type == "secretariat":
        if language == LanguageCode.TE:
            answer = (
                "మీ సమీప గ్రామ / వార్డు సచివాలయం వివరాలు:\n\n"
                "• **స్థానిక నెట్‌వర్క్:** ఆంధ్రప్రదేశ్‌లోని ప్రతి గ్రామ పంచాయతీ మరియు మున్సిపల్ వార్డు పరిధిలో గ్రామ/వార్డు సచివాలయాలు పనిచేస్తున్నాయి. పౌర ధ్రువీకరణ పత్రాలు (ఆదాయ, కుల ధ్రువపత్రాలు), పింఛన్లు మరియు సంక్షేమ పథకాల దరఖాస్తులు ఇక్కడే స్వీకరిస్తారు.\n"
                "• **డైరెక్టరీ పరిమితి:** గ్రామ/వార్డు స్థాయి కేంద్రాల భౌగోళిక కోఆర్డినేట్లు ఈ కేంద్రీకృత డైరెక్టరీలో నమోదు కాలేదు.\n"
                "• **అధికారిక సంప్రదింపు:**\n"
                "  - అధికారిక పోర్టల్‌లో మీ సచివాలయాన్ని కనుగొనండి: https://gramawardsachivalayam.ap.gov.in\n"
                "  - మీ వార్డు/గ్రామ పంచాయతీ కార్యాలయాన్ని నేరుగా సందర్శించండి.\n"
                "  - జిల్లా వారీగా ఇతర ప్రభుత్వ ఆరోగ్య సౌకర్యాలను వీక్షించడానికి క్రింది బటన్ ఉపయోగించండి."
            )
            follow_ups = [
                "గ్రామ సచివాలయంలో లభించే ధ్రువపత్రాల సేవల వివరాలు కావాలా?",
                "ఎన్టీఆర్ భరోసా పింఛను దరఖాస్తు ప్రక్రియ గురించి తెలుసుకోవాలా?",
            ]
            safety_notice = "పౌర సేవల సలహా: ప్రభుత్వ సంక్షేమ సేవలకు మీ అధికారిక గ్రామ సచివాలయంలోని పంచాయతీ కార్యదర్శిని మాత్రమే సంప్రదించండి."
        else:
            answer = (
                "Grama / Ward Sachivalayams operate across every village and municipal ward in Andhra Pradesh:\n\n"
                "• **Local Network:** Andhra Pradesh has established secretariats in every village and ward to deliver over 500 citizen services at the doorstep, including caste/income certificates, social security pensions, and ration cards.\n"
                "• **Central Directory Scope:** Village and ward secretariats are local administrative units; individual village-level GPS pins are not compiled in this central district directory.\n"
                "• **Official Access:**\n"
                "  - Locate your designated secretariat on the official portal: https://gramawardsachivalayam.ap.gov.in\n"
                "  - Inquire directly at your local Panchayat or municipal office.\n"
                "  - Use the Nearby Services interface below to view verified public health centers in your district."
            )
            follow_ups = [
                "Would you like details on citizen services at Grama Sachivalayam?",
                "Would you like to know how to apply for NTR Bharosa pension at the secretariat?",
            ]
            safety_notice = "Citizen Advisory: Apply for government certificates and welfare schemes exclusively through official Grama / Ward Sachivalayam staff."

        return {
            "answer": answer,
            "sources": [],
            "needs_follow_up": True,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
            "service_action": {
                "action": "open_nearby",
                "service_type": "secretariat",
                "district": target_district,
            },
        }

    # 3. Handle Hospital / Community Health Centre (CHC / PHC)
    if not target_district:
        if language == LanguageCode.TE:
            answer = (
                "ఆంధ్రప్రదేశ్‌లోని ప్రభుత్వ ఆసుపత్రులు మరియు కమ్యూనిటీ ఆరోగ్య కేంద్రాల వివరాలు తెలుసుకోవడానికి, "
                "దయచేసి మీ జిల్లా లేదా సమీప పట్టణం పేరును తెలియజేయండి (ఉదా: కాకినాడ, విశాఖపట్నం, గుంటూరు).\n\n"
                "మీరు దిగువ ఉన్న బటన్‌ను క్లిక్ చేయడం ద్వారా నేరుగా జీపీఎస్ (GPS) లేదా జిల్లా ఎంపికతో సేవల డైరెక్టరీని తెరవవచ్చు.\n\n"
                "అత్యవసర వైద్య సహాయం కోసం వెంటనే 108 (అంబులెన్స్) లేదా 104 (వైద్య సలహా) కు కాల్ చేయండి."
            )
            follow_ups = [
                "కాకినాడలోని ప్రభుత్వ సాధారణ ఆసుపత్రి (GGH) ఎక్కడ ఉంది?",
                "విశాఖపట్నంలోని కింగ్ జార్జ్ ఆసుపత్రి (KGH) ఎక్కడ ఉంది?",
            ]
            safety_notice = "వైద్య హెచ్చరిక: అత్యవసర సమయాల్లో ఆలస్యం చేయకుండా 108 అంబులెన్స్ సేవలను సంప్రదించండి."
        else:
            answer = (
                "To locate verified government hospitals and community health centres near you, "
                "please specify your district or city in Andhra Pradesh (e.g., Kakinada, Visakhapatnam, Guntur, Kurnool).\n\n"
                "You can also click the button below to open the Nearby Services directory and use device GPS or select your district directly.\n\n"
                "For immediate emergency medical assistance, please dial 108 (Ambulance) or 104 (Health Advice Helpline)."
            )
            follow_ups = [
                "Where is the Government General Hospital in Kakinada located?",
                "Where is King George Hospital (KGH) in Visakhapatnam located?",
            ]
            safety_notice = "Medical Advisory: For life-threatening emergencies, immediately dial 108 for an ambulance."

        return {
            "answer": answer,
            "sources": [],
            "needs_follow_up": True,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
            "service_action": {
                "action": "open_nearby",
                "service_type": target_type,
                "district": None,
            },
        }

    # Target district is known: search verified health facilities
    try:
        facilities = find_nearby_services(service_type=target_type, district=target_district)
        if not facilities and target_type == "community_health_centre":
            facilities = find_nearby_services(service_type="hospital", district=target_district)
    except Exception:
        facilities = []

    sources = []
    if facilities:
        if language == LanguageCode.TE:
            lines = [f"[{target_district} పరిధిలోని ధృవీకరించబడిన ప్రభుత్వ ఆరోగ్య సేవలు]:\n"]
            for f in facilities:
                lines.append(f"• **{f['name']}**")
                lines.append(f"  చిరునామా: {f['address']}")
                if f.get("phone"):
                    lines.append(f"  ఫోన్: {f['phone']}")
                if f.get("source_url"):
                    lines.append(f"  అధికారిక వెబ్‌సైట్: {f['source_url']}")
                lines.append("")
            lines.append("అత్యవసర వైద్య సహాయం కోసం 108 కు, ఆరోగ్య సలహాల కోసం 104 కు కాల్ చేయండి.")
            answer = "\n".join(lines).strip()
            follow_ups = [
                "డా. ఎన్టీఆర్ వైద్య సేవ నెట్‌వర్క్ ఆసుపత్రుల వివరాలు కావాలా?",
                "104 మరియు 108 సేవల వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
            ]
            safety_notice = "గమనిక: చిరునామాలు మరియు ఫోన్ నంబర్లు ప్రభుత్వ డైరెక్టరీల ఆధారంగా అందించబడ్డాయి."
        else:
            lines = [f"[Verified public health facilities for {target_district}, Andhra Pradesh]:\n"]
            for f in facilities:
                lines.append(f"• **{f['name']}**")
                lines.append(f"  Address: {f['address']}")
                if f.get("phone"):
                    lines.append(f"  Phone: {f['phone']}")
                if f.get("source_url"):
                    lines.append(f"  Directory: {f['source_url']}")
                lines.append("")
            lines.append("For emergency medical care, dial 108 (Ambulance) or 104 (Health Helpline).")
            answer = "\n".join(lines).strip()
            follow_ups = [
                "Would you like details on Dr. NTR Vaidya Seva cashless treatment coverage?",
                "Would you like information on 104 mobile medical unit schedules?",
            ]
            safety_notice = "Public Health Notice: Facility directory details are sourced from official DME and APVVP government directories."

        for f in facilities:
            if f.get("source_url"):
                sources.append(
                    Source(
                        title=f["name"],
                        url=f["source_url"],
                        publisher="Directorate of Medical Education / APVVP",
                        verified_at="2026-11-21",
                    )
                )

        return {
            "answer": answer,
            "sources": sources,
            "needs_follow_up": False,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
            "service_action": {
                "action": "open_nearby",
                "service_type": target_type,
                "district": target_district,
            },
        }
    else:
        if language == LanguageCode.TE:
            answer = (
                f"{target_district} జిల్లాకు సంబంధించి ధృవీకరించబడిన ఆసుపత్రి వివరాలు ప్రస్తుతం మా డైరెక్టరీలో అందుబాటులో లేవు.\n"
                "దయచేసి సమీపంలోని జిల్లా ఆసుపత్రి లేదా కమ్యూనిటీ ఆరోగ్య కేంద్రాన్ని సంప్రదించండి. "
                "అత్యవసర అంబులెన్స్ సహాయం కోసం 108 కు కాల్ చేయండి."
            )
            follow_ups = ["104 ఉచిత వైద్య సలహా సేవల గురించి తెలుసుకోవాలనుకుంటున్నారా?"]
            safety_notice = "వైద్య హెచ్చరిక: అత్యవసర పరిస్థితుల్లో వెంటనే 108 కు కాల్ చేయండి."
        else:
            answer = (
                f"Verified hospital listings for {target_district} district are currently not substantiated in our central directory.\n"
                "Please visit your nearest Community Health Centre (CHC) or Area Hospital. "
                "For emergency medical transportation, please dial 108."
            )
            follow_ups = ["Would you like information on 104 mobile medical health services?"]
            safety_notice = "Medical Notice: In case of acute medical emergencies, immediately dial 108."

        return {
            "answer": answer,
            "sources": [],
            "needs_follow_up": True,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
            "service_action": {
                "action": "open_nearby",
                "service_type": target_type,
                "district": target_district,
            },
        }


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Main Chat Endpoint",
    description="Processes citizen messages, routes to domain specialist, retrieves verified context, and returns grounded answers.",
)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    # 1. Validate message content
    clean_message = request.message.strip()
    if not clean_message:
        raise BadRequestException(
            message="Message cannot be blank or empty whitespace.",
            code="EMPTY_MESSAGE",
        )

    # 2. Generate conversation ID if omitted
    conv_id = request.conversation_id
    if not conv_id or not conv_id.strip():
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"

    # 3. Deterministic clinical emergency safety guard
    # Operates BEFORE RAG retrieval or generic fallbacks
    emergency_result = check_clinical_emergency(
        query=clean_message,
        language=request.language,
    )
    if emergency_result:
        response = ChatResponse(
            conversation_id=conv_id,
            answer=emergency_result["answer"],
            assistant=request.assistant,
            language=request.language,
            sources=[],
            needs_follow_up=False,
            follow_up_questions=emergency_result["follow_up_questions"],
            safety_notice=emergency_result["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 4. Ambiguous NTR reference clarification
    if is_ambiguous_ntr_query(clean_message):
        ntr_clarification = _handle_ambiguous_ntr(request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=ntr_clarification["answer"],
            assistant=request.assistant,
            language=request.language,
            sources=[],
            needs_follow_up=True,
            follow_up_questions=ntr_clarification["follow_up_questions"],
            safety_notice=ntr_clarification["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 5. Contextual follow-up resolution for multi-turn conversations
    routed_assistant = request.assistant
    if _is_contextual_query(clean_message) and not detect_named_schemes(clean_message):
        memory_ctx = _CONVERSATION_MEMORY.get(conv_id)
        if memory_ctx and memory_ctx.get("last_scheme_name"):
            last_scheme = memory_ctx["last_scheme_name"]
            if request.language == LanguageCode.TE:
                clean_message = re.sub(r"దీనికి|ఈ\s*పథకానికి|ఆ\s*పథకానికి", f"{last_scheme} పథకానికి", clean_message)
                if last_scheme not in clean_message:
                    clean_message = f"{last_scheme}: {clean_message}"
            else:
                clean_message = re.sub(r"\b(?:this|the|that)\s+scheme\b", f"{last_scheme} scheme", clean_message, flags=re.IGNORECASE)
                clean_message = re.sub(r"\b(?:for\s+this|for\s+it)\b", f"for {last_scheme}", clean_message, flags=re.IGNORECASE)
                if last_scheme.lower() not in clean_message.lower():
                    clean_message = f"{clean_message} for {last_scheme}"
            if memory_ctx.get("last_assistant"):
                routed_assistant = memory_ctx["last_assistant"]

    # 6. Unsupported named scheme query (e.g. PMXYZ)
    unsupported_name = _detect_unsupported_scheme(clean_message)
    if unsupported_name:
        unsupported_res = _handle_unsupported_scheme(unsupported_name, request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=unsupported_res["answer"],
            assistant=routed_assistant,
            language=request.language,
            sources=[],
            needs_follow_up=True,
            follow_up_questions=unsupported_res["follow_up_questions"],
            safety_notice=unsupported_res["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 7. Ambiguous government scheme clarification (generic unnamed query under general schemes)
    if routed_assistant == AssistantIdentifier.SCHEMES and (
        is_ambiguous_scheme_query(clean_message, request.language)
        or (_is_contextual_query(clean_message) and not detect_named_schemes(clean_message))
    ):
        clarification_result = get_scheme_clarification_response(request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=clarification_result["answer"],
            assistant=routed_assistant,
            language=request.language,
            sources=[],
            needs_follow_up=True,
            follow_up_questions=clarification_result["follow_up_questions"],
            safety_notice=clarification_result["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 8. Cross-domain specialist routing based on detected scheme
    named_doc_ids = detect_named_schemes(clean_message)
    if named_doc_ids:
        # Collect domains of all matched schemes
        domains = set()
        for did in named_doc_ids:
            info = SCHEME_REGISTRY.get(did)
            if info and info.get("domain"):
                domains.add(info["domain"])

        domain_map = {
            "agriculture": AssistantIdentifier.AGRICULTURE,
            "healthcare": AssistantIdentifier.HEALTHCARE,
            "education": AssistantIdentifier.EDUCATION,
            "schemes": AssistantIdentifier.SCHEMES,
        }
        # If multiple schemes cross multiple domains, route to general schemes specialist
        if len(domains) > 1:
            routed_assistant = AssistantIdentifier.SCHEMES
        else:
            single_dom = list(domains)[0] if domains else None
            if single_dom and single_dom in domain_map:
                routed_assistant = domain_map[single_dom]

    # 9. Call internal retrieval interface owned by Member 2
    top_k_val = 6 if len(named_doc_ids) > 1 else 5
    retrieval_outcome = fetch_retrieval_context(
        query=clean_message,
        assistant=routed_assistant.value,
        language=request.language.value,
        state=request.state,
        district=request.district,
        top_k=top_k_val,
    )

    # 10. Technical failure safety gate: if retrieval service fails, return technical issue
    if retrieval_outcome is not None and not retrieval_outcome.success:
        result = agent_router.route_and_process(
            query=clean_message,
            assistant=routed_assistant,
            language=request.language,
            state=request.state,
            district=request.district,
            retrieval_outcome=retrieval_outcome,
        )
        response = ChatResponse(
            conversation_id=conv_id,
            answer=result["answer"],
            assistant=routed_assistant,
            language=request.language,
            sources=result["sources"],
            needs_follow_up=result["needs_follow_up"],
            follow_up_questions=result["follow_up_questions"],
            safety_notice=result.get("safety_notice"),
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 11. Nearby service intent routing (Hospital, CHC, RBK, or Grama Sachivalayam)
    nearby_res = _handle_nearby_service_query(
        clean_message, request.language, request.state, request.district
    )
    if nearby_res:
        response = ChatResponse(
            conversation_id=conv_id,
            answer=nearby_res["answer"],
            assistant=request.assistant,
            language=request.language,
            sources=nearby_res["sources"],
            needs_follow_up=nearby_res["needs_follow_up"],
            follow_up_questions=nearby_res["follow_up_questions"],
            safety_notice=nearby_res["safety_notice"],
            service_action=nearby_res.get("service_action"),
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 12. Technical skill training / APSSDC inquiries
    if _detect_apssdc_query(clean_message):
        apssdc_res = _handle_apssdc_query(request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=apssdc_res["answer"],
            assistant=AssistantIdentifier.EDUCATION,
            language=request.language,
            sources=[],
            needs_follow_up=True,
            follow_up_questions=apssdc_res["follow_up_questions"],
            safety_notice=apssdc_res["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 13. Generic scholarship inquiries & typographical variants (e.g., availble schoalrship)
    if _detect_generic_scholarship_query(clean_message) and not detect_named_schemes(clean_message):
        scholarship_res = _handle_generic_scholarship_query(request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=scholarship_res["answer"],
            assistant=AssistantIdentifier.EDUCATION,
            language=request.language,
            sources=scholarship_res.get("sources", []),
            needs_follow_up=True,
            follow_up_questions=scholarship_res["follow_up_questions"],
            safety_notice=scholarship_res["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 14. Route to specialist agent
    result = agent_router.route_and_process(
        query=clean_message,
        assistant=routed_assistant,
        language=request.language,
        state=request.state,
        district=request.district,
        retrieval_outcome=retrieval_outcome,
    )

    response = ChatResponse(
        conversation_id=conv_id,
        answer=result["answer"],
        assistant=routed_assistant,
        language=request.language,
        sources=result["sources"],
        needs_follow_up=result["needs_follow_up"],
        follow_up_questions=result["follow_up_questions"],
        safety_notice=result["safety_notice"],
    )

    # 13. Record conversation context for multi-turn contextual queries
    last_did = named_doc_ids[0] if named_doc_ids else None
    if not last_did and response.sources:
        for s in response.sources:
            s_dids = detect_named_schemes(s.title)
            if s_dids:
                last_did = s_dids[0]
                break

    if last_did and last_did in SCHEME_REGISTRY:
        s_info = SCHEME_REGISTRY[last_did]
        s_name = s_info.get("current_name") or s_info.get("title")
        _CONVERSATION_MEMORY.set(
            conv_id=conv_id,
            scheme_id=last_did,
            scheme_name=s_name,
            assistant=routed_assistant,
        )

    # 14. Persist interaction in database (safe, non-blocking on failure)
    _save_chat_interaction_safely(conv_id, request, response)

    return response
