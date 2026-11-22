"""
Core Retrieval Service for AI Grama Sahayak.
Implements the agreed internal retrieval interface consumed by Member 1's central chat orchestration.
"""

import logging
from typing import Any, Dict, List, Optional
from app.services.retrieval.chunking import MarkdownChunker
from app.services.retrieval.indexer import HybridMultilingualIndexer
from app.services.retrieval.ingestion import DocumentIngestionEngine
from app.services.retrieval.models import RetrievedChunk, SourceCitation

logger = logging.getLogger("ai_grama_sahayak.services.retrieval.service")

# Allowed assistant identifiers matching API contracts Section 3
VALID_ASSISTANTS = {"agriculture", "healthcare", "education", "schemes"}


class RetrievalService:
    """
    Main retrieval service coordinator.
    Manages document ingestion, chunking, multilingual hybrid indexing,
    and filtered context retrieval.
    """

    def __init__(
        self,
        kb_base_dir: Optional[str] = None,
        min_score_threshold: float = 0.06,
        target_chunk_size: int = 650,
        chunk_overlap: int = 80,
    ):
        self.kb_base_dir = kb_base_dir
        self.ingestion_engine = DocumentIngestionEngine(kb_base_dir=kb_base_dir)
        self.chunker = MarkdownChunker(
            target_chunk_size=target_chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.indexer = HybridMultilingualIndexer(
            min_score_threshold=min_score_threshold,
        )
        self._is_initialized = False

    def initialize(self, include_demo: bool = False) -> None:
        """
        Loads verified knowledge documents, chunks them, and builds the index.
        By default, strictly excludes demo fixtures.
        """
        logger.info("Initializing RetrievalService (include_demo=%s)...", include_demo)
        documents = self.ingestion_engine.ingest_directory(
            subdir="verified",
            include_demo=include_demo,
        )

        all_chunks: List[RetrievedChunk] = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        self.indexer.index_chunks(all_chunks)
        self._is_initialized = True
        logger.info(
            "RetrievalService initialized successfully with %d documents and %d chunks.",
            len(documents),
            len(all_chunks),
        )

    def retrieve(
        self,
        query: str,
        assistant: str,
        language: str = "en",
        state: Optional[str] = None,
        district: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching chunks strictly filtered by domain and returns predictable dictionaries.
        """
        # Validate assistant identifier
        assistant_clean = (assistant or "").strip().lower()
        if assistant_clean not in VALID_ASSISTANTS:
            raise ValueError(
                f"Invalid assistant '{assistant}'. Must be one of: {', '.join(sorted(VALID_ASSISTANTS))}."
            )

        # Handle empty or whitespace query honestly
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        # Lazy initialize if not yet loaded
        if not self._is_initialized:
            self.initialize(include_demo=False)

        # Perform domain-filtered search
        chunks = self.indexer.search(
            query=clean_query,
            assistant=assistant_clean,
            language=language,
            state=state,
            district=district,
            top_k=top_k,
        )

        # Convert to predictable dictionaries
        return [chunk.to_dict() for chunk in chunks]


# Singleton instance for application-wide retrieval
_global_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _global_service
    if _global_service is None:
        _global_service = RetrievalService()
    return _global_service


def retrieve_context(
    query: str,
    assistant: str,
    language: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Standard internal interface consumed by Member 1's chat orchestration.
    Coordinates with Member 1 via backend/app/core/retrieval_client.py.

    Parameters:
        query: User message or search query string.
        assistant: Assistant identifier ('agriculture', 'healthcare', 'education', 'schemes').
        language: Language code ('en', 'te').
        state: State filter (e.g. 'Andhra Pradesh') or None.
        district: District filter (e.g. 'Kakinada') or None.
        top_k: Maximum number of chunks to return (default 5).

    Returns:
        List of chunk dictionaries, each containing:
        - text
        - title
        - url
        - publisher
        - verified_at
        - source (dict with title, url, publisher, verified_at)
        - metadata (domain, language, score, state, district, chunk_id)
        - score
    """
    service = get_retrieval_service()
    return service.retrieve(
        query=query,
        assistant=assistant,
        language=language,
        state=state,
        district=district,
        top_k=top_k,
    )


def get_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Helper function extracting unique, deduplicated citations formatted
    strictly as Section 3 Common Source Objects for Member 1 responses.
    """
    citations: List[Dict[str, str]] = []
    seen_urls = set()

    for chunk in chunks:
        source = chunk.get("source") or {}
        url = source.get("url") or chunk.get("url")
        if not url or url in seen_urls:
            continue

        citation = {
            "title": str(source.get("title") or chunk.get("title") or "Official source"),
            "url": str(url),
            "publisher": str(source.get("publisher") or chunk.get("publisher") or "Government Authority"),
            "verified_at": str(source.get("verified_at") or chunk.get("verified_at") or "2026-11-21"),
        }
        citations.append(citation)
        seen_urls.add(url)

    return citations


def format_evidence_text(chunks: List[Dict[str, Any]]) -> str:
    """
    Helper function formatting retrieved chunks into clean evidence text
    ready for prompt injection.
    """
    if not chunks:
        return ""

    snippets: List[str] = []
    for idx, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Evidence")
        text = chunk.get("text", "").strip()
        snippets.append(f"--- Evidence Chunk {idx} [{title}] ---\n{text}")

    return "\n\n".join(snippets)
