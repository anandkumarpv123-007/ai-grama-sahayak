from typing import List, Optional
from app.agents.base import BaseSpecialistAgent
from app.schemas.common import AssistantIdentifier, LanguageCode


class EducationAgent(BaseSpecialistAgent):
    """
    Specialist Agent for Public Education and Scholarship Assistance.
    Covers government schools, fee reimbursement (Vidya Deevena), hostel allowances (Vasathi Deevena),
    Amma Vodi, post-matric scholarships, and university admission guidelines.
    """

    def __init__(self):
        super().__init__(
            assistant_id=AssistantIdentifier.EDUCATION,
            name="Education Specialist",
            domain="School Education, Scholarships, Fee Reimbursement & JnanaBhumi",
            description="Assists students and parents with scholarships, educational benefits, and school admission guidelines.",
        )

    def get_safety_notice(self, language: LanguageCode) -> Optional[str]:
        if language == LanguageCode.TE:
            return (
                "విద్యా సలహా: స్కాలర్‌షిప్‌లు, ఫీజు రీయింబర్స్‌మెంట్ మరియు అడ్మిషన్ల గడువులు అధికారిక ప్రభుత్వ ఉత్తర్వులకు "
                "లోబడి ఉంటాయి. ఎల్లప్పుడూ జ్ఞానభూమి (JnanaBhumi) అధికారిక పోర్టల్ లేదా మీ విద్యాసంస్థ ద్వారా మాత్రమే ధృవీకరించుకోండి."
            )
        return (
            "Educational Advisory: Scholarship eligibility, fee reimbursement disbursements, and academic deadlines "
            "are governed by official Department of Higher/School Education notifications. Please cross-verify through "
            "the official JnanaBhumi portal or your educational institution."
        )

    def get_default_follow_up_questions(
        self,
        language: LanguageCode,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[str]:
        if language == LanguageCode.TE:
            return [
                "జగనన్న విద్యా దీవెన లేదా వసతి దీవెన స్కాలర్‌షిప్ దరఖాస్తు విధానం తెలుసుకోవాలా?",
                "దరఖాస్తు చేయడానికి కావలసిన ధృవపత్రాల (ఆదాయ, కుల, బోనఫైడ్) జాబితా కావాలా?",
                "జ్ఞానభూమి పోర్టల్‌లో అప్లికేషన్ స్టేటస్ ఎలా చెక్ చేయాలో తెలుసుకోవాలా?",
            ]
        return [
            "Would you like the application procedure for Jagananna Vidya Deevena or Vasathi Deevena?",
            "Do you need a checklist of required documents (income, caste, student bonafide certificate)?",
            "Would you like to know how to track your scholarship status on the JnanaBhumi portal?",
        ]
