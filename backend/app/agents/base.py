import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.schemas.common import AssistantIdentifier, LanguageCode, Source
from app.core.emergency_detector import check_clinical_emergency
from app.services.retrieval.scheme_registry import detect_scheme_details, SCHEME_REGISTRY
from app.services.answer_synthesizer import (
    detect_query_intent,
    synthesize_scheme_answer,
    extract_bilingual_evidence_from_chunks,
    sanitize_english_text,
    sanitize_telugu_text,
)


SCHEME_TAILORED_FOLLOW_UPS: Dict[str, Dict[str, List[str]]] = {
    "edu_thalliki_vandanam_scheme": {
        "en": [
            "What are the required documents and Rice Card criteria for Thalliki Vandanam?",
            "How is student school attendance (75% benchmark) verified for eligibility?",
            "Where can mothers verify their Aadhaar NPCI bank account seeding status?",
        ],
        "te": [
            "తల్లికి వందనం ధృవీకరణకు అవసరమైన పత్రాలు మరియు రైస్ కార్డు నిబంధనలు ఏమిటి?",
            "75% పాఠశాల హాజరు నిబంధన వివరాలు ఎలా తనిఖీ చేయాలి?",
            "తల్లి బ్యాంక్ ఖాతా ఆధార్-ఎన్‌పీసీఐ సీడింగ్ స్థితిని ఎక్కడ తెలుసుకోవచ్చు?",
        ],
    },
    "agri_annadata_sukhibhava_pmkisan": {
        "en": [
            "What are the landholding rules and tenant farmer criteria for Annadata Sukhibhava?",
            "How do farmers complete PM-KISAN e-KYC and land record linking?",
            "Where is the nearest Rythu Bharosa Kendram (RBK) for application assistance?",
        ],
        "te": [
            "అన్నదాత సుఖీభవ పథకం అర్హతలు మరియు కౌలు రైతుల నిబంధనలు ఏమిటి?",
            "పీఎం కిసాన్ ఈ-కేవైసీ (e-KYC) మరియు భూ రికార్డుల అనుసంధానం ఎలా పూర్తి చేయాలి?",
            "దరఖాస్తు సహాయం కోసం స్థానిక రైతు భరోసా కేంద్రాన్ని (RBK) ఎలా సంప్రదించాలి?",
        ],
    },
    "schemes_ntr_bharosa_pension": {
        "en": [
            "What are the age requirements and category rules for NTR Bharosa pensions?",
            "Which documents are required for new pension registration at Grama Sachivalayam?",
            "How can beneficiaries track their pension verification and disbursement status?",
        ],
        "te": [
            "ఎన్టీఆర్ భరోసా పింఛన్ వయోపరిమితి మరియు వర్గాల వివరాలు ఏమిటి?",
            "సచివాలయంలో కొత్త పింఛన్ నమోదుకు ఏయే పత్రాలు సమర్పించాలి?",
            "పింఛన్ ధృవీకరణ మరియు పంపిణీ స్థితిని ఎలా తనిఖీ చేయాలి?",
        ],
    },
    "schemes_mgnregs_andhra_pradesh": {
        "en": [
            "How can rural households apply for an MGNREGS Job Card?",
            "What are the guidelines for 100 days of guaranteed wage employment?",
            "Where can workers submit grievance complaints regarding wage payments?",
        ],
        "te": [
            "గ్రామీణ కుటుంబాలు ఉపాధి హామీ జాబ్ కార్డు కోసం ఎలా దరఖాస్తు చేయాలి?",
            "100 రోజుల హామీ వేతన ఉపాధి మార్గదర్శకాలు ఏమిటి?",
            "వేతన చెల్లింపుల సమస్యలపై ఎక్కడ ఫిర్యాదు చేయాలి?",
        ],
    },
    "health_dr_ntr_vaidya_seva_aarogyasri": {
        "en": [
            "Which medical treatments and surgical procedures are covered under Dr. NTR Vaidya Seva?",
            "What is the procedure to receive cashless treatment at empaneled network hospitals?",
            "How can patients contact Aarogyamithras at government hospitals for assistance?",
        ],
        "te": [
            "డాక్టర్ ఎన్టీఆర్ వైద్య సేవ కింద ఏయే శస్త్రచికిత్సలు మరియు చికిత్సలు అందుబాటులో ఉన్నాయి?",
            "నెట్‌వర్క్ ఆసుపత్రులలో ఉచిత నగదు రహిత చికిత్స పొందే విధానం ఏమిటి?",
            "సహాయం కోసం ఆసుపత్రుల్లోని ఆరోగ్యమిత్రలను ఎలా సంప్రదించాలి?",
        ],
    },
    "schemes_pedalandariki_illu_housing": {
        "en": [
            "What are the eligibility criteria and income limits for Pedalandariki Illu house site pattas?",
            "What is the construction subsidy and stage-wise payment process through APSHCL?",
            "Where can applicants check their housing sanction and plot allotment status?",
        ],
        "te": [
            "పేదలందరికీ ఇళ్లు ఇళ్ల స్థలాల పట్టాల అర్హతలు మరియు ఆదాయ పరిమితులు ఏమిటి?",
            "గృహ నిర్మాణ రాయితీ మరియు దశలవారీ చెల్లింపుల విధానం ఏమిటి?",
            "ఇంటి మంజూరు మరియు స్థలం కేటాయింపు స్థితిని ఎక్కడ తనిఖీ చేయవచ్చు?",
        ],
    },
}


class BaseSpecialistAgent(ABC):
    """
    Modular base specialist agent.
    Each specialist encapsulates domain-specific reasoning, verified source validation,
    multilingual phrasing (English & Telugu), and required public-service safety notices.
    """

    def __init__(
        self,
        assistant_id: AssistantIdentifier,
        name: str,
        domain: str,
        description: str,
    ):
        self.assistant_id = assistant_id
        self.name = name
        self.domain = domain
        self.description = description

    @abstractmethod
    def get_safety_notice(self, language: LanguageCode) -> Optional[str]:
        """Return mandatory public-service safety or advisory notice for this domain."""
        pass

    @abstractmethod
    def get_default_follow_up_questions(
        self,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[str]:
        """Return domain-relevant suggested follow-up questions."""
        pass

    def extract_sources(self, retrieved_chunks: List[Dict[str, Any]]) -> List[Source]:
        """
        Safely extracts and deduplicates verified government sources from retrieval chunks.
        Never invents or fabricates sources.
        """
        sources: List[Source] = []
        seen_urls = set()

        for chunk in retrieved_chunks:
            source_data = chunk.get("source")
            if not source_data or not isinstance(source_data, dict):
                continue

            url = source_data.get("url")
            if not url or url in seen_urls:
                continue

            title = source_data.get("title") or "Official verified source"
            publisher = source_data.get("publisher") or "Government Authority"
            verified_at = source_data.get("verified_at") or "2026-11-21"

            try:
                source = Source(
                    title=str(title),
                    url=str(url),
                    publisher=str(publisher),
                    verified_at=str(verified_at),
                )
                sources.append(source)
                seen_urls.add(url)
            except Exception:
                continue

        return sources

    def process_query(
        self,
        query: str,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        retrieval_outcome: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates answer generation strictly grounded in verified retrieval evidence.
        Explicitly distinguishes between:
        - Retrieval service failure (reports service error honestly)
        - Genuine empty retrieval (truthfully reports verified info is unavailable)
        - Verified evidence present (synthesizes grounded response and cites sources)
        """
        # Retrieve context-appropriate safety notice
        try:
            safety_notice = self.get_safety_notice(language, query=query)
        except TypeError:
            safety_notice = self.get_safety_notice(language)

        # Retrieve follow up questions (tailored or default)
        try:
            follow_ups = self.get_default_follow_up_questions(
                language, state=state, district=district, query=query
            )
        except TypeError:
            follow_ups = self.get_default_follow_up_questions(
                language, state=state, district=district
            )

        # 1. Check for retrieval service failure
        if retrieval_outcome is not None and not getattr(retrieval_outcome, "success", True):
            if language == LanguageCode.TE:
                answer = (
                    "సమాచార పునరుద్ధరణ సేవలో సాంకేతిక సమస్య ఎదురైంది. దయచేసి కాసేపటి తర్వాత మళ్లీ ప్రయత్నించండి "
                    "లేదా మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని సంప్రదించండి."
                )
            else:
                answer = (
                    "The verified retrieval service encountered a temporary technical issue. "
                    "Please try again shortly or contact your local Grama / Ward Sachivalayam for verified assistance."
                )
            return {
                "answer": answer,
                "sources": [],
                "needs_follow_up": True,
                "follow_up_questions": follow_ups,
                "safety_notice": safety_notice,
            }

        # 2. Extract chunks from outcome or direct parameter
        chunks = (
            getattr(retrieval_outcome, "chunks", None)
            if retrieval_outcome is not None
            else retrieved_chunks
        ) or []

        # 3. Strict ground rule: Genuine empty evidence
        if not chunks:
            # Deterministic clinical emergency guard: never direct an emergency to a Grama Sachivalayam
            emergency_result = check_clinical_emergency(query, language)
            if emergency_result:
                return emergency_result

            if language == LanguageCode.TE:
                answer = (
                    "ఈ ప్రశ్నకు సంబంధించి ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం అందుబాటులో లేదు.\n"
                    "వివరాల కోసం దయచేసి మీ స్థానిక గ్రామ/వార్డు సచివాలయాన్ని లేదా సంబంధిత ప్రభుత్వ కార్యాలయాన్ని సంప్రదించండి."
                )
            else:
                answer = (
                    "Verified official information is currently unavailable for this query.\n"
                    "Please consult official government portals or visit your local Grama / Ward Sachivalayam for verified assistance."
                )

            return {
                "answer": answer,
                "sources": [],
                "needs_follow_up": True,
                "follow_up_questions": follow_ups,
                "safety_notice": safety_notice,
            }

        # Check for scheme-tailored follow-ups
        first_chunk = chunks[0] if chunks else None
        doc_id = ""
        if first_chunk:
            meta = first_chunk.get("metadata", {}) if isinstance(first_chunk, dict) else getattr(first_chunk, "metadata", {})
            doc_id = meta.get("doc_id", "")
        if doc_id and doc_id in SCHEME_TAILORED_FOLLOW_UPS:
            lang_key = "te" if language == LanguageCode.TE else "en"
            scheme_follow_ups = SCHEME_TAILORED_FOLLOW_UPS[doc_id].get(lang_key)
            if scheme_follow_ups:
                follow_ups = scheme_follow_ups

        # 4. Evidence is present: synthesize response strictly grounded in chunks
        sources = self.extract_sources(chunks)
        answer = self.synthesize_grounded_answer(query, chunks, language, state, district)

        return {
            "answer": answer,
            "sources": sources,
            "needs_follow_up": False,
            "follow_up_questions": follow_ups,
            "safety_notice": safety_notice,
        }

    def synthesize_grounded_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        language: LanguageCode,
        state: Optional[str],
        district: Optional[str],
    ) -> str:
        """
        Synthesizes a concise, citizen-friendly response strictly grounded in verified chunks.
        Answers the exact question first, isolates languages cleanly (zero Telugu script in English),
        explains historical predecessor context accurately, and targets approximately 100–180 words.
        """
        if not chunks:
            if language == LanguageCode.TE:
                return "ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం అందుబాటులో లేదు."
            return "Verified official information is currently unavailable."

        is_te = (language == LanguageCode.TE)

        # Detect historical scheme context if user used predecessor terms
        scheme_info = detect_scheme_details(query)
        is_historical = scheme_info.get("is_historical", False)
        hist_note = ""
        if is_historical:
            hist_note = (
                scheme_info.get("historical_note_te", "")
                if is_te
                else scheme_info.get("historical_note_en", "")
            )
            # Qualify specifically when user queries past/historical operational rules
            is_hist_rules_query = any(w in query.lower() for w in ["historical", "past", "earlier", "erstwhile", "గతంలో", "పూర్వపు", "పాత"])
            if is_hist_rules_query:
                if is_te:
                    hist_limit_note = (
                        "గమనిక: పూర్వపు పథక చట్టబద్ధమైన కార్యాచరణ రికార్డులు చారిత్రకమైనవి; "
                        "ప్రస్తుత సక్రియ అధికారిక డేటాబేస్ సంస్కరించబడిన మార్గదర్శకాలను మాత్రమే అందిస్తుంది."
                    )
                else:
                    hist_limit_note = (
                        "Note on historical rules: Operational records for erstwhile schemes are historical; "
                        "the active verified knowledge base maintains current policy under the successor framework."
                    )
                hist_note = f"{hist_limit_note}\n\n{hist_note}" if hist_note else hist_limit_note

        # Multi-document check: for comparisons or multi-scheme queries, pick top chunk of each distinct document
        distinct_docs: Dict[str, Any] = {}
        for c in chunks:
            c_doc_id = (c.get("metadata", {}) if isinstance(c, dict) else getattr(c, "metadata", {})).get("doc_id", "")
            if c_doc_id and c_doc_id not in distinct_docs:
                distinct_docs[c_doc_id] = c

        intent = detect_query_intent(query, language)

        first_chunk = chunks[0] if chunks else None
        first_doc_id = ""
        if first_chunk:
            meta = first_chunk.get("metadata", {}) if isinstance(first_chunk, dict) else getattr(first_chunk, "metadata", {})
            first_doc_id = meta.get("doc_id", "")

        # When a single verified scheme document is primarily targeted, synthesize via verified scheme profiles
        if len(distinct_docs) < 2 and first_doc_id:
            scheme_answer = synthesize_scheme_answer(
                query=query,
                doc_id=first_doc_id,
                intent=intent,
                language=language,
                state=state,
                district=district,
                chunks=chunks,
            )
            if scheme_answer:
                # Prepend historical note if user mentioned historical name and it is not already in the answer
                if hist_note and hist_note not in scheme_answer:
                    if "\n\n" in scheme_answer and scheme_answer.startswith("["):
                        prefix, rest = scheme_answer.split("\n\n", 1)
                        scheme_answer = f"{prefix}\n\n{hist_note}\n\n{rest}"
                    else:
                        scheme_answer = f"{hist_note}\n\n{scheme_answer}"

                if not is_te:
                    scheme_answer = sanitize_english_text(scheme_answer)
                else:
                    scheme_answer = sanitize_telugu_text(scheme_answer)
                return scheme_answer

        if len(distinct_docs) >= 2:
            selected_chunks = list(distinct_docs.values())[:3]
        else:
            selected_chunks = chunks[:2] if len(chunks) >= 2 else chunks

        formatted_sections = []
        total_len = 0
        for chunk in selected_chunks:
            formatted = self._format_single_chunk(chunk, is_te)
            if formatted and formatted not in formatted_sections:
                if total_len > 0 and (total_len + len(formatted) > 1200):
                    break
                formatted_sections.append(formatted)
                total_len += len(formatted)

        if not formatted_sections:
            if is_te:
                return "ధృవీకరించబడిన అధికారిక సమాచారం ప్రస్తుతం అందుబాటులో లేదు."
            return "Verified official information is currently unavailable."

        combined_answer = "\n\n".join(formatted_sections).strip()

        # If historical note exists and isn't already in the answer, prepend it
        if hist_note and hist_note not in combined_answer:
            combined_answer = f"{hist_note}\n\n{combined_answer}"

        # Extract scheme title if available from top chunk
        first_chunk = chunks[0] if chunks else None
        scheme_title = ""
        if len(distinct_docs) >= 2:
            scheme_title = "ఆంధ్రప్రదేశ్ సంక్షేమ పథకాల వివరాలు" if is_te else "Government Schemes Comparison"
        elif first_chunk:
            raw_title = (first_chunk.get("title") if isinstance(first_chunk, dict) else getattr(first_chunk, "title", "")) or ""
            if raw_title:
                clean_t = re.split(r"\s+(?:Scheme|Program|Citizen|Guidelines)\b", raw_title, flags=re.IGNORECASE)[0].strip()
                scheme_title = clean_t or raw_title

        # Incorporate historical name in title if relevant
        if len(distinct_docs) < 2 and is_historical and scheme_info.get("historical_name"):
            h_name = scheme_info.get("historical_name", "")
            c_name = scheme_info.get("current_name", scheme_title)
            if is_te:
                scheme_title = f"{c_name} (గతంలో {h_name})"
            else:
                scheme_title = f"{c_name} (formerly {h_name})"

        location_prefix = ""
        if district and state:
            loc_str = f"{district}, {state}"
            if is_te:
                prefix_core = f"{scheme_title} - {loc_str}" if scheme_title else loc_str
                location_prefix = f"[{prefix_core} పరిధిలోని అధికారిక సమాచారం]:\n\n"
            else:
                prefix_core = f" on {scheme_title}" if scheme_title else ""
                location_prefix = f"[Verified official information{prefix_core} for {loc_str}]:\n\n"
        elif state:
            if is_te:
                prefix_core = f"{scheme_title} - {state}" if scheme_title else state
                location_prefix = f"[{prefix_core} పరిధిలోని అధికారిక సమాచారం]:\n\n"
            else:
                prefix_core = f" on {scheme_title}" if scheme_title else ""
                location_prefix = f"[Verified official information{prefix_core} for {state}]:\n\n"
        elif scheme_title:
            if is_te:
                location_prefix = f"[{scheme_title} - అధికారిక సమాచారం]:\n\n"
            else:
                location_prefix = f"[Verified official information on {scheme_title}]:\n\n"

        final_response = f"{location_prefix}{combined_answer}"

        # STRICT LANGUAGE ISOLATION: For English queries, ensure ZERO lines of Telugu text leak through
        if not is_te:
            resp_lines = final_response.split("\n")
            sanitized_lines = []
            for line in resp_lines:
                te_chars = len(re.findall(r"[\u0C00-\u0C7F]", line))
                # Drop line if it starts with Telugu or has substantial Telugu characters
                if line.strip() and '\u0C00' <= line.strip()[0] <= '\u0C7F':
                    continue
                if te_chars >= 5 and (te_chars > len(line) * 0.10):
                    continue
                if te_chars > 0 and len(re.findall(r"[a-zA-Z]", line)) < 5:
                    continue
                sanitized_lines.append(line)
            final_response = "\n".join(sanitized_lines).strip()

        return final_response

    def _format_single_chunk(self, chunk: Dict[str, Any], is_te: bool) -> str:
        """
        Extracts clean, readable, language-appropriate content from a retrieved chunk.
        Eliminates raw markdown headers, duplicate notes, and language mismatches.
        """
        raw_text = chunk.get("text", "").strip()
        if not raw_text:
            return ""

        lines = raw_text.split("\n")
        cleaned_lines = []

        # Capture complete multi-line Telugu explanation block if present
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

        te_explanation = "\n".join(te_lines).strip()

        for line in lines:
            s = line.strip()
            if not s:
                continue
            # Strip section header markers like [6. Application...]
            if s.startswith("[") and s.endswith("]"):
                continue
            if s.startswith("#"):
                continue

            # For English queries, omit raw Telugu explanation blocks
            if not is_te and ("తెలుగు వివరణ:" in s or "తెలుగు వివరణ" in s):
                continue

            cleaned_lines.append(s)

        # For Telugu queries with a dedicated Telugu explanation, prioritize it
        if is_te and te_explanation:
            portals_or_helplines = [
                l for l in cleaned_lines
                if ("http" in l or re.search(r"\b(?:108|104|14555|155251|1800-180-1551|14447|1902|1800-425-6776|1800-425-2123)\b", l))
                and "తెలుగు వివరణ" not in l
            ]
            parts = [te_explanation]
            if portals_or_helplines:
                parts.append("\nఅధికారిక పోర్టల్స్ & సంప్రదింపు వివరాలు:")
                parts.extend(portals_or_helplines)
            return "\n".join(parts)

        # For Telugu queries without dedicated te_explanation, filter out pure-English duplicate paragraphs
        if is_te:
            has_any_telugu = any(re.search(r"[\u0C00-\u0C7F]", l) for l in cleaned_lines)
            if has_any_telugu:
                filtered = [
                    l for l in cleaned_lines
                    if re.search(r"[\u0C00-\u0C7F]", l) or re.search(r"https?://|\b\d{4,6}\b", l)
                ]
                if filtered:
                    cleaned_lines = filtered
        else:
            # For English queries, strictly eliminate Telugu lines and sanitize inline Telugu script
            filtered = []
            for l in cleaned_lines:
                clean_l = sanitize_english_text(l)
                if not clean_l or len(re.findall(r"[a-zA-Z]", clean_l)) < 3:
                    continue
                filtered.append(clean_l)
            if filtered:
                cleaned_lines = filtered

        # Return cleanly joined content
        return "\n".join(cleaned_lines)
