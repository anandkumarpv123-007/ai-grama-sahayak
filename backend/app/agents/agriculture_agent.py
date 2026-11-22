from typing import List, Optional
from app.agents.base import BaseSpecialistAgent
from app.schemas.common import AssistantIdentifier, LanguageCode


class AgricultureAgent(BaseSpecialistAgent):
    """
    Specialist Agent for Agriculture and Farmer Services.
    Covers crop advisory, fertilizer/seed subsidies, Rythu Bharosa Kendram (RBK) services,
    irrigation, crop insurance (e-Panta, PMFBY), and agricultural market assistance.
    """

    def __init__(self):
        super().__init__(
            assistant_id=AssistantIdentifier.AGRICULTURE,
            name="Agriculture Specialist",
            domain="Farming, Crop Advisory, PM-Kisan & Rythu Bharosa",
            description="Assists farmers with crop advisories, subsidies, and agricultural schemes.",
        )

    def get_safety_notice(self, language: LanguageCode) -> Optional[str]:
        if language == LanguageCode.TE:
            return (
                "వ్యవసాయ సలహా: ఎరువుల మోతాదు, పురుగుమందుల వాడకం మరియు సాగు పద్ధతులు స్థానిక నేల స్వభావం, "
                "వాతావరణంపై ఆధారపడి ఉంటాయి. అమలు చేయడానికి ముందు దయచేసి మీ స్థానిక రైతు భరోసా కేంద్రం (RBK) లేదా "
                "వ్యవసాయ విస్తరణ అధికారిని (AEO) సంప్రదించండి."
            )
        return (
            "Agricultural Advisory: Crop management, pesticide application, and fertilizer dosage depend on "
            "local agro-climatic conditions and soil health. Please verify recommendations with your local Rythu "
            "Bharosa Kendram (RBK) or Agricultural Extension Officer before implementation."
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
                f"మీకు సమీపంలోని రైతు భరోసా కేంద్రం (RBK){loc_te} వివరాలు కావాలా?",
                "ఈ పంటకు సంబంధించి ఉచిత పంటల బీమా లేదా ఈ-పంట (e-Panta) నమోదు వివరాలు తెలుసుకోవాలా?",
                "సబ్సిడీ ఎరువులు మరియు విత్తనాల లభ్యత గురించి మరింత సమాచారం కావాలా?",
            ]
        return [
            f"Would you like details on your nearest Rythu Bharosa Kendram (RBK){loc}?",
            "Do you need steps for e-Panta crop booking or crop insurance enrollment?",
            "Would you like information on subsidized seeds, fertilizers, or farm machinery?",
        ]
