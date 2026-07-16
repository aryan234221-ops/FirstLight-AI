from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentChunk:
    """Represents an embedded chunk of a project document."""

    id: str
    project_id: str
    document_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """Provider-independent vector store contract for RAG retrieval."""

    @abstractmethod
    def add_documents(self, project_id: str, documents: list[DocumentChunk]) -> None:
        """Add document chunks for a project."""

    @abstractmethod
    def search(self, project_id: str, query_embedding: list[float], top_k: int = 5) -> list[DocumentChunk]:
        """Search for top matching chunks by query embedding."""

    @abstractmethod
    def delete_document(self, project_id: str, document_id: str) -> None:
        """Delete all chunks belonging to a document."""

    @abstractmethod
    def clear_project(self, project_id: str) -> None:
        """Clear all chunks for a project."""
