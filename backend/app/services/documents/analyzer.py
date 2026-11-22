"""Document Analyzer Service.

Provides complete document validation (MIME, extension, magic bytes, size limits),
in-memory text extraction, field parsing, checklist status determination,
and citizen safety warnings.
"""

from typing import Dict, Any, List, Optional
import os

from .extractor import extract_text_from_pdf, extract_text_from_image
from .field_parser import (
    detect_document_type,
    parse_fields_from_text,
    evaluate_checklist,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/pjpeg",
    "image/x-png",
}

# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}

DISCLAIMER_WARNING = (
    "Extracted data is provisional and not automatically verified. "
    "Please verify with the original document."
)


class DocumentAnalysisError(Exception):
    """Base exception for document analysis errors."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class OversizedFileError(DocumentAnalysisError):
    """Raised when file size exceeds 10 MB limit."""

    def __init__(self, size_bytes: int):
        message = (
            f"File size ({size_bytes / (1024 * 1024):.2f} MB) exceeds "
            f"the maximum allowed limit of 10 MB."
        )
        super().__init__(
            code="PAYLOAD_TOO_LARGE",
            message=message,
            status_code=413,
        )


class InvalidFileTypeError(DocumentAnalysisError):
    """Raised when file extension, MIME type, or magic bytes are invalid."""

    def __init__(self, detail: str):
        super().__init__(
            code="INVALID_FILE_TYPE",
            message=f"Unsupported file format. Only PDF, JPG, and PNG are accepted. {detail}",
            status_code=400,
        )


def validate_file_upload(
    content: bytes, filename: str, content_type: Optional[str] = None
) -> str:
    """Validate upload size, file extension, MIME type, and magic bytes.

    Returns:
        Normalized file category: 'pdf', 'jpeg', or 'png'.
    """
    if len(content) == 0:
        raise DocumentAnalysisError(
            code="EMPTY_FILE",
            message="Uploaded file is empty (0 bytes).",
            status_code=400,
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise OversizedFileError(len(content))

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"Received extension '{ext}'. Only .pdf, .jpg, .jpeg, and .png are permitted."
        )

    if content_type:
        clean_mime = content_type.lower().split(";")[0].strip()
        if clean_mime not in ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(
                f"Received MIME type '{clean_mime}'. Expected application/pdf, image/jpeg, or image/png."
            )

    # Magic byte check
    if content.startswith(MAGIC_BYTES["pdf"]):
        norm_type = "pdf"
    elif content.startswith(MAGIC_BYTES["jpeg"]):
        norm_type = "jpeg"
    elif content.startswith(MAGIC_BYTES["png"]):
        norm_type = "png"
    else:
        raise InvalidFileTypeError(
            "File header does not match expected PDF, JPG, or PNG magic byte signature."
        )

    # Cross-verify extension with detected magic byte type
    if norm_type == "pdf" and ext != ".pdf":
        raise InvalidFileTypeError("File has PDF content but non-PDF extension.")
    if norm_type == "jpeg" and ext not in (".jpg", ".jpeg"):
        raise InvalidFileTypeError("File has JPEG content but non-JPEG extension.")
    if norm_type == "png" and ext != ".png":
        raise InvalidFileTypeError("File has PNG content but non-PNG extension.")

    return norm_type


def analyze_document_content(
    content: bytes,
    filename: str,
    content_type: Optional[str] = None,
    document_type_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform complete document analysis in memory.

    Parameters:
        content: Binary content of uploaded file.
        filename: Name of the uploaded file.
        content_type: MIME type reported in request header.
        document_type_hint: Optional hint provided by citizen/client.

    Returns:
        Dictionary conforming to API contract:
        {
            "document_type": str,
            "extracted_fields": Dict[str, Any],
            "checklist_status": str,
            "missing_fields": List[str],
            "warnings": List[str]
        }
    """
    # 1. Validate file
    file_type = validate_file_upload(content, filename, content_type)

    # 2. Extract text in-memory
    warnings: List[str] = []
    # Always include the disclaimer warning
    warnings.append(DISCLAIMER_WARNING)

    extracted_text = ""
    extraction_warnings: List[str] = []

    if file_type == "pdf":
        extracted_text, extraction_warnings = extract_text_from_pdf(content)
    else:
        extracted_text, extraction_warnings = extract_text_from_image(content, filename)

    warnings.extend(extraction_warnings)

    # 3. Detect document type
    doc_type = detect_document_type(extracted_text, user_hint=document_type_hint)

    # 4. Extract fields from text
    extracted_fields = parse_fields_from_text(extracted_text, doc_type)

    # 5. Determine checklist status and missing fields
    checklist_status, missing_fields = evaluate_checklist(doc_type, extracted_fields)

    # If document has no text or OCR is unavailable, force status to unverified_or_incomplete
    if not extracted_text.strip() or not extracted_fields:
        checklist_status = "unverified_or_incomplete"
        if not any("scanned" in w.lower() or "ocr" in w.lower() for w in warnings):
            warnings.append(
                "Unable to extract readable text. The document may be blank, scanned, or encrypted."
            )

    return {
        "document_type": doc_type,
        "extracted_fields": extracted_fields,
        "checklist_status": checklist_status,
        "missing_fields": missing_fields,
        "warnings": warnings,
    }
