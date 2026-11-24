import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, status
from app.schemas.eligibility import EligibilityRequest, EligibilityResponse
from app.core.eligibility_rules import evaluate_scheme_eligibility
from app.core.exceptions import BadRequestException
from app.core.config import settings
from app.database.session import (
    get_session_factory,
    get_database_status,
    DatabaseStatus,
    record_db_failure,
    record_db_success,
)
from app.models.eligibility_log import EligibilityAudit

logger = logging.getLogger("ai_grama_sahayak.api.eligibility")

router = APIRouter()


def _save_eligibility_audit_safely(
    request: EligibilityRequest,
    response: EligibilityResponse,
) -> None:
    """
    Safely records eligibility assessment in PostgreSQL for audit and transparency.
    Completely non-blocking when database is disabled, unconfigured, or unreachable.
    Does not expose sensitive applicant information or credentials in logs.
    """
    try:
        if not getattr(settings, "DATABASE_AUDIT_ENABLED", True):
            logger.debug("Eligibility audit log skipped: DATABASE_AUDIT_ENABLED is False.")
            return

        db_status = get_database_status(timeout=0.3)
        if db_status != DatabaseStatus.AVAILABLE_OPERATIONAL:
            logger.debug(
                "Eligibility audit log skipped: database is %s.",
                db_status.value,
            )
            return

        session_factory = get_session_factory()
        session = session_factory()
        try:
            audit = EligibilityAudit(
                scheme_id=response.scheme_id,
                status=response.status.value,
                language=request.language.value,
                missing_fields=response.missing_fields if response.missing_fields else None,
            )
            session.add(audit)
            session.commit()
            record_db_success()
            logger.debug(
                "Eligibility audit log successfully saved for scheme '%s'.",
                response.scheme_id,
            )
        except Exception as exc:
            session.rollback()
            record_db_failure()
            # Safe logging without exposing credentials or applicant PII
            logger.debug(
                "Eligibility audit log skipped/failed: %s",
                type(exc).__name__,
            )
        finally:
            session.close()
    except Exception as exc:
        record_db_failure()
        # Safe logging without exposing credentials or applicant PII
        logger.debug(
            "Eligibility audit log skipped/failed: %s",
            type(exc).__name__,
        )


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
async def check_eligibility_endpoint(
    request: EligibilityRequest,
    background_tasks: BackgroundTasks = None,
) -> EligibilityResponse:
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

    # Dispatch audit logging safely as background task to ensure event loop is never blocked
    if background_tasks is not None:
        background_tasks.add_task(_save_eligibility_audit_safely, request, response)
    else:
        _save_eligibility_audit_safely(request, response)

    return response
