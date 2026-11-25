# Member 4 — Implementation Documentation

**Project:** AI Grama Sahayak
**Event:** HackWithAditya 2026
**Member:** Rakshitha Kothala (Member 4)
**Branch:** `dev/member-4-doc-services`
**Git Author Name:** Rakshitha Kothala
**Git Author Email:** `radhakrishnakothala89-cloud` (see [Section 10](#10-git-author-email-configuration-issue))

---

## Table of Contents

1. [Member Name and Responsibilities](#1-member-name-and-responsibilities)
2. [Implemented Modules and Source File Paths](#2-implemented-modules-and-source-file-paths)
3. [Document Analysis Workflow](#3-document-analysis-workflow)
4. [Nearby-Services Architecture and Limitations](#4-nearby-services-architecture-and-limitations)
5. [Grievance Drafting Implementation](#5-grievance-drafting-implementation)
6. [Database Failure Isolation](#6-database-failure-isolation)
7. [Testing and Validation](#7-testing-and-validation)
8. [Original Commit References](#8-original-commit-references)
9. [Known Limitations](#9-known-limitations)
10. [Git Author Email Configuration Issue](#10-git-author-email-configuration-issue)

---

## 1. Member Name and Responsibilities

**Name:** Rakshitha Kothala
**Role:** Member 4 — Document Analysis, Nearby Services, and Grievance Drafting

**Responsibilities:**

- Design and implement the document analysis pipeline (upload validation, text extraction, field parsing, checklist evaluation).
- Build the nearby-services discovery module with a verified Andhra Pradesh government health facilities dataset.
- Implement the bilingual grievance drafting service (English and Telugu) with citizen safety guardrails.
- Create corresponding FastAPI route handlers for each module.
- Write unit and integration tests for all three service modules plus an API endpoint test harness.
- Provide synthetic test documents for the document analysis pipeline.
- Fix the root API test harness import-order issue to ensure tests could run from the project root.
- Implement database failure isolation for the eligibility audit subsystem to prevent database unavailability from blocking citizen requests.
- Expand document detection coverage and the nearby-services facility dataset in a follow-up commit.

---

## 2. Implemented Modules and Source File Paths

### Service Modules (Backend)

| Module | Source File |
|---|---|
| Document Analyzer (orchestrator) | [`backend/app/services/documents/analyzer.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/documents/analyzer.py) |
| Document Text Extractor | [`backend/app/services/documents/extractor.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/documents/extractor.py) |
| Document Field Parser | [`backend/app/services/documents/field_parser.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/documents/field_parser.py) |
| Documents Package Init | [`backend/app/services/documents/__init__.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/documents/__init__.py) |
| Grievance Drafter | [`backend/app/services/grievances/drafter.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/grievances/drafter.py) |
| Grievances Package Init | [`backend/app/services/grievances/__init__.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/grievances/__init__.py) |
| AP Services Dataset (models) | [`backend/app/services/locations/models.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/locations/models.py) |
| Nearby Service Finder | [`backend/app/services/locations/service_finder.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/locations/service_finder.py) |
| Locations Package Init | [`backend/app/services/locations/__init__.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/services/locations/__init__.py) |

### API Routes

| Endpoint | Source File |
|---|---|
| `POST /api/documents/analyze` | [`backend/app/api/documents.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/api/documents.py) |
| `POST /api/grievances/draft` | [`backend/app/api/grievances.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/api/grievances.py) |
| `GET /api/services/nearby` | [`backend/app/api/services.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/api/services.py) |

### Database Failure Isolation (Cross-Module)

| File | Nature of Change |
|---|---|
| [`backend/app/api/eligibility.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/api/eligibility.py) | Modified — added database status checks, background task dispatch, rollback/close handling |
| [`backend/app/core/config.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/core/config.py) | Modified — added `DATABASE_ENABLED` and `DATABASE_AUDIT_ENABLED` settings |
| [`backend/app/database/session.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/app/database/session.py) | Modified — added `DatabaseStatus` enum, `get_database_status()`, cooldown/circuit-breaker logic, `record_db_failure()`, `record_db_success()` |

### Tests

| Test Suite | Source File |
|---|---|
| Document Analysis Tests | [`tests/test_documents.py`](file:///c:/Users/radha/ai-grama-sahayak/tests/test_documents.py) |
| Grievance Drafting Tests | [`tests/test_grievances.py`](file:///c:/Users/radha/ai-grama-sahayak/tests/test_grievances.py) |
| Nearby Services Tests | [`tests/test_services.py`](file:///c:/Users/radha/ai-grama-sahayak/tests/test_services.py) |
| API Endpoint Test Harness | [`tests/test_api_endpoints.py`](file:///c:/Users/radha/ai-grama-sahayak/tests/test_api_endpoints.py) |
| Test Package Init (shims) | [`tests/__init__.py`](file:///c:/Users/radha/ai-grama-sahayak/tests/__init__.py) |
| Eligibility Audit Perf Tests | [`backend/tests/test_eligibility_audit_performance.py`](file:///c:/Users/radha/ai-grama-sahayak/backend/tests/test_eligibility_audit_performance.py) |

### Synthetic Test Data

| File | Description |
|---|---|
| [`document_samples/README.md`](file:///c:/Users/radha/ai-grama-sahayak/document_samples/README.md) | Description of synthetic samples |
| [`document_samples/generate_samples.py`](file:///c:/Users/radha/ai-grama-sahayak/document_samples/generate_samples.py) | Script to generate synthetic PDF/PNG test documents |
| `document_samples/synthetic_income_certificate.pdf` | Synthetic income certificate (digital PDF) |
| `document_samples/synthetic_caste_certificate.pdf` | Synthetic caste certificate (digital PDF) |
| `document_samples/synthetic_ration_card.pdf` | Synthetic ration card (digital PDF) |
| `document_samples/synthetic_income_cert.png` | Synthetic income certificate (image) |
| `document_samples/synthetic_blank.png` | Blank image for edge-case testing |
| `document_samples/synthetic_scanned_unreadable.pdf` | Scanned/unreadable PDF for OCR fallback testing |
| `document_samples/synthetic_invalid.txt` | Invalid file type for rejection testing |

---

## 3. Document Analysis Workflow

The document analysis pipeline is implemented across three modules, orchestrated by `analyzer.py`.

### 3.1 Upload Validation (`analyzer.py` → `validate_file_upload()`)

The validation sequence performs four checks in order:

1. **Empty file check** — rejects 0-byte uploads with `EMPTY_FILE` error.
2. **Size limit** — enforces a 10 MB maximum (`MAX_UPLOAD_BYTES`). Raises `OversizedFileError` (HTTP 413).
3. **Extension check** — allows only `.pdf`, `.jpg`, `.jpeg`, `.png`.
4. **MIME type check** — validates the `Content-Type` header against an allowlist.
5. **Magic byte verification** — reads the first bytes of the file and matches against known signatures (`%PDF-`, `\xff\xd8\xff` for JPEG, `\x89PNG\r\n\x1a\n` for PNG). Cross-verifies that the detected type matches the file extension.

Returns a normalized file category: `"pdf"`, `"jpeg"`, or `"png"`.

### 3.2 Text Extraction (`extractor.py`)

Two extraction paths based on file category:

- **PDF** (`extract_text_from_pdf()`):
  - Originally used `pypdf` as the sole PDF reader.
  - Commit `4e49293` added PyMuPDF (`fitz`) as the preferred extractor with pypdf as fallback.
  - Enforces `MAX_PDF_PAGES = 20` and `MAX_EXTRACTED_TEXT_LENGTH = 100,000` characters.
  - Returns empty text with an honest warning for scanned/image-only PDFs.

- **Image** (`extract_text_from_image()`):
  - Validates image integrity via `PIL.Image.verify()`.
  - Attempts OCR via `pytesseract` if available.
  - Returns empty text with an explicit warning if OCR is unavailable — does **not** treat PNG metadata as document text.

All extraction is performed in-memory without writing citizen documents to disk.

### 3.3 Field Parsing (`field_parser.py`)

#### Document Type Detection (`detect_document_type()`)

Identifies the document type using a two-tier strategy:

1. **User hint** — if the caller provides a `document_type_hint`, it is normalized and matched against known types (with synonym resolution for terms like "community" → `caste_certificate`, "rice" → `ration_card`).
2. **Text keyword matching** — falls back to searching the extracted text for characteristic phrases (e.g., "income certificate", "annual income" → `income_certificate`).

Supported document types: `income_certificate`, `caste_certificate`, `ration_card`, `rice_card`, `patta_passbook`, `aadhaar_card`, `general_document`.

#### Field Extraction (`parse_fields_from_text()`)

Extracts structured fields per document type using regex patterns:

| Document Type | Fields Extracted |
|---|---|
| `income_certificate` | `certificate_number`, `applicant_name`, `annual_income`, `issue_date`, `district` |
| `caste_certificate` | `certificate_number`, `applicant_name`, `caste_category`, `issue_date`, `district` |
| `ration_card` / `rice_card` | `ration_card_number`, `head_of_family`, `district` |
| `patta_passbook` | `khata_number`, `pattadar_name`, `survey_number`, `district` |
| `aadhaar_card` | `aadhaar_number` (masked: `XXXX-XXXX-nnnn`), `name`, `year_of_birth_or_dob` |
| `general_document` | `document_number`, `name`, `date` |

District detection matches against a full list of 26 current Andhra Pradesh districts.

**Privacy safeguard:** Aadhaar numbers are masked on extraction, exposing only the last 4 digits.

#### Checklist Evaluation (`evaluate_checklist()`)

Compares extracted fields against per-type required-field checklists (`DOCUMENT_CHECKLISTS`). Returns:

- `"complete"` — all required fields present.
- `"partially_complete"` — some but not all required fields present.
- `"unverified_or_incomplete"` — no required fields present, or no text extracted.

### 3.4 API Route (`documents.py`)

`POST /api/documents/analyze` accepts a multipart file upload with an optional `document_type` form field. The route handler:

1. Validates the upload exists and has a filename.
2. Reads the file stream in chunks via `read_upload_stream()` with on-the-fly size enforcement (aborts immediately if the stream exceeds 10 MB without buffering the entire oversized file).
3. Delegates to `analyze_document_content()`.
4. Returns the response conforming to the `DocumentAnalysisResponse` schema.

Every response includes a disclaimer warning: *"Extracted data is provisional and not automatically verified. Please verify with the original document."*

### 3.5 Subsequent Improvements (Not by Member 4)

Commit `b1e4c02` (by Virapaneni Anandkumar / Member 1, integration phase) modified `field_parser.py` to adjust regex boundaries and schema enum compatibility across modules.

---

## 4. Nearby-Services Architecture and Limitations

### 4.1 Data Model (`models.py`)

The service dataset is a static Python list (`VERIFIED_AP_SERVICES`) of verified Andhra Pradesh government health facilities. Each record includes:

- Facility `name`, `id`, `service_type` (`"hospital"` or `"community_health_centre"`).
- `district`, `mandal`, `address`.
- `phone` — from official DME directory pages (set to `None` where not published).
- `latitude`, `longitude` — **approximate city-level** coordinates, not surveyed GPS pins.
- `source_url`, `publisher`, `verified_at` — provenance fields referencing official AP `.gov.in` / `.nic.in` pages.
- `evidence` — per-record audit trail explaining the source.

**Initial dataset (commit `df06b4c`):** 10 facilities — 6 DME Government General/Teaching Hospitals and 4 APVVP District/Area/CHC Hospitals.

**Expanded dataset (commit `4e49293`):** Added 5 more facilities (Area Hospitals in Palnadu, Prakasam, Guntur, Krishna districts plus a CHC in Mangalagiri), bringing the total to 15.

A `haversine_distance_km()` function provides approximate radial distance calculations.

Quarantined records (facilities lacking directory substantiation) are explicitly separated and excluded from query results.

### 4.2 Service Finder (`service_finder.py`)

`find_nearby_services()` accepts optional filters:

- `service_type` — filters by facility type. Aliases `"healthcare"` matches both `"hospital"` and `"community_health_centre"`. Commit `4e49293` added additional aliases: `"health"`, `"phc"`, `"hospital_or_phc"`.
- `district` — case-insensitive district name matching (substring supported).
- `latitude` / `longitude` / `radius_km` — Haversine radial search within the specified radius (default 50 km).

Requires at least one of `district` or coordinates. Input validation covers coordinate ranges, radius positivity, and paired lat/lon.

Results are sorted by ascending distance when coordinates are provided.

**Commit `4e49293` integration improvement:** Imported `normalize_district()` and `AP_DISTRICT_SYNONYMS` from `field_parser.py` to support canonical district matching and Telugu-script district name lookups.

### 4.3 API Route (`services.py`)

`GET /api/services/nearby` with query parameters: `service_type`, `district`, `latitude`, `longitude`, `radius_km`. Returns `{"services": [...]}` conforming to `NearbyServicesResponse`.

### 4.4 Limitations

- **Health facilities only** — the dataset covers only hospitals and community health centres. No schools, post offices, or other public service types.
- **Static dataset** — facility data is hardcoded in Python; not dynamically fetched from an external API or database.
- **Approximate coordinates** — all GPS positions are city/locality-level centers, not surveyed building locations. Distance values are approximate radial estimates, not road distances.
- **Phone numbers not call-verified** — DME directory phone numbers are reproduced from official pages but have not been independently call-verified. APVVP facility phones are `None` where not published.
- **15 facilities** — coverage is limited to a small subset of AP's public health infrastructure.

---

## 5. Grievance Drafting Implementation

### 5.1 Drafter Module (`drafter.py`)

`draft_grievance()` generates a formal, respectful complaint letter for citizens in either English (`"en"`) or Telugu (`"te"`).

**Parameters:** `category`, `description`, `district`, `mandal`, `language`.

**Supported categories** (10): `water_supply`, `electricity`, `roads`, `sanitation`, `ration`, `pension`, `revenue`, `agriculture`, `health`, `education`. Each has bilingual labels (English and Telugu). Unknown categories fall back to a generic title.

**Output structure:**

```json
{
  "subject": "...",
  "complaint_body": "...",
  "recommended_next_steps": ["..."],
  "official_links": [{"title": "...", "url": "...", "publisher": "...", "verified_at": "..."}]
}
```

### 5.2 Citizen Safety Guardrails

The drafter enforces strict guardrails:

1. **Never claims submission** — the complaint body explicitly addresses it to the appropriate authority but the next steps always state the draft has "NOT been submitted automatically to any government office" (English) / "ఏ ప్రభుత్వ కార్యాలయానికీ స్వయంచాలకంగా సమర్పించబడలేదు" (Telugu).
2. **Never claims tracking** — no fabricated complaint/tracking numbers are generated.
3. **Official links only** — provides 3 verified AP government portal links (Spandana, Grama/Ward Sachivalayam, Meeseva) as submission guidance.
4. **Bilingual guidance** — Telugu next steps advise submission via Spandana, toll-free 1902, or in-person at the local Sachivalayam/Collectorate.

### 5.3 Input Validation

Raises `ValueError` for:
- Empty/blank `category`, `description`, `district`, or `mandal`.
- Unsupported `language` (only `"en"` and `"te"` accepted).

### 5.4 API Route (`grievances.py`)

`POST /api/grievances/draft` accepts a JSON body with `category`, `description`, `district`, `mandal`, and optional `language` (default `"en"`). Returns the draft conforming to `GrievanceDraftResponse`.

---

## 6. Database Failure Isolation

Commit `dd88ea9` addressed a latency and reliability problem in the eligibility check endpoint. The original implementation (by Member 1) persisted audit logs synchronously during each eligibility request. When the PostgreSQL database was unavailable or slow, this blocked the citizen's eligibility response.

### 6.1 Changes to `eligibility.py`

- Added a **pre-flight database status check** (`get_database_status(timeout=0.3)`) before attempting audit persistence. If the database is not `AVAILABLE_OPERATIONAL`, audit logging is skipped immediately with a debug log.
- Added a **`DATABASE_AUDIT_ENABLED` settings check** — if explicitly set to `False`, audit logging is skipped without touching the database at all.
- Changed audit persistence from a context-manager session to explicit `session` / `try` / `except` / `finally` with `rollback()` and `close()` on failure.
- Dispatched audit logging as a **`BackgroundTasks`** task to avoid blocking the async event loop.
- Called `record_db_failure()` on any database exception to initiate cooldown.
- Sanitized error logging to expose only the exception type name, not credentials or applicant PII.

### 6.2 Changes to `config.py`

Added two new `Settings` fields:

- `DATABASE_ENABLED: bool` (default `True`) — explicit toggle for the database connection globally.
- `DATABASE_AUDIT_ENABLED: bool` (default `True`) — toggle specifically for eligibility audit logging.

### 6.3 Changes to `session.py`

- Added `DatabaseStatus` enum: `AVAILABLE_OPERATIONAL`, `DISABLED`, `UNCONFIGURED`, `COOLDOWN`, `UNREACHABLE`.
- Implemented `get_database_status(timeout)` — performs a lightweight probe (`SELECT 1`) with a configurable timeout. Uses a cooldown cache to avoid repeated probe attempts when the database is known to be down.
- Added `record_db_failure()` and `record_db_success()` to manage the cooldown state.
- Added `is_database_explicitly_disabled()` for use by other modules.
- Added `reset_db_state_cache()` for test reset.

### 6.4 Design Principle

The core eligibility evaluation (rule engine) has **zero database dependency**. The database is used solely for optional audit logging. Member 4's changes ensure that:

- A citizen's eligibility response is never delayed or blocked by database issues.
- Repeated requests while the database is down skip the probe immediately (cooldown circuit-breaker).
- The eligibility response schema and content are identical whether audit logging succeeds, fails, or is disabled.

---

## 7. Testing and Validation

### 7.1 Test Suites Created (Commit `df06b4c`)

**`tests/test_documents.py`** (298 lines) — Unit tests for the document analysis pipeline:
- File validation (size limits, extension checks, MIME type checks, magic byte verification).
- PDF text extraction with pypdf (including page limits, text truncation).
- Image extraction paths (OCR available/unavailable).
- Document type detection (keyword matching and user hints).
- Field parsing for income certificates, caste certificates, ration cards, patta passbooks, Aadhaar cards.
- Checklist evaluation (complete, partially complete, unverified).
- Edge cases: empty files, corrupt files, scanned PDFs.

**`tests/test_grievances.py`** (179 lines) — Unit tests for grievance drafting:
- English and Telugu draft generation.
- Guardrail assertions (no false submission claims, no tracking claims).
- Official links conformance (`.gov.in` URLs, Common Source Object schema).
- Input validation (empty fields, unsupported language).
- Tone checks (respectful address, formal closing).

**`tests/test_services.py`** (162 lines) — Unit tests for nearby-services:
- District-based search (Kakinada, Guntur, Visakhapatnam).
- Coordinate-based Haversine search with radius filtering.
- Service type filtering (including `"healthcare"` alias).
- Verified dataset integrity (10 facilities, source URLs, evidence fields).
- Input validation (missing parameters, invalid coordinates, negative radius).
- Empty result honesty (no fabricated records).

**`tests/test_api_endpoints.py`** (286 lines) — Integration tests for all three API routes:
- Document upload endpoint (valid PDF, oversized file, invalid type, empty file).
- Grievance draft endpoint (English/Telugu, missing fields).
- Nearby services endpoint (district search, coordinate search, validation errors).

**`tests/__init__.py`** (208 lines) — Test package initialization providing:
- `sys.path` configuration for running tests from the project root.
- Shims and mocks for dependencies not available in the test environment.

### 7.2 Tests Added in Follow-Up Commits

**Commit `9c758a6`** — Fixed import order in `tests/test_api_endpoints.py`:
- Ensured the root `tests` package (and its shims) is imported before `backend/` modules.
- Added `sys.path` deduplication guards to prevent path pollution.

**Commit `dd88ea9`** — Added `backend/tests/test_eligibility_audit_performance.py` (232 lines):
- 7 test scenarios for database failure isolation:
  1. Eligibility works with database completely disabled.
  2. Eligibility works with database unconfigured (`DATABASE_URL=None`).
  3. Eligibility works when database connection times out.
  4. Audit logging succeeds when database is available.
  5. Audit logging failure handled gracefully (rollback, close, no unhandled exception).
  6. Repeated requests under database unavailability stay fast (cooldown circuit-breaker, <100ms average for subsequent requests).
  7. Response integrity — identical schema output whether audit succeeds, fails, or is disabled.
- Tests assert that `DATABASE_AUDIT_ENABLED=False` disables audit without disabling the global database.

**Commit `4e49293`** — Expanded test coverage:
- Added 10 document acceptance test cases to `tests/test_documents.py` (193 additional lines):
  1. Digital income certificate PDF — auto-detection and field extraction.
  2. Scanned income certificate PDF — honest unverified status.
  3. User-hinted caste certificate.
  4. Ration card with head-of-family extraction.
  5. Income certificate PNG with OCR unavailable.
  6. Auto-detect user hint for digital PDF.
  7. Valid upload that is not a known AP document type.
  8. Explicit Aadhaar hint with privacy masking.
  9. Unrelated document — does not force incorrect category.
  10. Empty/invalid file — rejected with proper error code.

- Added service tests to `tests/test_services.py` (33 additional lines):
  - Palnadu district search with spelling variants and Telugu script.
  - Guntur and Krishna expanded coverage assertions.
  - `"education"` service type returns honest empty results.
  - GPS coordinate search near Narasaraopet with distance sorting.
- Updated verified dataset count from 10 to 15.

---

## 8. Original Commit References

All commits authored by **Rakshitha Kothala** (`radhakrishnakothala89-cloud`).

Repository: `https://github.com/anandkumarpv123-007/ai-grama-sahayak`

| Commit | Date | Description | Link |
|---|---|---|---|
| `df06b4c` | 2026-11-22 16:51 IST | feat(member-4): implement document analysis, nearby services and grievance drafting | [View commit](https://github.com/anandkumarpv123-007/ai-grama-sahayak/commit/df06b4c600c253b1a454b598448fecefc8494c10) |
| `9c758a6` | 2026-11-23 23:30 IST | test: fix root API harness import order | [View commit](https://github.com/anandkumarpv123-007/ai-grama-sahayak/commit/9c758a6e4ad85f0e89228ebee7e1b87c09210076) |
| `dd88ea9` | 2026-11-24 12:53 IST | fix(eligibility): prevent optional database audit latency and isolate failures | [View commit](https://github.com/anandkumarpv123-007/ai-grama-sahayak/commit/dd88ea94e231dc126b54149a0a309c086dea4a4f) |
| `4e49293` | 2026-11-24 23:41 IST | fix(services): improve document detection and citizen service coverage | [View commit](https://github.com/anandkumarpv123-007/ai-grama-sahayak/commit/4e492937d0b3494e57fb2d9f31f312efb3ea774d) |

**Total original contribution:** 26 new files, ~3,143 lines added in `df06b4c`; followed by targeted fixes totaling ~1,186 additional lines across the three follow-up commits.

### Subsequent Integration Work (by Other Members)

The following commits modified Member 4's files but were authored by other team members:

| Commit | Author | Description |
|---|---|---|
| `e15b155` | Virapaneni Anandkumar | Merge of `dev/member-4-doc-services` into `integration/round1` |
| `b1e4c02` | Virapaneni Anandkumar | Integration fix: cross-module schema enums, regex boundaries, test compatibility adjustments in `field_parser.py`, `documents.py`, `grievances.py`, `services.py`, `tests/__init__.py`, `test_api_endpoints.py` |
| `ecb5a88` | Virapaneni Anandkumar | Acceptance fix: citizen discovery, service navigation and document handling improvements |

These integration commits adapted Member 4's modules for cross-member compatibility (schema enums, import paths, regex boundary adjustments) but did not alter the core architectural design or introduce new feature modules.

---

## 9. Known Limitations

### Document Analysis
- **No real OCR in default deployment** — `pytesseract` is an optional dependency. Without it, image-based documents return empty text with a warning.
- **Regex-based field extraction** — relies on pattern matching rather than ML-based NER. Edge cases with unusual formatting, non-standard field labels, or heavily abbreviated text may fail to extract fields.
- **No PDF decryption** — encrypted PDFs fail extraction with an honest error message.
- **No multi-language OCR** — if OCR is available, it defaults to English. Telugu-script documents in image format may not be extractable.
- **26 AP districts only** — district detection is limited to the current 26 Andhra Pradesh districts.

### Nearby Services
- **Health facilities only** — no coverage for schools, post offices, revenue offices, or other public service types.
- **Static dataset of 15 facilities** — does not cover the full breadth of AP's public health infrastructure.
- **Approximate coordinates** — not suitable for precise navigation.
- **No real-time availability** — cannot reflect facility closures, relocations, or staff availability.

### Grievance Drafting
- **Template-based** — generates a fixed-structure formal letter. Cannot adapt to complex, multi-issue grievances.
- **Two languages only** — English and Telugu. No support for Urdu, Hindi, or other languages spoken in AP.
- **No submission integration** — the system generates a draft only; it does not submit to Spandana or any government portal.
- **10 categories** — categories are predefined. Unusual grievance types receive generic formatting.

### Database Failure Isolation
- **Cooldown is in-process** — the circuit-breaker state is per-process (in-memory). It is not shared across multiple worker processes or server instances.
- **Fixed cooldown timeout** — the cooldown period is not dynamically adjusted based on failure patterns.

---

## 10. Git Author Email Configuration Issue

All 10 commits authored by Rakshitha Kothala (across all branches) use the Git author email `radhakrishnakothala89-cloud` — which is **not a valid email address** (it lacks a domain, e.g., `@gmail.com`).

This occurred because Member 4's local Git configuration had `user.email` set to their GitHub username rather than their actual email address. The likely cause was running:

```bash
git config user.email "radhakrishnakothala89-cloud"
```

instead of:

```bash
git config user.email "radhakrishnakothala89-cloud@users.noreply.github.com"
# or
git config user.email "actual-email@example.com"
```

**Impact:**
- GitHub does not link these commits to Member 4's GitHub profile in the contributor graph, since the email does not match any verified email on their GitHub account.
- The commits are still verifiable by author name ("Rakshitha Kothala") and are present in the repository history with their correct content and timestamps.
- Git history has **not** been rewritten to correct this. The original author metadata is preserved as-is.

**Note:** This is a local Git configuration issue only. It does not affect the code content, commit integrity, or the ability to verify authorship through the repository log.

---

> **Review Notice:** This document was generated from source code inspection and Git history analysis. Member 4 (Rakshitha Kothala) must review this document for accuracy, correct any inaccuracies, and understand the technical content before committing it to the repository.
