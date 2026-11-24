import logging
import uuid
import re
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


def _handle_nearby_service_query(
    query: str,
    language: LanguageCode,
    state: Optional[str],
    district: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Detects nearby service discovery intent (Hospital/CHC or RBK/Sachivalayam).
    For Hospital/CHC: queries substantiated AP public health directories.
    For RBK/Sachivalayam: honestly explains directory scope and provides authoritative portals.
    """
    q_norm = normalize_text(query)
    q_lower = query.lower()

    # Location intent indicators
    has_loc = any(w in q_lower or w in q_norm for w in [
        "near", "nearest", "nearby", "where", "location", "address", "find",
        "సమీప", "దగ్గర", "ఎక్కడ", "చిరునామా", "కేంద్రం ఎక్కడ", "ఆసుపత్రి ఎక్కడ",
    ])

    # 1. RBK / Sachivalayam indicators
    has_office = any(w in q_lower or w in q_norm for w in [
        "rbk", "rythu bharosa kendram", "sachivalayam", "village secretariat", "ward secretariat",
        "ఆర్బీకే", "రైతు భరోసా కేంద్రం", "సచివాలయం", "గ్రామ సచివాలయం", "వార్డు సచివాలయం",
    ])
    is_local_office_intent = has_loc and has_office

    # 2. Hospital / Healthcare indicators
    has_health_target = any(w in q_lower or w in q_norm for w in [
        "hospital", "hospitals", "clinic", "health centre", "health center", "chc", "phc",
        "ఆసుపత్రి", "ఆసుపత్రులు", "హాస్పిటల్", "ఆరోగ్య కేంద్రం",
    ])
    is_scheme_q = any(w in q_lower or w in q_norm for w in [
        "vaidya seva", "aarogyasri", "pmjay", "ayushman bharat", "వైద్య సేవ", "ఆరోగ్యశ్రీ"
    ])
    is_hospital_intent = has_loc and has_health_target and not is_scheme_q

    if not is_hospital_intent and not is_local_office_intent:
        return None

    # Handle RBK / Sachivalayam nearby intent honestly
    if is_local_office_intent:
        if language == LanguageCode.TE:
            answer = (
                "AI గ్రామ సహాయక్ ప్రస్తుతం ఆంధ్రప్రదేశ్‌లోని ప్రభుత్వ ఆసుపత్రులు మరియు అత్యవసర వైద్య కేంద్రాల ధృవీకరించబడిన డైరెక్టరీని నిర్వహిస్తోంది.\n\n"
                "మీ సమీపంలోని రైతు భరోసా కేంద్రం (RBK) లేదా గ్రామ/వార్డు సచివాలయం సేవల కోసం:\n"
                "• **గ్రామ/వార్డు సచివాలయం**: మీ స్థానిక గ్రామ లేదా వార్డు సచివాలయ కేంద్రాన్ని నేరుగా సందర్శించండి లేదా అధికారిక పోర్టల్ చూడండి: https://gramawardsachivalayam.ap.gov.in\n"
                "• **రైతు భరోసా కేంద్రం (RBK)**: మీ గ్రామ సచివాలయ పరిధిలోని గ్రామ వ్యవసాయ సహాయకుడిని (VAA) సంప్రదించండి లేదా పోర్టల్ చూడండి: https://karshak.ap.gov.in\n\n"
                "ఈ కేంద్రాల ద్వారా సంక్షేమ పథకాల నమోదు, ఈ-పంట (e-Crop) నమోదు మరియు వివిధ ప్రభుత్వ ధ్రువపత్రాల సేవలు పొందవచ్చు."
            )
            follow_ups = [
                "గ్రామ సచివాలయంలో లభించే ప్రజా సేవల వివరాలు తెలుసుకోవాలనుకుంటున్నారా?",
                "రైతు భరోసా కేంద్రంలో ఈ-పంట నమోదు ప్రక్రియ గురించి సమాచారం కావాలా?",
            ]
            safety_notice = (
                "పౌర సేవల సలహా: ప్రభుత్వ సంక్షేమ సేవల దరఖాస్తులను మీ అధికారిక గ్రామ సచివాలయంలో మాత్రమే సమర్పించండి. "
                "అనధికార వ్యక్తులకు లేదా మధ్యవర్తులకు ఎటువంటి రుసుములు చెల్లించవద్దు."
            )
        else:
            answer = (
                "AI Grama Sahayak currently maintains verified location directories for public teaching hospitals and community health centres across Andhra Pradesh.\n\n"
                "To locate and access your nearest Rythu Bharosa Kendram (RBK) or Grama / Ward Sachivalayam:\n"
                "• **Grama / Ward Sachivalayam**: Visit your local village or ward secretariat, or check the official citizen portal: https://gramawardsachivalayam.ap.gov.in\n"
                "• **Rythu Bharosa Kendram (RBK)**: Contact your Village Agriculture Assistant (VAA) at your local village secretariat or check: https://karshak.ap.gov.in\n\n"
                "These local centers provide official assistance for welfare scheme enrollment, e-Panta / e-Crop registration, and citizen certificates."
            )
            follow_ups = [
                "Would you like details on citizen services available at Grama Sachivalayam?",
                "Would you like information on e-Panta crop registration at RBKs?",
            ]
            safety_notice = (
                "Citizen Advisory: Always access government services through official village secretariats or designated government portals. "
                "Never pay unauthorized intermediaries."
            )

        return {
            "answer": answer,
            "sources": [],
            "needs_follow_up": True,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
        }

    # Handle Hospital / Healthcare nearby intent
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

    if not target_district:
        if language == LanguageCode.TE:
            answer = (
                "ఆంధ్రప్రదేశ్‌లోని ప్రభుత్వ ఆసుపత్రులు మరియు ఆరోగ్య కేంద్రాల వివరాలు తెలుసుకోవడానికి, "
                "దయచేసి మీ జిల్లా లేదా సమీప పట్టణం పేరును తెలియజేయండి (ఉదా: కాకినాడ, విశాఖపట్నం, గుంటూరు).\n\n"
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
        }

    # Target district is known: search verified health facilities
    try:
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

    # 5. Ambiguous government scheme clarification (unnamed scheme under general schemes)
    if request.assistant == AssistantIdentifier.SCHEMES and is_ambiguous_scheme_query(
        clean_message, request.language
    ):
        clarification_result = get_scheme_clarification_response(request.language)
        response = ChatResponse(
            conversation_id=conv_id,
            answer=clarification_result["answer"],
            assistant=request.assistant,
            language=request.language,
            sources=[],
            needs_follow_up=True,
            follow_up_questions=clarification_result["follow_up_questions"],
            safety_notice=clarification_result["safety_notice"],
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 6. Cross-domain specialist routing based on detected scheme
    routed_assistant = request.assistant
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

    # 7. Call internal retrieval interface owned by Member 2
    top_k_val = 6 if len(named_doc_ids) > 1 else 5
    retrieval_outcome = fetch_retrieval_context(
        query=clean_message,
        assistant=routed_assistant.value,
        language=request.language.value,
        state=request.state,
        district=request.district,
        top_k=top_k_val,
    )

    # 8. Technical failure safety gate: if retrieval service fails, return technical issue
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

    # 9. Nearby service intent routing (Hospital or RBK / Sachivalayam)
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
        )
        _save_chat_interaction_safely(conv_id, request, response)
        return response

    # 10. Route to specialist agent
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

    # 10. Persist interaction in database (safe, non-blocking on failure)
    _save_chat_interaction_safely(conv_id, request, response)

    return response
