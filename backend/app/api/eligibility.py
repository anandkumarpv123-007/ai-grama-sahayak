import logging
from fastapi import APIRouter, status
from app.schemas.eligibility import EligibilityRequest, EligibilityResponse
from app.core.eligibility_rules import evaluate_scheme_eligibility
from app.core.exceptions import BadRequestException
from app.database.session import get_session_factory
from app.models.eligibility_log import EligibilityAudit

logger = logging.getLogger("ai_grama_sahayak.api.eligibility")

router = APIRouter()


def _save_eligibility_audit_safely(
    request: EligibilityRequest,
    response: EligibilityResponse,
) -> None:
    """
    Safely records eligibility assessment in PostgreSQL for audit and transparency.
    Non-blocking if database is unavailable.
    """
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            audit = EligibilityAudit(
                scheme_id=response.scheme_id,
                status=response.status.value,
                language=request.language.value,
                missing_fields=response.missing_fields if response.missing_fields else None,
            )
            session.add(audit)
            session.commit()
    except Exception as exc:
        logger.debug("Eligibility audit log skipped/failed: %s", exc)


@router.post(
    "/eligibility/check",
    response_model=EligibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Scheme Eligibility Evaluation",
    description=(
        "Evaluates citizen eligibility against deterministic, documented scheme rules. "
        "Returns only the agreed statuses: eligible, ineligible, needs_more_information, unable_to_verify."
    ),
)
async def check_eligibility_endpoint(request: EligibilityRequest) -> EligibilityResponse:
    scheme_id = request.scheme_id.strip()
    if not scheme_id:
        raise BadRequestException(
            message="scheme_id cannot be blank.",
            code="EMPTY_SCHEME_ID",
        )

    # Deterministic rule evaluation
    result = evaluate_scheme_eligibility(
        scheme_id=scheme_id,
        applicant_profile=request.applicant_profile,
        language=request.language,
    )

    response = EligibilityResponse(
        scheme_id=result["scheme_id"],
        status=result["status"],
        reasons=result["reasons"],
        missing_fields=result["missing_fields"],
        benefits=result["benefits"],
        required_documents=result["required_documents"],
        application_steps=result["application_steps"],
        sources=result["sources"],
    )

    _save_eligibility_audit_safely(request, response)
    return response
