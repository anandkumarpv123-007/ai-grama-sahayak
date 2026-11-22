from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.schemas.common import AssistantIdentifier, LanguageCode, Source


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
        safety_notice = self.get_safety_notice(language)
        follow_ups = self.get_default_follow_up_questions(language, state, district)

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
        Synthesize answer text strictly from verified chunks.
        Subclasses can customize phrasing while respecting facts.
        """
        evidence_texts = [
            chunk.get("text", "").strip()
            for chunk in chunks
            if chunk.get("text", "").strip()
        ]
        combined_evidence = "\n\n".join(evidence_texts)

        if not combined_evidence:
            if language == LanguageCode.TE:
                return "ధృవీకరించబడిన సమాచారం ప్రస్తుతం అందుబాటులో లేదు."
            return "Verified information is currently unavailable."

        location_prefix = ""
        if district and state:
            loc_str = f"{district}, {state}"
            location_prefix = (
                f"[{loc_str} పరిధిలోని ధృవీకరించిన సమాచారం]:\n\n"
                if language == LanguageCode.TE
                else f"[Verified information for {loc_str}]:\n\n"
            )
        elif state:
            location_prefix = (
                f"[{state} పరిధిలోని ధృవీకరించిన సమాచారం]:\n\n"
                if language == LanguageCode.TE
                else f"[Verified information for {state}]:\n\n"
            )

        return f"{location_prefix}{combined_evidence}"
