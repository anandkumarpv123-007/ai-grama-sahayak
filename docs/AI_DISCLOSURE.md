# AI Tools and External Dependency Disclosure

In accordance with HackWithAditya 2026 guidelines, this document provides a comprehensive disclosure of AI tools, external services, and third-party models utilized during the development and execution of the AI Grama Sahayak Level 1 prototype.

---

## 1. Development-Time AI Assistance

The engineering team leveraged AI coding and reasoning assistants to accelerate development, improve code quality, and conduct architectural reviews. All generated code was inspected, integrated, tested, and verified by team members.

### 1.1 Antigravity (Google DeepMind)
- **Role:** Agentic software development, automated test orchestration, static analysis remediation, and multi-file code integration.
- **Usage:**
  - Diagnosed and resolved subtle voice streaming audio chunk concatenation bugs.
  - Built regression suites for document analysis, WebP handling, and Telugu OCR verification.
  - Maintained repository hygiene, linting conformity, and cross-platform compatibility across Windows and Linux environments.

### 1.2 ChatGPT (OpenAI)
- **Role:** Architectural brainstorming, design review, API contract refinement, and documentation drafting.
- **Usage:**
  - Assisted in designing the bilingual schema models and RESTful endpoint contracts.
  - Provided structural guidance for the retrieval evaluation benchmark and knowledge base curation.

---

## 2. Runtime AI and External Speech Services

The running prototype interfaces with external cloud services exclusively for Indic speech processing. The core reasoning and knowledge retrieval engines operate independently of external Large Language Models (LLMs).

### 2.1 Sarvam AI
- **Speech-to-Text (STT):**
  - **Model:** `saaras:v4`
  - **Purpose:** Converts spoken citizen voice queries (Telugu and English) into text.
  - **Mode:** Cloud REST API integration via `POST https://api.sarvam.ai/speech-to-text`.
- **Text-to-Speech (TTS):**
  - **Model:** `bulbul:v3`
  - **Speaker Persona:** `kavitha` (Indic voice profile)
  - **Purpose:** Synthesizes Telugu and English text responses into spoken audio for citizens.
  - **Mode:** Cloud REST API integration via `POST https://api.sarvam.ai/text-to-speech`.
- **Graceful Fallback:** If `SARVAM_API_KEY` is not provided, the platform seamlessly degrades to client-side text interaction or browser speech synthesis (`window.speechSynthesis`) where supported. (Note: browser speech synthesis availability and Telugu voice support vary across client browsers, operating systems, and devices).

---

## 3. Bundled Machine Learning & OCR Models

### 3.1 Tesseract OCR Traineddata Models
- **Bundled Files:**
  - `backend/app/services/documents/tessdata/eng.traineddata` (English Fast Model, ~4.11 MB)
  - `backend/app/services/documents/tessdata/tel.traineddata` (Telugu Fast Model, ~2.77 MB)
- **Origin:** Official GitHub repository `tesseract-ocr/tessdata_fast`.
- **License:** Apache License, Version 2.0 (accompanied by full [LICENSE](file:///backend/app/services/documents/tessdata/LICENSE) text and attribution [NOTICE](file:///backend/app/services/documents/tessdata/NOTICE)).
- **Execution:** Executed locally on the server in-memory via PyMuPDF (fitz) embedded OCR bindings. Requires a running backend instance but does not require an external internet connection or cloud OCR API.
- **Resource Limits:** Digital PDF extraction processes up to 20 pages; scanned image-only PDFs run embedded OCR up to the first 5 pages.

---

## 4. Distinction Between Development AI and Runtime Systems

| Component | Technology | Nature | External API Required? |
| :--- | :--- | :--- | :--- |
| **Response Reasoning** | Deterministic Template Synthesizer (reduces unsupported responses) | Internal Rule Engine | **No** (Local logic) |
| **Scheme Retrieval** | Domain-Scoped Text Search (14 curated government knowledge documents) | Internal Ingestion & Matcher | **No** (Local markdown) |
| **Eligibility Assessment**| Deterministic Criteria Engine | Internal Rule Matrix | **No** (Local logic) |
| **Document OCR** | PyMuPDF + Tesseract fast models | Bundled Local Binaries | **No** (Local execution) |
| **Speech-to-Text** | Sarvam AI `saaras:v4` | Cloud Speech API | **Yes** (Optional for voice) |
| **Text-to-Speech** | Sarvam AI `bulbul:v3` | Cloud Speech API | **Yes** (Optional for voice) |
