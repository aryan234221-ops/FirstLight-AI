from __future__ import annotations

import re
from uuid import uuid4

from app.rag.vector_store import DocumentChunk


_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


class DocumentChunker:
    """Split document text into overlapping, sentence-aware chunks."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap must be greater than or equal to 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")

        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document_id: str, project_id: str, text: str) -> list[DocumentChunk]:
        normalized_document_id = document_id.strip()
        normalized_project_id = project_id.strip()
        normalized_text = text.strip()

        if not normalized_document_id:
            raise ValueError("document_id must be a non-empty string")
        if not normalized_project_id:
            raise ValueError("project_id must be a non-empty string")
        if not normalized_text:
            raise ValueError("text must be a non-empty string")

        parts = [part.strip() for part in _SENTENCE_SPLIT_PATTERN.split(normalized_text) if part.strip()]

        if not parts:
            parts = [normalized_text]

        chunks: list[DocumentChunk] = []
        current = ""
        carry = ""

        for sentence in parts:
            candidate = sentence if not current else f"{current} {sentence}"
            if len(candidate) <= self._chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(self._to_chunk(normalized_project_id, normalized_document_id, current, len(chunks)))
                carry = current[-self._overlap :] if self._overlap > 0 else ""

            if len(sentence) > self._chunk_size:
                pointer = 0
                while pointer < len(sentence):
                    end = min(pointer + self._chunk_size, len(sentence))
                    piece = sentence[pointer:end].strip()
                    if piece:
                        chunks.append(self._to_chunk(normalized_project_id, normalized_document_id, piece, len(chunks)))
                    if end >= len(sentence):
                        break
                    pointer = max(end - self._overlap, pointer + 1)
                current = ""
                carry = ""
                continue

            current = f"{carry} {sentence}".strip() if carry else sentence

        if current:
            chunks.append(self._to_chunk(normalized_project_id, normalized_document_id, current, len(chunks)))

        return chunks

    @staticmethod
    def _to_chunk(project_id: str, document_id: str, text: str, index: int) -> DocumentChunk:
        return DocumentChunk(
            id=str(uuid4()),
            project_id=project_id,
            document_id=document_id,
            text=text,
            embedding=[],
            metadata={"chunk_index": index},
        )
