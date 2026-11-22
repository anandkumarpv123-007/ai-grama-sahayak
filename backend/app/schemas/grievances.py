from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LanguageCode


class GrievanceDraftRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str = Field(..., description="Category of civic grievance (e.g. water_supply, road_repair, electricity, sanitation)")
    description: str = Field(..., min_length=5, description="Citizen description of the issue or complaint")
    district: str = Field(..., description="District where the issue occurred")
    mandal: str = Field(..., description="Mandal or sub-district where the issue occurred")
    language: LanguageCode = Field(default=LanguageCode.EN, description="Response language (en or te)")


class GrievanceDraftResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subject: str = Field(..., description="Formal subject line suitable for official submission")
    complaint_body: str = Field(..., description="Polite, structured formal draft of the complaint")
    recommended_next_steps: List[str] = Field(
        default_factory=list,
        description="Actionable steps for the citizen to submit through official grievance channels",
    )
    official_links: List[str] = Field(
        default_factory=list,
        description="Official grievance redressal portals (e.g., Spandana, CPGRAMS)",
    )
