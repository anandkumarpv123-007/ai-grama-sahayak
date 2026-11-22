from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class DocumentAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_type: str = Field(..., description="Classification or type of analyzed document")
    extracted_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs extracted from document content",
    )
    checklist_status: str = Field(
        ...,
        description="Verification checklist status: complete, partially_complete, incomplete, unreadable",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Required fields not present in document",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings regarding legibility, validity or potential inconsistencies",
    )
