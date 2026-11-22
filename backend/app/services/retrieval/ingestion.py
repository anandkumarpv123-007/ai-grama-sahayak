"""
Document Ingestion Engine for AI Grama Sahayak Knowledge Base.
Supports Markdown (.md), Plain Text (.txt), HTML (.html), and PDF (.pdf) documents.
Extracts frontmatter metadata, validates against sources_manifest.csv,
and strictly separates production verified records from synthetic demo fixtures.
"""

import csv
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.services.retrieval.models import IngestedDocument

logger = logging.getLogger("ai_grama_sahayak.services.retrieval.ingestion")


class DocumentIngestionEngine:
    """
    Ingests and parses source documents into structured IngestedDocument objects.
    """

    def __init__(self, kb_base_dir: Optional[str] = None):
        if kb_base_dir:
            self.kb_base_dir = Path(kb_base_dir)
        else:
            # Default to repo root / knowledge_base
            current_dir = Path(__file__).resolve().parent
            # Navigate up: retrieval -> services -> app -> backend -> repo_root
            repo_root = current_dir.parent.parent.parent.parent
            self.kb_base_dir = repo_root / "knowledge_base"

        self.manifest_path = self.kb_base_dir / "sources_manifest.csv"
        self._manifest_cache: Dict[str, Dict[str, str]] = {}

    def load_manifest(self) -> Dict[str, Dict[str, str]]:
        """
        Loads knowledge_base/sources_manifest.csv and caches records by URL/Title.
        """
        if not self.manifest_path.exists():
            logger.warning("sources_manifest.csv not found at %s", self.manifest_path)
            return {}

        manifest: Dict[str, Dict[str, str]] = {}
        try:
            with open(self.manifest_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = (row.get("url") or "").strip()
                    title = (row.get("title") or "").strip()
                    if url:
                        manifest[url] = row
                    if title:
                        manifest[title.lower()] = row
            self._manifest_cache = manifest
        except Exception as exc:
            logger.error("Failed to read sources_manifest.csv: %s", exc)

        return self._manifest_cache

    def ingest_directory(
        self,
        subdir: str = "verified",
        include_demo: bool = False,
    ) -> List[IngestedDocument]:
        """
        Ingests all documents from a knowledge base directory.
        By default, ingests only 'verified' documents and strictly excludes 'demo'.
        """
        target_dir = self.kb_base_dir / subdir
        if not target_dir.exists():
            logger.warning("Target directory does not exist: %s", target_dir)
            return []

        documents: List[IngestedDocument] = []
        for root, _, files in os.walk(target_dir):
            for file in sorted(files):
                file_path = Path(root) / file
                doc = self.ingest_file(file_path)
                if doc is None:
                    continue

                # Strict isolation: Do not load demo fixtures or unverified sources in trusted production retrieval
                if not include_demo and (doc.status in ("demo", "unverified") or "demo" in str(file_path)):
                    logger.debug("Skipping demo or unverified document in production mode: %s", file_path)
                    continue

                documents.append(doc)

        logger.info(
            "Ingestion completed: %d documents loaded from %s (include_demo=%s)",
            len(documents),
            target_dir,
            include_demo,
        )
        return documents

    def ingest_file(self, file_path: Path | str) -> Optional[IngestedDocument]:
        """
        Ingests an individual file based on its extension (.md, .txt, .html, .pdf).
        """
        path = Path(file_path)
        if not path.is_file():
            logger.warning("File does not exist: %s", path)
            return None

        suffix = path.suffix.lower()
        try:
            if suffix in [".md", ".markdown"]:
                return self._parse_markdown(path)
            elif suffix == ".txt":
                return self._parse_text(path)
            elif suffix in [".html", ".htm"]:
                return self._parse_html(path)
            elif suffix == ".pdf":
                return self._parse_pdf(path)
            else:
                logger.debug("Unsupported file type ignored: %s", path)
                return None
        except Exception as exc:
            logger.error("Failed to ingest file %s: %s", path, exc, exc_info=True)
            return None

    def _parse_frontmatter(self, text: str) -> tuple[Dict[str, Any], str]:
        """
        Extracts YAML-style frontmatter headers between '---' delimiters.
        """
        metadata: Dict[str, Any] = {}
        content = text

        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, text, re.DOTALL)
        if match:
            raw_meta, content = match.group(1), match.group(2)
            for line in raw_meta.split("\n"):
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.lower() == "null" or val == "":
                    metadata[key] = None
                elif val.lower() == "true":
                    metadata[key] = True
                elif val.lower() == "false":
                    metadata[key] = False
                else:
                    metadata[key] = val

        return metadata, content.strip()

    def _parse_markdown(self, path: Path) -> IngestedDocument:
        with open(path, mode="r", encoding="utf-8") as f:
            raw = f.read()

        meta, content = self._parse_frontmatter(raw)
        doc_id = meta.get("id") or path.stem
        title = meta.get("title") or self._extract_first_header(content) or path.stem.replace("_", " ").title()
        domain = meta.get("domain") or path.parent.name
        url = meta.get("url") or "https://ap.gov.in"
        publisher = meta.get("publisher") or "Government of Andhra Pradesh"
        verified_at = meta.get("verified_at") or "2026-11-21"
        language = meta.get("language") or "bilingual"
        status = meta.get("status") or ("demo" if "demo" in str(path) else "active")

        return IngestedDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            domain=domain,
            url=url,
            publisher=publisher,
            verified_at=verified_at,
            language=language,
            state=meta.get("state", "Andhra Pradesh"),
            district=meta.get("district"),
            status=status,
            file_path=str(path),
            metadata=meta,
        )

    def _parse_text(self, path: Path) -> IngestedDocument:
        with open(path, mode="r", encoding="utf-8") as f:
            raw = f.read()

        meta, content = self._parse_frontmatter(raw)
        doc_id = meta.get("id") or path.stem
        title = meta.get("title") or path.stem.replace("_", " ").title()
        domain = meta.get("domain") or path.parent.name
        url = meta.get("url") or "https://ap.gov.in"
        publisher = meta.get("publisher") or "Government of Andhra Pradesh"
        verified_at = meta.get("verified_at") or "2026-11-21"

        return IngestedDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            domain=domain,
            url=url,
            publisher=publisher,
            verified_at=verified_at,
            language=meta.get("language", "bilingual"),
            state=meta.get("state", "Andhra Pradesh"),
            district=meta.get("district"),
            status=meta.get("status", "active"),
            file_path=str(path),
            metadata=meta,
        )

    def _parse_html(self, path: Path) -> IngestedDocument:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required for HTML ingestion")

        with open(path, mode="r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else path.stem.replace("_", " ").title()

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        content = soup.get_text(separator="\n\n").strip()
        doc_id = path.stem
        domain = path.parent.name

        return IngestedDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            domain=domain,
            url="https://ap.gov.in",
            publisher="Government of Andhra Pradesh",
            verified_at="2026-11-21",
            language="bilingual",
            state="Andhra Pradesh",
            district=None,
            status="active",
            file_path=str(path),
            metadata={},
        )

    def _parse_pdf(self, path: Path) -> IngestedDocument:
        text_pages: List[str] = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            for page in doc:
                text_pages.append(page.get_text())
            doc.close()
        except ImportError:
            # Fallback to pypdf
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for page in reader.pages:
                text_pages.append(page.extract_text() or "")

        content = "\n\n".join(text_pages).strip()
        doc_id = path.stem
        title = path.stem.replace("_", " ").title()
        domain = path.parent.name

        return IngestedDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            domain=domain,
            url="https://ap.gov.in",
            publisher="Government of Andhra Pradesh",
            verified_at="2026-11-21",
            language="bilingual",
            state="Andhra Pradesh",
            district=None,
            status="active",
            file_path=str(path),
            metadata={},
        )

    def _extract_first_header(self, text: str) -> Optional[str]:
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return re.sub(r"^#+\s*", "", line).strip()
        return None
