# Synthetic Document Samples

This directory contains synthetic sample documents created specifically for testing the Document Analysis endpoint (`POST /api/documents/analyze`) of AI Grama Sahayak.

## Privacy & Safety Confirmation
- **Zero Real Citizen Data**: All documents in this folder contain completely fictitious, synthetic data.
- **No Private Credentials**: No real Aadhaar numbers, personal names, or confidential records of any individual are present.
- **Test-Only Assets**: Used strictly for automated test suites and contract verification.

## Sample Files

| Filename | Format | Purpose | Expected Analysis Outcome |
| :--- | :--- | :--- | :--- |
| `synthetic_income_certificate.pdf` | PDF 1.4 | Valid AP Meeseva Income Certificate format | Extracted fields: `certificate_number`, `applicant_name`, `annual_income`, `issue_date`, `district`. Checklist status: `complete`. |
| `synthetic_caste_certificate.pdf` | PDF 1.4 | Valid AP Meeseva Community Certificate format | Extracted fields: `certificate_number`, `applicant_name`, `caste_category`, `issue_date`, `district`, `mandal`. Checklist status: `complete`. |
| `synthetic_ration_card.pdf` | PDF 1.4 | Valid AP Rice Card format | Extracted fields: `ration_card_number`, `head_of_family`, `district`. Checklist status: `complete`. |
| `synthetic_scanned_unreadable.pdf` | PDF 1.4 | Scanned/image-only PDF with no text stream | Checklist status: `unverified_or_incomplete`. Warning: "The document appears to be a scanned or image-based PDF without an embedded text layer." |
| `synthetic_income_cert.png` | PNG | Synthetic image upload | Without an OCR engine configured, returns `unverified_or_incomplete` with an explicit advisory notice that OCR is unavailable and manual verification is required. |
| `synthetic_blank.png` | PNG | Blank image without text | Checklist status: `unverified_or_incomplete`. Warning: "Optical Character Recognition (OCR) is unavailable or could not detect machine-readable text in this image." |
| `synthetic_invalid.txt` | TXT | Unsupported file format | HTTP 400 Bad Request with `INVALID_FILE_TYPE`. |
