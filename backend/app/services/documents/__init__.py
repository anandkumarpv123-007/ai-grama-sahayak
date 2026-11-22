"""Documents service package for AI Grama Sahayak."""

from .analyzer import (
    analyze_document_content,
    validate_file_upload,
    DocumentAnalysisError,
    OversizedFileError,
    InvalidFileTypeError,
    MAX_UPLOAD_BYTES,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    DISCLAIMER_WARNING,
)
from .extractor import extract_text_from_pdf, extract_text_from_image
from .field_parser import (
    detect_document_type,
    parse_fields_from_text,
    evaluate_checklist,
    DOCUMENT_CHECKLISTS,
)

__all__ = [
    "analyze_document_content",
    "validate_file_upload",
    "DocumentAnalysisError",
    "OversizedFileError",
    "InvalidFileTypeError",
    "MAX_UPLOAD_BYTES",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
    "DISCLAIMER_WARNING",
    "extract_text_from_pdf",
    "extract_text_from_image",
    "detect_document_type",
    "parse_fields_from_text",
    "evaluate_checklist",
    "DOCUMENT_CHECKLISTS",
]
