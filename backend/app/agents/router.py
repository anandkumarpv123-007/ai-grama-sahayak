import logging
from typing import Any, Dict, List, Optional
from app.agents.base import BaseSpecialistAgent
from app.agents.agriculture_agent import AgricultureAgent
from app.agents.healthcare_agent import HealthcareAgent
from app.agents.education_agent import EducationAgent
from app.agents.schemes_agent import SchemesAgent
from app.schemas.common import AssistantIdentifier, LanguageCode
from app.core.exceptions import BadRequestException

logger = logging.getLogger("ai_grama_sahayak.agents.router")


class AgentRouter:
    """
    Central router that selects and coordinates specialist agents.
    Provides modular routing across the 4 specialist domains without creating
    unrelated, disconnected chatbots.
    """

    def __init__(self):
        self._agents: Dict[AssistantIdentifier, BaseSpecialistAgent] = {
            AssistantIdentifier.AGRICULTURE: AgricultureAgent(),
            AssistantIdentifier.HEALTHCARE: HealthcareAgent(),
            AssistantIdentifier.EDUCATION: EducationAgent(),
            AssistantIdentifier.SCHEMES: SchemesAgent(),
        }

    def get_agent(self, assistant: AssistantIdentifier | str) -> BaseSpecialistAgent:
        """
        Retrieves the specialist agent corresponding to the assistant identifier.
        """
        try:
            assistant_id = (
                assistant
                if isinstance(assistant, AssistantIdentifier)
                else AssistantIdentifier(assistant)
            )
        except ValueError:
            valid_assistants = [a.value for a in AssistantIdentifier]
            raise BadRequestException(
                message=f"Unknown assistant '{assistant}'. Must be one of: {', '.join(valid_assistants)}.",
                code="INVALID_ASSISTANT",
            )

        agent = self._agents.get(assistant_id)
        if not agent:
            raise BadRequestException(
                message=f"Assistant '{assistant_id}' is not configured.",
                code="ASSISTANT_NOT_CONFIGURED",
            )
        return agent

    def classify_intent(self, text: str) -> AssistantIdentifier:
        """
        Optional heuristic intent classifier based on bilingual keywords
        for routing assistance or verification.
        """
        text_lower = text.lower()

        # Keywords for Agriculture
        agri_keywords = [
            "crop", "farmer", "farming", "seed", "fertilizer", "pesticide",
            "soil", "paddy", "rythu", "kisan", "irrigation", "cultivation",
            "పంట", "రైతు", "విత్తనాలు", "ఎరువులు", "వ్యవసాయం", "వరి", "పంటల బీమా"
        ]
        # Keywords for Healthcare
        health_keywords = [
            "hospital", "doctor", "health", "medicine", "clinic", "fever",
            "treatment", "aarogyasri", "ayushman", "phc", "ambulance",
            "ఆసుపత్రి", "వైద్యుడు", "ఆరోగ్యం", "మందులు", "జ్వరం", "ఆరోగ్యశ్రీ", "చికిత్స"
        ]
        # Keywords for Education
        edu_keywords = [
            "school", "college", "scholarship", "fee", "education", "student",
            "vidya", "vasathi", "deevena", "hostel", "admission", "jnanabhumi",
            "పాఠశాల", "కళాశాల", "స్కాలర్‌షిప్", "విద్యా", "విద్యార్థి", "ఫీజు", "వసతి"
        ]
        # Keywords for Schemes
        schemes_keywords = [
            "pension", "ration", "rice card", "scheme", "subsidy", "yojana",
            "cheyutha", "aasara", "illu", "sachivalayam", "beneficiary",
            "పింఛన్", "రేషన్", "పథకం", "సచివాలయం", "చేయూత", "ఆసరా", "ఇల్లు"
        ]

        def count_matches(keywords: List[str]) -> int:
            return sum(1 for kw in keywords if kw in text_lower)

        scores = {
            AssistantIdentifier.AGRICULTURE: count_matches(agri_keywords),
            AssistantIdentifier.HEALTHCARE: count_matches(health_keywords),
            AssistantIdentifier.EDUCATION: count_matches(edu_keywords),
            AssistantIdentifier.SCHEMES: count_matches(schemes_keywords),
        }

        best_assistant = max(scores, key=scores.get)
        if scores[best_assistant] > 0:
            return best_assistant
        return AssistantIdentifier.SCHEMES

    def route_and_process(
        self,
        query: str,
        assistant: AssistantIdentifier,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        retrieval_outcome: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches query processing to the designated specialist agent.
        """
        agent = self.get_agent(assistant)
        logger.info(
            "Routing query to %s [language=%s, district=%s, state=%s]",
            agent.name,
            language.value,
            district,
            state,
        )
        return agent.process_query(
            query=query,
            language=language,
            state=state,
            district=district,
            retrieved_chunks=retrieved_chunks,
            retrieval_outcome=retrieval_outcome,
        )


agent_router = AgentRouter()
