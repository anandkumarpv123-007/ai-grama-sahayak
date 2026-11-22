from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, status, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AppBaseException
from app.schemas.health import HealthResponse
from app.schemas.common import ErrorResponse, ErrorBody
from app.schemas.voice import (
    VoiceTranscribeResponse,
    VoiceSpeakRequest,
    VoiceSpeakResponse,
)
from app.schemas.documents import DocumentAnalysisResponse
from app.schemas.services import NearbyServicesResponse
from app.schemas.grievances import GrievanceDraftRequest, GrievanceDraftResponse

# Import Member 1 Routers
from app.api.chat import router as chat_router
from app.api.eligibility import router as eligibility_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Grama Sahayak Backend initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "AI Grama Sahayak — Multilingual Public-Service Assistance Platform.\n"
        "Specialist assistants for Agriculture, Healthcare, Education, and Government Schemes."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Standard Exception Handlers matching API Contracts
# ---------------------------------------------------------
@app.exception_handler(AppBaseException)
async def handle_app_exception(request: Request, exc: AppBaseException) -> JSONResponse:
    error_content = ErrorResponse(
        error=ErrorBody(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=error_content)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    clean_details = []
    for err in exc.errors():
        clean_details.append({
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type"),
        })
    error_content = ErrorResponse(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="The request contains invalid information.",
            details=clean_details,
        )
    ).model_dump()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_content,
    )


@app.exception_handler(StarletteHTTPException)
async def handle_starlette_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else f"HTTP_{exc.status_code}"
    error_content = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=str(exc.detail),
            details=[],
        )
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=error_content)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    error_content = ErrorResponse(
        error=ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            details=[],
        )
    ).model_dump()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_content,
    )


# ---------------------------------------------------------
# Member 1 Endpoints
# ---------------------------------------------------------
@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System Health"],
    summary="Health Check",
    description="Returns service health status, service identifier, and current version.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="ai-grama-sahayak",
        version=settings.VERSION,
    )


# Register Member 1 owned API routers
app.include_router(chat_router, prefix="/api", tags=["Chat & Agents (M1)"])
app.include_router(eligibility_router, prefix="/api", tags=["Eligibility (M1)"])


# ---------------------------------------------------------
# Router Registration for Members 3 & 4
# Only register placeholders when the module is genuinely absent from disk.
# If the module exists, import directly so internal errors are never silently masked.
# ---------------------------------------------------------
import importlib.util

# 1. Voice Router (Member 3)
if importlib.util.find_spec("app.api.voice") is not None:
    from app.api.voice import router as voice_router
    app.include_router(voice_router, prefix="/api", tags=["Voice Services (M3)"])
    logger.info("Loaded Member 3 voice router from app.api.voice.")
else:
    from fastapi import APIRouter
    voice_placeholder = APIRouter(prefix="/api/voice", tags=["Voice Services (M3 Placeholder)"])

    @voice_placeholder.post(
        "/transcribe",
        response_model=VoiceTranscribeResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Voice Transcription Placeholder (M3)",
        description="Pending Member 3 voice transcription module integration.",
    )
    async def placeholder_transcribe(
        file: UploadFile = File(...),
        language: str = Form("en"),
    ) -> JSONResponse:
        error_content = ErrorResponse(
            error=ErrorBody(
                code="SERVICE_UNAVAILABLE",
                message="Voice transcription service is temporarily unavailable (pending Member 3 integration).",
                details=[],
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_content)

    @voice_placeholder.post(
        "/speak",
        response_model=VoiceSpeakResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Voice Synthesis Placeholder (M3)",
        description="Pending Member 3 voice synthesis module integration.",
    )
    async def placeholder_speak(request: VoiceSpeakRequest) -> JSONResponse:
        error_content = ErrorResponse(
            error=ErrorBody(
                code="SERVICE_UNAVAILABLE",
                message="Voice synthesis service is temporarily unavailable (pending Member 3 integration).",
                details=[],
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_content)

    app.include_router(voice_placeholder)
    logger.info("Registered Member 3 voice placeholder router (module genuinely absent; returns HTTP 503).")

# 2. Document Analysis Router (Member 4)
if importlib.util.find_spec("app.api.documents") is not None:
    from app.api.documents import router as documents_router
    app.include_router(documents_router, prefix="/api", tags=["Document Services (M4)"])
    logger.info("Loaded Member 4 documents router from app.api.documents.")
else:
    from fastapi import APIRouter
    documents_placeholder = APIRouter(prefix="/api/documents", tags=["Document Services (M4 Placeholder)"])

    @documents_placeholder.post(
        "/analyze",
        response_model=DocumentAnalysisResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Document Analysis Placeholder (M4)",
        description="Pending Member 4 document analysis module integration.",
    )
    async def placeholder_analyze(
        file: UploadFile = File(...),
        document_type: Optional[str] = Form(None),
    ) -> JSONResponse:
        error_content = ErrorResponse(
            error=ErrorBody(
                code="SERVICE_UNAVAILABLE",
                message="Document analysis service is temporarily unavailable (pending Member 4 integration).",
                details=[],
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_content)

    app.include_router(documents_placeholder)
    logger.info("Registered Member 4 documents placeholder router (module genuinely absent; returns HTTP 503).")

# 3. Nearby Services Router (Member 4)
if importlib.util.find_spec("app.api.services") is not None:
    from app.api.services import router as services_router
    app.include_router(services_router, prefix="/api", tags=["Nearby Services (M4)"])
    logger.info("Loaded Member 4 services router from app.api.services.")
else:
    from fastapi import APIRouter
    services_placeholder = APIRouter(prefix="/api/services", tags=["Nearby Services (M4 Placeholder)"])

    @services_placeholder.get(
        "/nearby",
        response_model=NearbyServicesResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Nearby Public Services Placeholder (M4)",
        description="Pending Member 4 nearby services module integration.",
    )
    async def placeholder_nearby(
        service_type: Optional[str] = Query(None),
        district: Optional[str] = Query(None),
        latitude: Optional[float] = Query(None),
        longitude: Optional[float] = Query(None),
    ) -> JSONResponse:
        error_content = ErrorResponse(
            error=ErrorBody(
                code="SERVICE_UNAVAILABLE",
                message="Nearby public services lookup is temporarily unavailable (pending Member 4 integration).",
                details=[],
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_content)

    app.include_router(services_placeholder)
    logger.info("Registered Member 4 services placeholder router (module genuinely absent; returns HTTP 503).")

# 4. Grievance Redressal Router (Member 4)
if importlib.util.find_spec("app.api.grievances") is not None:
    from app.api.grievances import router as grievances_router
    app.include_router(grievances_router, prefix="/api", tags=["Grievances (M4)"])
    logger.info("Loaded Member 4 grievances router from app.api.grievances.")
else:
    from fastapi import APIRouter
    grievances_placeholder = APIRouter(prefix="/api/grievances", tags=["Grievances (M4 Placeholder)"])

    @grievances_placeholder.post(
        "/draft",
        response_model=GrievanceDraftResponse,
        responses={503: {"model": ErrorResponse}},
        summary="Grievance Drafting Placeholder (M4)",
        description="Pending Member 4 grievance drafting module integration.",
    )
    async def placeholder_grievance(request: GrievanceDraftRequest) -> JSONResponse:
        error_content = ErrorResponse(
            error=ErrorBody(
                code="SERVICE_UNAVAILABLE",
                message="Grievance drafting service is temporarily unavailable (pending Member 4 integration).",
                details=[],
            )
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=error_content)

    app.include_router(grievances_placeholder)
    logger.info("Registered Member 4 grievances placeholder router (module genuinely absent; returns HTTP 503).")
