\# AI Grama Sahayak — API Contracts (Frozen)



\## Frozen Technology Stack

\- \*\*Frontend:\*\* Next.js + TypeScript

\- \*\*Backend:\*\* Python + FastAPI

\- \*\*Database:\*\* PostgreSQL

\- \*\*Communication:\*\* REST + JSON

\- \*\*API Documentation:\*\* FastAPI Swagger

\- \*\*Version Control:\*\* Git + GitHub



\---



\## 1. Overall Architecture



The communication flow is:

1\. Citizen interacts with the Next.js frontend.

2\. Frontend sends requests to FastAPI.

3\. Central agent router identifies the specialist assistant.

4\. Specialist logic retrieves verified information or invokes its relevant service.

5\. Backend returns a structured response with sources and next steps.

6\. Frontend displays the answer in the selected language.



\*Important:\* The four assistants are not four independent chatbots. They are specialist capabilities coordinated by one central backend.



\---



\## 2. API Endpoint List



| Method | Endpoint | Owner |

| :--- | :--- | :--- |

| `GET` | `/api/health` | M1 |

| `POST` | `/api/chat` | M1 |

| `POST` | `/api/eligibility/check` | M1 |

| `POST` | `/api/voice/transcribe` | M3 |

| `POST` | `/api/voice/speak` | M3 |

| `POST` | `/api/documents/analyze` | M4 |

| `GET` | `/api/services/nearby` | M4 |

| `POST` | `/api/grievances/draft` | M4 |



\*Note:\* Member 2 develops an internal retrieval service consumed by Member 1's chat orchestration rather than exposing a separate public endpoint.



\---



\## 3. Shared Data Formats



\### Language Codes

| Language | Code |

| :--- | :--- |

| English | `en` |

| Telugu | `te` |



\*(Hindi is excluded from the initial API contract and will be extended after Telugu and English work reliably.)\*



\### Assistant Identifiers

\- `agriculture`

\- `healthcare`

\- `education`

\- `schemes`



\### Common Source Object

Whenever an answer uses verified information, sources must follow this format:



&#x20;   {

&#x20;     "title": "Official source title",

&#x20;     "url": "https://verified-official-source.gov.in/page",

&#x20;     "publisher": "Government department",

&#x20;     "verified\_at": "2026-11-21"

&#x20;   }



\*(Member 2 must supply actual verified source URLs; the URL above is illustrative.)\*



\### Common Error Response

All backend endpoints should use this structure for errors:



&#x20;   {

&#x20;     "error": {

&#x20;       "code": "VALIDATION\_ERROR",

&#x20;       "message": "The request contains invalid information.",

&#x20;       "details": \[]

&#x20;     }

&#x20;   }



\*\*HTTP Status Codes:\*\*

\- `400`: Invalid requests

\- `404`: Missing resources

\- `413`: Oversized uploads

\- `422`: Validation failures

\- `500`: Unexpected server errors



\---



\## 4. Exact Endpoint Contracts



\### A. Health Check — Member 1

\*\*`GET /api/health`\*\*



\*\*Response:\*\*



&#x20;   {

&#x20;     "status": "healthy",

&#x20;     "service": "ai-grama-sahayak",

&#x20;     "version": "1.0.0"

&#x20;   }



\---



\### B. Main Chat — Member 1

\*\*`POST /api/chat`\*\*



\*\*Request:\*\*



&#x20;   {

&#x20;     "message": "What government schemes are available for farmers?",

&#x20;     "assistant": "agriculture",

&#x20;     "language": "te",

&#x20;     "state": "Andhra Pradesh",

&#x20;     "district": "Kakinada",

&#x20;     "conversation\_id": null

&#x20;   }



\*\*Response:\*\*



&#x20;   {

&#x20;     "conversation\_id": "conv\_123",

&#x20;     "answer": "Here is information about relevant agricultural schemes...",

&#x20;     "assistant": "agriculture",

&#x20;     "language": "te",

&#x20;     "sources": \[

&#x20;       {

&#x20;         "title": "Official scheme information",

&#x20;         "url": "https://verified-source.gov.in",

&#x20;         "publisher": "Government department",

&#x20;         "verified\_at": "2026-11-21"

&#x20;       }

&#x20;     ],

&#x20;     "needs\_follow\_up": false,

&#x20;     "follow\_up\_questions": \[],

&#x20;     "safety\_notice": null

&#x20;   }



\*\*Rules:\*\*

\- `message` is required.

\- `assistant` must be one of the four supported identifiers (`agriculture`, `healthcare`, `education`, `schemes`).

\- `language` must be `en` or `te`.

\- `district` is optional.

\- `conversation\_id` is optional; the backend creates one if absent.

\- Never invent sources.

\- If reliable evidence is unavailable, say so instead of generating an unsupported answer.



\---



\### C. Eligibility Check — Member 1

\*\*`POST /api/eligibility/check`\*\*



\*\*Request:\*\*



&#x20;   {

&#x20;     "scheme\_id": "scheme\_example\_001",

&#x20;     "language": "en",

&#x20;     "applicant\_profile": {

&#x20;       "state": "Andhra Pradesh",

&#x20;       "district": "Kakinada",

&#x20;       "age": 35,

&#x20;       "occupation": "farmer"

&#x20;     }

&#x20;   }



\*\*Response:\*\*



&#x20;   {

&#x20;     "scheme\_id": "scheme\_example\_001",

&#x20;     "status": "needs\_more\_information",

&#x20;     "reasons": \[],

&#x20;     "missing\_fields": \["annual\_income"],

&#x20;     "benefits": \[],

&#x20;     "required\_documents": \[],

&#x20;     "application\_steps": \[],

&#x20;     "sources": \[]

&#x20;   }



\*\*Allowed `status` values:\*\*

\- `eligible`

\- `ineligible`

\- `needs\_more\_information`

\- `unable\_to\_verify`



\*Critical rule:\* Eligibility must be evaluated against documented scheme rules. An LLM must not independently declare a person eligible.



\---



\### D. Voice Transcription — Member 3

\*\*`POST /api/voice/transcribe`\*\*



\*\*Request (`multipart/form-data`):\*\*

| Field | Type |

| :--- | :--- |

| `file` | Audio file |

| `language` | `te` or `en` |



\*\*Response:\*\*



&#x20;   {

&#x20;     "transcribed\_text": "What are the available farming schemes?",

&#x20;     "language": "en",

&#x20;     "confidence": 0.94

&#x20;   }



\---



\### E. Voice Synthesis — Member 3

\*\*`POST /api/voice/speak`\*\*



\*\*Request:\*\*



&#x20;   {

&#x20;     "text": "Here are the available farming schemes.",

&#x20;     "language": "en"

&#x20;   }



\*\*Response:\*\*



&#x20;   {

&#x20;     "audio\_base64": "BASE64\_ENCODED\_AUDIO",

&#x20;     "mime\_type": "audio/mpeg",

&#x20;     "language": "en"

&#x20;   }



\*(The frontend will decode and play the returned audio. Do not put actual audio files or encoded audio into Git commits.)\*



\---



\### F. Document Analysis — Member 4

\*\*`POST /api/documents/analyze`\*\*



\*\*Request (`multipart/form-data`):\*\*

| Field | Type |

| :--- | :--- |

| `file` | PDF, JPG, or PNG |

| `document\_type` | Optional string |



\*\*Response:\*\*



&#x20;   {

&#x20;     "document\_type": "income\_certificate",

&#x20;     "extracted\_fields": {

&#x20;       "certificate\_number": "DEMO123",

&#x20;       "issue\_date": "2026-01-10"

&#x20;     },

&#x20;     "checklist\_status": "partially\_complete",

&#x20;     "missing\_fields": \["annual\_income"],

&#x20;     "warnings": \[]

&#x20;   }



\*\*Rules:\*\*

\- Maximum upload size: 10 MB.

\- Accept only PDF, JPG, and PNG.

\- Treat extracted information as unverified until checked against the original document.

\- Use synthetic sample documents for testing, not real citizens' private documents.



\---



\### G. Nearby Services — Member 4

\*\*`GET /api/services/nearby`\*\*



\*\*Query Parameters:\*\*

\- By district: `/api/services/nearby?service\_type=hospital\&district=Kakinada`

\- By coordinates: `/api/services/nearby?service\_type=hospital\&latitude=16.9891\&longitude=82.2475`



\*\*Response:\*\*



&#x20;   {

&#x20;     "services": \[

&#x20;       {

&#x20;         "name": "Demo Government Hospital",

&#x20;         "service\_type": "hospital",

&#x20;         "address": "Demo address, Kakinada, Andhra Pradesh, India",

&#x20;         "phone": null,

&#x20;         "distance\_km": null,

&#x20;         "source\_url": null

&#x20;       }

&#x20;     ]

&#x20;   }



\*(The example is synthetic and must never be presented as a real hospital. Member 4 must populate the real dataset with verified entries and sources. Latitude and longitude must be supplied together if used.)\*



\---



\### H. Grievance Drafting — Member 4

\*\*`POST /api/grievances/draft`\*\*



\*\*Request:\*\*



&#x20;   {

&#x20;     "category": "water\_supply",

&#x20;     "description": "There has been no water supply in our village for three days.",

&#x20;     "district": "Kakinada",

&#x20;     "mandal": "Example Mandal",

&#x20;     "language": "en"

&#x20;   }



\*\*Response:\*\*



&#x20;   {

&#x20;     "subject": "Request regarding interruption in water supply",

&#x20;     "complaint\_body": "I would like to bring to your attention...",

&#x20;     "recommended\_next\_steps": \[

&#x20;       "Identify the appropriate local authority.",

&#x20;       "Review the official complaint submission procedure."

&#x20;     ],

&#x20;     "official\_links": \[]

&#x20;   }



\*(This endpoint drafts complaints and provides submission guidance. It does not submit complaints to government departments.)\*



\---



\## 5. File Ownership — No Overlapping Development



| Member | Main Ownership |

| :--- | :--- |

| \*\*M1\*\* | `backend/app/api/\*`, `agents/\*`, `schemas/\*`, `core/\*`, `database/\*`, `models/\*` |

| \*\*M2\*\* | `backend/app/services/retrieval/\*`, `knowledge\_base/\*` |

| \*\*M3\*\* | `frontend/\*`, voice service implementation |

| \*\*M4\*\* | `backend/app/services/documents/\*`, `services/locations/\*`, `services/grievances/\*` |



\- Shared interfaces must be reviewed before changing them.

\- Member 2 must not independently change the chat response format.

\- Member 3 must consume the agreed response format rather than inventing a different one.



\---



\## 6. Exact Backend File Ownership



&#x20;   backend/app/

&#x20;   │

&#x20;   ├── main.py                         # M1

&#x20;   │

&#x20;   ├── api/

&#x20;   │   ├── chat.py                     # M1

&#x20;   │   ├── eligibility.py              # M1

&#x20;   │   ├── voice.py                    # M3

&#x20;   │   ├── documents.py                # M4

&#x20;   │   ├── services.py                 # M4

&#x20;   │   └── grievances.py               # M4

&#x20;   │

&#x20;   ├── agents/

&#x20;   │   ├── router.py                   # M1

&#x20;   │   ├── agriculture\_agent.py        # M1

&#x20;   │   ├── healthcare\_agent.py         # M1

&#x20;   │   ├── education\_agent.py          # M1

&#x20;   │   └── schemes\_agent.py            # M1

&#x20;   │

&#x20;   ├── schemas/                        # M1

&#x20;   ├── core/                           # M1

&#x20;   ├── database/                       # M1

&#x20;   ├── models/                         # M1

&#x20;   │

&#x20;   └── services/

&#x20;       ├── retrieval/                  # M2

&#x20;       ├── voice/                      # M3

&#x20;       ├── documents/                  # M4

&#x20;       ├── locations/                  # M4

&#x20;       └── grievances/                 # M4



\- \*\*Member 1\*\* owns `main.py` and registers the routers created by Members 3 and 4. Members 3 and 4 must not independently edit `main.py`.

\- \*\*Member 1\*\* owns shared request/response schemas. Other members must import and use those schemas rather than creating competing versions.



\---



\## 7. API Contract Rules



1\. Never change an agreed endpoint or JSON field name without team approval.

2\. Never return fabricated government sources, hospitals, scheme information, or eligibility results.

3\. Return appropriate HTTP status codes and the agreed error structure.

4\. Validate uploaded files and user inputs.

5\. Use environment variables for API keys and database credentials.

6\. Never commit `.env`, API keys, passwords, or personal documents.

7\. Every feature must have at least basic tests.

8\. Document any incomplete feature honestly.

