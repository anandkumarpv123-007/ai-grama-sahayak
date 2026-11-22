from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LanguageCode(str, Enum):
    """
    Agreed language codes for AI Grama Sahayak.
    Note: Hindi ('hi') is explicitly excluded from the initial API contract
    and will be extended after Telugu and English work reliably.
    """
    EN = "en"
    TE = "te"


class AssistantIdentifier(str, Enum):
    """
    Agreed specialist assistant identifiers.
    """
    AGRICULTURE = "agriculture"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SCHEMES = "schemes"


class Source(BaseModel):
    """
    Agreed common verified source structure.
    Never invent fake government sources.
    """
    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., description="Official title of the verified source")
    url: str = Field(..., description="URL to the official verified source")
    publisher: str = Field(..., description="Government department or authoritative publisher")
    verified_at: str = Field(..., description="Date when source was verified, e.g. YYYY-MM-DD")


class ErrorBody(BaseModel):
    code: str = Field(..., description="Error code string (e.g. VALIDATION_ERROR, NOT_FOUND)")
    message: str = Field(..., description="User-friendly error message")
    details: List[Any] = Field(default_factory=list, description="Optional diagnostic details")


class ErrorResponse(BaseModel):
    """
    Agreed standard error response format across all endpoints.
    """
    error: ErrorBody
