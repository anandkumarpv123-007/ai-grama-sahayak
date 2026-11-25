"""Test package configuration for AI Grama Sahayak.

Sets up test harness shims in sys.modules ONLY when external packages
(FastAPI, Pydantic, pypdf, or Member 1's app.schemas) are not installed in the local test runner.
This guarantees that unit and integration tests can execute reliably in isolated environments.
"""

import sys
import types
from typing import Any, Optional, List, Dict

# Ensure backend directory is in sys.path
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _setup_test_shims():
    # 1. Pydantic shim if pydantic is not installed
    if "pydantic" not in sys.modules:
        try:
            import pydantic
        except ImportError:
            pydantic_mod = types.ModuleType("pydantic")
            class BaseModel:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
                def dict(self):
                    return self.__dict__
            def Field(*args, **kwargs):
                return None
            pydantic_mod.BaseModel = BaseModel
            pydantic_mod.Field = Field
            sys.modules["pydantic"] = pydantic_mod

    # 2. FastAPI shim if fastapi is not installed
    if "fastapi" not in sys.modules:
        try:
            import fastapi
        except ImportError:
            fastapi_mod = types.ModuleType("fastapi")
            fastapi_responses = types.ModuleType("fastapi.responses")

            class JSONResponse:
                def __init__(self, content: Any, status_code: int = 200):
                    self.content = content
                    self.status_code = status_code

            class HTTPException(Exception):
                def __init__(self, status_code: int, detail: Any = None):
                    super().__init__(str(detail))
                    self.status_code = status_code
                    self.detail = detail

            class APIRouter:
                def __init__(self, prefix: str = "", tags: Optional[List[str]] = None, *args, **kwargs):
                    self.prefix = prefix
                    self.tags = tags or []
                    self.routes = []

                def post(self, path: str, *args, **kwargs):
                    def decorator(fn):
                        self.routes.append(("POST", self.prefix + path, fn))
                        return fn
                    return decorator

                def get(self, path: str, *args, **kwargs):
                    def decorator(fn):
                        self.routes.append(("GET", self.prefix + path, fn))
                        return fn
                    return decorator

            def File(*args, **kwargs):
                return None

            def Form(*args, **kwargs):
                return None

            def Query(default=None, *args, **kwargs):
                return default

            class UploadFile:
                def __init__(self, filename: str, file: Any, content_type: Optional[str] = None):
                    self.filename = filename
                    self.file = file
                    self.content_type = content_type

                def read(self, size: int = -1) -> bytes:
                    return self.file.read(size)

            class status:
                HTTP_400_BAD_REQUEST = 400
                HTTP_413_REQUEST_ENTITY_TOO_LARGE = 413
                HTTP_422_UNPROCESSABLE_ENTITY = 422
                HTTP_500_INTERNAL_SERVER_ERROR = 500

            fastapi_mod.APIRouter = APIRouter
            fastapi_mod.File = File
            fastapi_mod.Form = Form
            fastapi_mod.Query = Query
            fastapi_mod.UploadFile = UploadFile
            fastapi_mod.HTTPException = HTTPException
            fastapi_mod.status = status
            fastapi_responses.JSONResponse = JSONResponse
            fastapi_mod.responses = fastapi_responses

            sys.modules["fastapi"] = fastapi_mod
            sys.modules["fastapi.responses"] = fastapi_responses

    # 3. Member 1's shared schemas shim if not yet present on branch
    if "app.schemas" not in sys.modules:
        try:
            import app.schemas
        except ImportError:
            schemas_pkg = types.ModuleType("app.schemas")
            doc_schemas = types.ModuleType("app.schemas.documents")
            srv_schemas = types.ModuleType("app.schemas.services")
            grv_schemas = types.ModuleType("app.schemas.grievances")

            from pydantic import BaseModel

            class DocumentAnalysisResponse(BaseModel):
                document_type: str
                extracted_fields: Dict[str, Any]
                checklist_status: str
                missing_fields: List[str]
                warnings: List[str]

            class ServiceItem(BaseModel):
                name: str
                service_type: str
                address: str
                phone: Optional[str] = None
                distance_km: Optional[float] = None
                source_url: Optional[str] = None

            class NearbyServicesResponse(BaseModel):
                services: List[ServiceItem]

            class GrievanceDraftRequest(BaseModel):
                category: str
                description: str
                district: str
                mandal: str
                language: str = "en"

            class GrievanceDraftResponse(BaseModel):
                subject: str
                complaint_body: str
                recommended_next_steps: List[str]
                official_links: List[Dict[str, str]]

            doc_schemas.DocumentAnalysisResponse = DocumentAnalysisResponse
            srv_schemas.ServiceItem = ServiceItem
            srv_schemas.NearbyServicesResponse = NearbyServicesResponse
            grv_schemas.GrievanceDraftRequest = GrievanceDraftRequest
            grv_schemas.GrievanceDraftResponse = GrievanceDraftResponse

            sys.modules["app.schemas"] = schemas_pkg
            sys.modules["app.schemas.documents"] = doc_schemas
            sys.modules["app.schemas.services"] = srv_schemas
            sys.modules["app.schemas.grievances"] = grv_schemas

    # 4. pypdf shim if not installed
    if "pypdf" not in sys.modules:
        try:
            import pypdf
        except ImportError:
            pypdf_mod = types.ModuleType("pypdf")

            class MockPage:
                def __init__(self, text: str = ""):
                    self._text = text

                def extract_text(self) -> str:
                    return self._text

            class MockPdfReader:
                def __init__(self, stream: Any):
                    content = stream.read() if hasattr(stream, "read") else stream
                    self.pages = []
                    # Check for simple text in mock PDFs
                    if b"%PDF-" in content and b"stream" in content:
                        import re
                        streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", content, re.DOTALL)
                        all_lines = []
                        for s in streams:
                            words = re.findall(rb"\((.*?)\)", s)
                            for w in words:
                                if w:
                                    clean_w = w.decode("latin1", errors="replace").replace(r"\(", "(").replace(r"\)", ")")
                                    all_lines.append(clean_w)
                        if all_lines:
                            self.pages.append(MockPage("\n".join(all_lines)))
                        else:
                            # PDF has stream but no text (e.g. scanned image PDF)
                            self.pages.append(MockPage(""))
                    elif b"%PDF-" in content:
                        self.pages.append(MockPage(""))

            pypdf_mod.PdfReader = MockPdfReader
            sys.modules["pypdf"] = pypdf_mod


def _enhance_real_fastapi_for_tests():
    try:
        import json
        from starlette.responses import JSONResponse as _StarletteJSONResponse
        if not hasattr(_StarletteJSONResponse, "content"):
            def _get_content(self):
                if not hasattr(self, "_parsed_content"):
                    try:
                        self._parsed_content = json.loads(self.body.decode("utf-8"))
                    except Exception:
                        self._parsed_content = None
                return self._parsed_content
            _StarletteJSONResponse.content = property(_get_content)
    except ImportError:
        pass

    try:
        from starlette.datastructures import UploadFile as _StarletteUploadFile, Headers
        _orig_upload_init = _StarletteUploadFile.__init__
        def _compat_upload_init(self, file=None, size=None, filename=None, headers=None, content_type=None, **kwargs):
            if content_type and not headers:
                headers = Headers({"content-type": content_type})
            return _orig_upload_init(self, file=file, size=size, filename=filename, headers=headers, **kwargs)
        _StarletteUploadFile.__init__ = _compat_upload_init
    except ImportError:
        pass


_setup_test_shims()
_enhance_real_fastapi_for_tests()

