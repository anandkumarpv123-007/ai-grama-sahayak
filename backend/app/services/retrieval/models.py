"""
Data models and schemas for Member 2's retrieval service.
Ensures predictable chunk structures, citation formats matching api_contracts.md,
and strict type validation.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourceCitation:
    """
    Standard citation object matching Section 3 Common Source Object in docs/api_contracts.md:
    {
      "title": "Official source title",
      "url": "https://verified-official-source.gov.in/page",
      "publisher": "Government department",
      "verified_at": "2026-11-21"
    }
    """
    title: str
    url: str
    publisher: str
    verified_at: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "publisher": self.publisher,
            "verified_at": self.verified_at,
        }


@dataclass
class RetrievedChunk:
    """
    Predictable retrieval chunk structure.
    Satisfies both Member 1's agent requirements (chunk['source'])
    and core RAG interface requirements (chunk['text'], chunk['title'], etc.).
    """
    text: str
    title: str
    url: str
    publisher: str
    verified_at: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation guaranteed to contain all required fields.
        Includes nested 'source' dict for seamless compatibility with Member 1's agents.
        """
        source_dict = {
            "title": self.title,
            "url": self.url,
            "publisher": self.publisher,
            "verified_at": self.verified_at,
        }
        return {
            "text": self.text,
            "title": self.title,
            "url": self.url,
            "publisher": self.publisher,
            "verified_at": self.verified_at,
            "score": round(self.score, 4),
            "source": source_dict,
            "metadata": self.metadata,
        }


@dataclass
class IngestedDocument:
    """
    Internal representation of an ingested document before chunking.
    """
    doc_id: str
    title: str
    content: str
    domain: str
    url: str
    publisher: str
    verified_at: str
    language: str = "bilingual"
    state: Optional[str] = None
    district: Optional[str] = None
    status: str = "active"
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
