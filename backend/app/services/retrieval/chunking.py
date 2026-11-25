"""
Chunking module for RAG service.
Splits documents into meaningful, context-preserving text chunks while strictly
preserving source metadata (title, URL, publisher, verified_at, domain, status).
"""

import re
from typing import List
from app.services.retrieval.models import IngestedDocument, RetrievedChunk


class MarkdownChunker:
    """
    Hierarchical chunker designed for government scheme documents, policies, and FAQs.
    Splits by Markdown headers (##, ###) and paragraphs while respecting maximum chunk size.
    """

    def __init__(self, target_chunk_size: int = 650, chunk_overlap: int = 80):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: IngestedDocument) -> List[RetrievedChunk]:
        """
        Splits an IngestedDocument into a list of RetrievedChunk objects.
        Every chunk retains complete source metadata and receives a unique chunk_id.
        """
        raw_text = doc.content.strip()
        if not raw_text:
            return []

        # Split document by Markdown headings (e.g., '# ', '## ', '### ')
        sections = self._split_into_sections(raw_text)

        chunks: List[RetrievedChunk] = []
        chunk_index = 0

        for section_title, section_body in sections:
            # Further split section body into paragraph chunks if it exceeds target size
            sub_chunks = self._chunk_section_text(section_title, section_body)

            for text_chunk in sub_chunks:
                chunk_id = f"{doc.doc_id}_c{chunk_index}"
                chunk_meta = {
                    "doc_id": doc.doc_id,
                    "chunk_id": chunk_id,
                    "section_title": section_title,
                    "domain": doc.domain,
                    "language": doc.language,
                    "state": doc.state,
                    "district": doc.district,
                    "status": doc.status,
                }
                # Merge any additional metadata
                if doc.metadata:
                    for k, v in doc.metadata.items():
                        if k not in chunk_meta:
                            chunk_meta[k] = v

                chunk = RetrievedChunk(
                    text=text_chunk,
                    title=doc.title,
                    url=doc.url,
                    publisher=doc.publisher,
                    verified_at=doc.verified_at,
                    score=0.0,
                    metadata=chunk_meta,
                )
                chunks.append(chunk)
                chunk_index += 1

        return chunks

    def _split_into_sections(self, text: str) -> List[tuple[str, str]]:
        """
        Splits markdown text into (header_title, body) tuples.
        """
        lines = text.split("\n")
        sections: List[tuple[str, str]] = []
        current_title = "General"
        current_lines: List[str] = []

        header_pattern = re.compile(r"^(#{1,4})\s+(.+)$")

        for line in lines:
            match = header_pattern.match(line.strip())
            if match:
                # Save previous section if not empty
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_title, body))
                current_title = match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)

        # Append last section
        last_body = "\n".join(current_lines).strip()
        if last_body:
            sections.append((current_title, last_body))

        if not sections and text.strip():
            sections.append(("Overview", text.strip()))

        return sections

    def _chunk_section_text(self, section_title: str, text: str) -> List[str]:
        """
        Breaks section text into smaller chunks if it exceeds target_chunk_size,
        respecting paragraph and bullet point boundaries.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return [f"[{section_title}]\n{text}"] if text.strip() else []

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len > self.target_chunk_size and current_chunk:
                combined_text = "\n\n".join(current_chunk)
                header_prefix = f"[{section_title}]\n" if section_title != "General" else ""
                chunks.append(f"{header_prefix}{combined_text}")

                # Maintain small overlap if possible
                overlap_seed = current_chunk[-1] if len(current_chunk[-1]) < self.chunk_overlap else ""
                current_chunk = [overlap_seed, para] if overlap_seed else [para]
                current_len = sum(len(p) for p in current_chunk)
            else:
                current_chunk.append(para)
                current_len += para_len

        if current_chunk:
            combined_text = "\n\n".join(current_chunk)
            header_prefix = f"[{section_title}]\n" if section_title != "General" else ""
            chunks.append(f"{header_prefix}{combined_text}")

        return chunks
