"""Document Text Extractor.

Supports extracting text from PDF, JPG, and PNG files in memory without saving
sensitive citizen documents to persistent disk storage.

Key principles:
- Uses pypdf as the sole supported method for PDF extraction
- Safe resource bounds: enforces maximum PDF page count (20) and text length (100,000 chars)
- No custom unbounded stream decompression
- Visual-only image handling: does NOT treat PNG metadata as document text
- Explicit fallback warning when OCR or embedded text is unavailable
"""

import io
import os
import logging
from typing import Tuple, List, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Safe extraction limits
MAX_PDF_PAGES = 20
MAX_EXTRACTED_TEXT_LENGTH = 100_000
MAX_IMAGE_DIMENSION = 3000


def _get_tessdata_path() -> Optional[str]:
    """Locate local tessdata directory with eng.traineddata and tel.traineddata."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    td_path = os.path.join(base_dir, "tessdata")
    if os.path.exists(os.path.join(td_path, "eng.traineddata")):
        return td_path
    return None


def extract_text_from_pdf(content: bytes) -> Tuple[str, List[str]]:
    """Extract text from PDF binary content with safe resource limits.

    Prefers PyMuPDF (fitz) for superior structural layout and whitespace handling,
    falling back to pypdf when PyMuPDF is unavailable.

    Enforces:
    - Maximum page processing limit (MAX_PDF_PAGES = 20)
    - Maximum extracted text length (MAX_EXTRACTED_TEXT_LENGTH = 100,000 characters)

    Returns:
        (extracted_text, warnings_list)
        If unreadable, scanned, or unsupported, returns ("", [warning]) honestly.
    """
    warnings: List[str] = []

    # 1. Attempt PyMuPDF (fitz) first
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            warnings.append("The uploaded PDF document contains 0 pages.")
            return "", warnings

        if total_pages > MAX_PDF_PAGES:
            warnings.append(
                f"PDF exceeds the maximum allowed limit of {MAX_PDF_PAGES} pages (found {total_pages}). "
                f"Only the first {MAX_PDF_PAGES} pages were processed."
            )

        pages_text: List[str] = []
        total_chars = 0
        pages_to_process = min(total_pages, MAX_PDF_PAGES)

        for i in range(pages_to_process):
            page = doc[i]
            txt = page.get_text() or ""
            txt_clean = txt.strip()
            if txt_clean:
                if total_chars + len(txt_clean) > MAX_EXTRACTED_TEXT_LENGTH:
                    allowed = MAX_EXTRACTED_TEXT_LENGTH - total_chars
                    pages_text.append(txt_clean[:allowed])
                    warnings.append(
                        f"Extracted document text exceeded the maximum size limit of "
                        f"{MAX_EXTRACTED_TEXT_LENGTH} characters and was truncated."
                    )
                    break
                pages_text.append(txt_clean)
                total_chars += len(txt_clean)

        combined_text = "\n".join(pages_text).strip()
        if combined_text:
            return combined_text, warnings

        # If combined digital text is empty in PyMuPDF, attempt OCR on scanned PDF pages
        td = _get_tessdata_path()
        if td:
            try:
                ocr_pages = []
                pages_to_ocr = min(total_pages, 5)
                for i in range(pages_to_ocr):
                    page = doc[i]
                    tp = page.get_textpage_ocr(language="eng+tel", tessdata=td, dpi=150)
                    page_txt = page.get_text(textpage=tp) or ""
                    if page_txt.strip():
                        ocr_pages.append(page_txt.strip())
                ocr_combined = "\n".join(ocr_pages).strip()
                if ocr_combined:
                    warnings.append(
                        "Document text extracted via Optical Character Recognition (OCR) for scanned PDF. "
                        "Please verify critical details against the original physical certificate."
                    )
                    return ocr_combined, warnings
            except Exception as e:
                logger.debug("Scanned PDF embedded OCR failed: %s; falling back to pypdf", str(e))
    except Exception as e:
        logger.debug("PyMuPDF extraction unavailable or failed: %s; falling back to pypdf", str(e))

    # 2. Fallback to pypdf
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(io.BytesIO(content))
        total_pages = len(reader.pages)

        if total_pages == 0:
            warnings.append("The uploaded PDF document contains 0 pages.")
            return "", warnings

        if total_pages > MAX_PDF_PAGES and not any("maximum allowed limit" in w for w in warnings):
            warnings.append(
                f"PDF exceeds the maximum allowed limit of {MAX_PDF_PAGES} pages (found {total_pages}). "
                f"Only the first {MAX_PDF_PAGES} pages were processed."
            )

        pages_to_process = reader.pages[:MAX_PDF_PAGES]
        pages_text = []
        total_chars = 0

        for page in pages_to_process:
            txt = page.extract_text() or ""
            txt_clean = txt.strip()
            if txt_clean:
                if total_chars + len(txt_clean) > MAX_EXTRACTED_TEXT_LENGTH:
                    allowed = MAX_EXTRACTED_TEXT_LENGTH - total_chars
                    pages_text.append(txt_clean[:allowed])
                    if not any("exceeded the maximum size limit" in w for w in warnings):
                        warnings.append(
                            f"Extracted document text exceeded the maximum size limit of "
                            f"{MAX_EXTRACTED_TEXT_LENGTH} characters and was truncated."
                        )
                    break
                pages_text.append(txt_clean)
                total_chars += len(txt_clean)

        combined_text = "\n".join(pages_text).strip()

        if not combined_text:
            warnings.append(
                "The document appears to be a scanned or image-based PDF without an embedded text layer, "
                "or the PDF format is unsupported. Optical Character Recognition (OCR) or manual physical verification is required."
            )
            return "", warnings

        return combined_text, warnings

    except Exception as e:
        logger.warning("PDF parsing failed: %s", str(e))
        warnings.append(
            "Failed to parse PDF document structure. The file may be encrypted, corrupted, or unsupported. "
            "Manual physical verification is required."
        )
        return "", warnings


def extract_text_from_image(content: bytes, filename: str = "") -> Tuple[str, List[str]]:
    """Inspect and extract text from JPG/PNG/WebP image content in memory.

    Uses embedded PyMuPDF OCR (with English and Telugu tessdata) and Pillow normalization.
    Strictly visual: does NOT treat image metadata chunks as document text.
    If OCR is unavailable or image is unreadable, returns empty text with an explicit warning.

    Returns:
        (extracted_text, warnings_list)
    """
    warnings: List[str] = []

    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
        # Re-open after verify()
        img = Image.open(io.BytesIO(content))
    except Exception as e:
        warnings.append(f"Image validation failed: {str(e)}. File may be corrupted.")
        return "", warnings

    # Normalize image mode to RGB and enforce safe dimension bound
    try:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
    except Exception as e:
        warnings.append(f"Image preprocessing warning: {str(e)}")

    ocr_text = ""
    td = _get_tessdata_path()

    # 1. Attempt PyMuPDF embedded OCR (self-contained, no external tesseract.exe needed)
    if td:
        try:
            import pymupdf
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            pdf_doc = pymupdf.open()
            pdf_page = pdf_doc.new_page(width=img.width, height=img.height)
            pdf_page.insert_image(pymupdf.Rect(0, 0, img.width, img.height), stream=png_bytes)
            tp = pdf_page.get_textpage_ocr(language="eng+tel", tessdata=td, dpi=150)
            ocr_text = pdf_page.get_text(textpage=tp).strip()
        except Exception as e:
            logger.debug("PyMuPDF embedded OCR failed: %s; trying pytesseract fallback", str(e))

    # 2. Fallback to pytesseract if installed and embedded OCR produced nothing
    if not ocr_text:
        try:
            import pytesseract  # type: ignore
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception:
            pass

    if ocr_text:
        warnings.append(
            "Document text extracted via Optical Character Recognition (OCR). "
            "Please verify critical details against the original physical certificate."
        )
        return ocr_text, warnings

    warnings.append(
        "Optical Character Recognition (OCR) is unavailable or could not detect machine-readable text in this image. "
        "Manual physical verification is required."
    )
    return "", warnings
