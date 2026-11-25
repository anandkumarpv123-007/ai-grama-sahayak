from typing import Any, Dict, List, Optional
from app.agents.base import BaseSpecialistAgent
from app.schemas.common import AssistantIdentifier, LanguageCode
from app.core.emergency_detector import check_clinical_emergency


class HealthcareAgent(BaseSpecialistAgent):
    """
    Specialist Agent for Public Healthcare and Medical Schemes.
    Covers PHC/CHC network, Dr. YSR Aarogyasri, Ayushman Bharat, maternal health,
    immunization schedules, 104 health advice, and 108 emergency services.
    """

    def __init__(self):
        super().__init__(
            assistant_id=AssistantIdentifier.HEALTHCARE,
            name="Healthcare Specialist",
            domain="Public Health, Aarogyasri, PHC Clinics, Maternal & Child Health",
            description="Provides citizens with verified information on public health facilities, schemes, and preventive care.",
        )

    def get_safety_notice(self, language: LanguageCode) -> Optional[str]:
        if language == LanguageCode.TE:
            return (
                "వైద్య హెచ్చరిక: ఈ సమాచారం ప్రజారోగ్య అవగాహన కొరకు మాత్రమే. ఇది వైద్యుని ప్రత్యక్ష సలహా లేదా చికిత్సకు "
                "ప్రత్యామ్నాయం కాదు. అత్యవసర పరిస్థితుల్లో వెంటనే 108 కు కాల్ చేయండి లేదా సమీప ప్రాథమిక ఆరోగ్య కేంద్రాన్ని (PHC) సంప్రదించండి."
            )
        return (
            "Medical Disclaimer: This information is for public awareness and healthcare facilitation only. "
            "It is not a substitute for professional medical consultation, diagnosis, or treatment. "
            "In case of medical emergencies, immediately dial 108 or visit your nearest government hospital/PHC."
        )

    def get_default_follow_up_questions(
        self,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[str]:
        loc = f" in {district}" if district else ""
        loc_te = f" {district} లో" if district else ""
        if language == LanguageCode.TE:
            return [
                f"మీకు సమీపంలోని నెట్‌వర్క్ ఆసుపత్రి లేదా ప్రాథమిక ఆరోగ్య కేంద్రం (PHC){loc_te} వివరాలు కావాలా?",
                "ఆరోగ్యశ్రీ (Aarogyasri) కార్డు ద్వారా ఉచిత చికిత్స లభించే వ్యాధుల జాబితా తెలుసుకోవాలా?",
                "తల్లి మరియు బిడ్డ సంక్షేమ పథకాలు లేదా వ్యాక్సినేషన్ షెడ్యూల్ వివరాలు కావాలా?",
            ]
        return [
            f"Would you like to locate the nearest PHC or empaneled government hospital{loc}?",
            "Do you need to check if a specific treatment or surgery is covered under Dr. YSR Aarogyasri / Ayushman Bharat?",
            "Would you like information on maternal health assistance or child immunization schedules?",
        ]

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
        Processes healthcare queries, intercepting clinical emergencies before retrieval
        or fallbacks.
        """
        emergency_result = check_clinical_emergency(query, language)
        if emergency_result:
            return emergency_result

        return super().process_query(
            query=query,
            language=language,
            state=state,
            district=district,
            retrieved_chunks=retrieved_chunks,
            retrieval_outcome=retrieval_outcome,
        )
