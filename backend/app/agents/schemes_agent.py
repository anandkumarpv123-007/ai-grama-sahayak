from typing import List, Optional
from app.agents.base import BaseSpecialistAgent
from app.schemas.common import AssistantIdentifier, LanguageCode


class SchemesAgent(BaseSpecialistAgent):
    """
    Specialist Agent for Public Welfare Schemes and Social Security.
    Covers welfare schemes, social security pensions (Pension Kanuka), ration card services (Rice Cards),
    housing schemes, women empowerment schemes (Aasara, Cheyutha), and Grama/Ward Sachivalayam delivery.
    """

    def __init__(self):
        super().__init__(
            assistant_id=AssistantIdentifier.SCHEMES,
            name="Government Schemes Specialist",
            domain="Welfare Schemes, Social Security Pensions, Ration Cards & Housing",
            description="Assists citizens with eligibility, documentation, and application steps for state and central government schemes.",
        )

    def get_safety_notice(self, language: LanguageCode) -> Optional[str]:
        if language == LanguageCode.TE:
            return (
                "పథకాల సలహా: ప్రభుత్వ సంక్షేమ పథకాల మార్గదర్శకాలు, ఆదాయ పరిమితులు మరియు లబ్ధిదారుల ఎంపిక నిబంధనలు "
                "ప్రభుత్వ జీవోలకు (GOs) లోబడి ఉంటాయి. దరఖాస్తును మీ స్థానిక గ్రామ/వార్డు సచివాలయంలో మాత్రమే సమర్పించండి. "
                "మధ్యవర్తులను నమ్మవద్దు."
            )
        return (
            "Public Schemes Advisory: Welfare scheme eligibility thresholds, required documentation, and benefit "
            "disbursements are subject to official government guidelines and periodic beneficiary verification. "
            "Always submit applications directly through your local Grama / Ward Sachivalayam or official government portals. "
            "Never pay money to unauthorized intermediaries."
        )

    def get_default_follow_up_questions(
        self,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[str]:
        if language == LanguageCode.TE:
            return [
                "మీ అర్హతను స్వయంచాలకంగా తనిఖీ చేయడానికి అర్హత కాలిక్యులేటర్ (Eligibility Check) ఉపయోగించాలనుకుంటున్నారా?",
                "ఈ పథకానికి దరఖాస్తు చేయడానికి అవసరమైన అధికారిక ధృవపత్రాల జాబితా కావాలా?",
                "గ్రామ/వార్డు సచివాలయంలో దరఖాస్తు సమర్పించే విధానం మరియు రశీదు ట్రాకింగ్ వివరాలు తెలుసుకోవాలా?",
            ]
        return [
            "Would you like to check your eligibility using our official scheme eligibility checker?",
            "Do you need the complete list of mandatory documents for this scheme?",
            "Would you like steps to submit and track your application via your Grama / Ward Sachivalayam?",
        ]
