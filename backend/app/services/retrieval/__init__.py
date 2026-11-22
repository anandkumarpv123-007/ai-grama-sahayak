"""
Retrieval Service Package for AI Grama Sahayak (Member 2).
Provides verified public-service context and citations to Member 1's chat orchestration.
"""

from app.services.retrieval.service import (
    retrieve_context,
    RetrievalService,
    get_retrieval_service,
    get_citations,
    format_evidence_text,
)
from app.services.retrieval.models import (
    RetrievedChunk,
    SourceCitation,
    IngestedDocument,
)

__all__ = [
    "retrieve_context",
    "RetrievalService",
    "get_retrieval_service",
    "get_citations",
    "format_evidence_text",
    "RetrievedChunk",
    "SourceCitation",
    "IngestedDocument",
]
