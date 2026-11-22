"""API Router for Grievance Drafting.

Endpoint:
POST /api/grievances/draft (when mounted under /api)

Prefix: /grievances

Accepts JSON:
- category: str
- description: str
- district: str
- mandal: str
- language: str ('en' or 'te')

Responses strictly follow the frozen API contracts in docs/api_contracts.md.
"""

from typing import Optional, List, Dict, Any
import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.schemas.grievances import (
    GrievanceDraftRequest,
    GrievanceDraftResponse,
)

from app.services.grievances.drafter import draft_grievance

logger = logging.getLogger(__name__)

# Router prefix is "/grievances"; when Member 1 mounts under prefix="/api",
# the final endpoint path is exactly POST /api/grievances/draft
router = APIRouter(prefix="/grievances", tags=["grievances"])


def _make_error_response(code: str, message: str, status_code: int = 400, details: Optional[List[Any]] = None) -> JSONResponse:
    """Format an error response following the shared API contract."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            }
        },
    )


@router.post("/draft", response_model=GrievanceDraftResponse)
def create_grievance_draft(request: GrievanceDraftRequest):
    """Draft a respectful and structured citizen grievance letter.

    Generates formal representations in Telugu ('te') or English ('en')
    with verified Andhra Pradesh official submission channels (Spandana / Sachivalayam).

    Guardrails:
    - Never claims the grievance has been submitted.
    - Never claims live tracking without an authorised integration.
    """
    category = getattr(request, "category", None)
    description = getattr(request, "description", None)
    district = getattr(request, "district", None)
    mandal = getattr(request, "mandal", None)
    language = getattr(request, "language", "en")

    missing_fields = []
    if not category or not str(category).strip():
        missing_fields.append("category")
    if not description or not str(description).strip():
        missing_fields.append("description")
    if not district or not str(district).strip():
        missing_fields.append("district")
    if not mandal or not str(mandal).strip():
        missing_fields.append("mandal")

    if missing_fields:
        return _make_error_response(
            code="VALIDATION_ERROR",
            message=f"Missing required fields: {', '.join(missing_fields)}.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=missing_fields,
        )

    clean_lang = str(language).strip().lower()
    if clean_lang not in ("en", "te"):
        return _make_error_response(
            code="VALIDATION_ERROR",
            message=f"Unsupported language '{language}'. Supported languages are 'en' (English) and 'te' (Telugu).",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        draft = draft_grievance(
            category=str(category),
            description=str(description),
            district=str(district),
            mandal=str(mandal),
            language=clean_lang,
        )
        return draft
    except ValueError as e:
        return _make_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        # Server-side logging of unexpected errors, returning generic public message
        logger.exception("Unexpected error occurred while generating grievance draft")
        return _make_error_response(
            code="SERVER_ERROR",
            message="An unexpected server error occurred while drafting the grievance.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
