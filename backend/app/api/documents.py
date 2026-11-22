"""API Router for Document Analysis.

Endpoint:
POST /api/documents/analyze (when mounted under /api)

Prefix: /documents

Accepts:
- file: UploadFile (PDF, JPG, PNG; max 10 MB)
- document_type: Optional[str] (form field)

Responses strictly follow the frozen API contracts in docs/api_contracts.md.
"""

from typing import Optional, Dict, Any, List
import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from app.schemas.documents import DocumentAnalysisResponse

from app.services.documents.analyzer import (
    analyze_document_content,
    DocumentAnalysisError,
    OversizedFileError,
    InvalidFileTypeError,
    MAX_UPLOAD_BYTES,
)

logger = logging.getLogger(__name__)

# Router prefix is "/documents"; when Member 1 mounts under prefix="/api",
# the final endpoint path is exactly POST /api/documents/analyze
router = APIRouter(prefix="/documents", tags=["documents"])


def _make_error_response(code: str, message: str, status_code: int, details: Optional[List[Any]] = None) -> JSONResponse:
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


def read_upload_stream(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES, chunk_size: int = 64 * 1024) -> bytes:
    """Read an uploaded file in chunks, enforcing max_bytes limit on the fly without buffering oversized files."""
    raw_file = getattr(file, "file", file)
    if not hasattr(raw_file, "read"):
        if hasattr(file, "read"):
            raw_file = file
        else:
            raise DocumentAnalysisError(
                code="FILE_READ_ERROR",
                message="Uploaded file object is not readable.",
                status_code=400,
            )

    chunks: List[bytes] = []
    total_read = 0

    while True:
        chunk = raw_file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_bytes:
            raise OversizedFileError(total_read)
        chunks.append(chunk)

    if total_read == 0:
        raise DocumentAnalysisError(
            code="EMPTY_FILE",
            message="Uploaded file is empty (0 bytes).",
            status_code=400,
        )

    return b"".join(chunks)


@router.post("/analyze", response_model=DocumentAnalysisResponse)
def analyze_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
):
    """Analyze an uploaded citizen public document (PDF, JPG, PNG).

    Extracts text, identifies document types, parses structured fields,
    evaluates missing checklist items, and returns warnings.

    Enforces 10 MB maximum size limit during stream reading and validates file format/MIME type.
    """
    if not file or not getattr(file, "filename", None):
        return _make_error_response(
            code="VALIDATION_ERROR",
            message="No file uploaded or missing filename.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Read stream with on-the-fly size enforcement (aborts immediately if > 10 MB)
    try:
        content = read_upload_stream(file, max_bytes=MAX_UPLOAD_BYTES)
    except OversizedFileError as e:
        return _make_error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code,
        )
    except DocumentAnalysisError as e:
        return _make_error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code,
        )
    except Exception as e:
        logger.exception("Failed to read uploaded file stream: %s", str(e))
        return _make_error_response(
            code="FILE_READ_ERROR",
            message="Failed to read the uploaded file stream.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = analyze_document_content(
            content=content,
            filename=file.filename,
            content_type=getattr(file, "content_type", None),
            document_type_hint=document_type,
        )
        return result
    except OversizedFileError as e:
        return _make_error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code,
        )
    except InvalidFileTypeError as e:
        return _make_error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code,
        )
    except DocumentAnalysisError as e:
        return _make_error_response(
            code=e.code,
            message=e.message,
            status_code=e.status_code,
        )
    except Exception:
        # Server-side logging of unexpected errors, returning generic public message
        logger.exception("Unexpected error occurred during document analysis")
        return _make_error_response(
            code="SERVER_ERROR",
            message="An unexpected server error occurred while analyzing the document.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
