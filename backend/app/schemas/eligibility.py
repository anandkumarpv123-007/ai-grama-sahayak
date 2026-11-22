from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LanguageCode, Source


class EligibilityStatus(str, Enum):
    """
    The exactly agreed four status values for eligibility check.
    Do not add or modify status values.
    """
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    NEEDS_MORE_INFORMATION = "needs_more_information"
    UNABLE_TO_VERIFY = "unable_to_verify"


class EligibilityRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scheme_id: str = Field(..., description="Unique scheme identifier to evaluate against")
    language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Response language preference (en or te)",
    )
    applicant_profile: Dict[str, Any] = Field(
        ...,
        description="Key-value mapping of applicant profile attributes (e.g., age, occupation, income, state)",
    )


class EligibilityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scheme_id: str = Field(..., description="Unique scheme identifier evaluated")
    status: EligibilityStatus = Field(
        ...,
        description="Eligibility result status: eligible, ineligible, needs_more_information, unable_to_verify",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="List of factual reasons supporting the status evaluation",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Profile fields required by scheme rules that were missing from the applicant profile",
    )
    benefits: List[str] = Field(
        default_factory=list,
        description="Benefits provided under this scheme if eligible",
    )
    required_documents: List[str] = Field(
        default_factory=list,
        description="Official documents required to apply for the scheme",
    )
    application_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step procedure to apply via official channels",
    )
    sources: List[Source] = Field(
        default_factory=list,
        description="Verified government sources documenting these scheme rules",
    )
