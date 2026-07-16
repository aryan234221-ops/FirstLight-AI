from __future__ import annotations

import logging
import math

from app.rag.vector_store import DocumentChunk, VectorStore


logger = logging.getLogger(__name__)


class InMemoryVectorStore(VectorStore):
    """In-memory vector store using cosine similarity for retrieval."""

    def __init__(self) -> None:
        self._documents_by_project: dict[str, list[DocumentChunk]] = {}

    def add_documents(self, project_id: str, documents: list[DocumentChunk]) -> None:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            self._log_failed("add_documents", project_id, "project_id must be a non-empty string")
            raise ValueError("project_id must be a non-empty string")
        if not documents:
            self._log_failed("add_documents", normalized_project_id, "documents must not be empty")
            raise ValueError("documents must not be empty")

        for document in documents:
            if document.project_id != normalized_project_id:
                self._log_failed(
                    "add_documents",
                    normalized_project_id,
                    "all document chunks must belong to the provided project_id",
                )
                raise ValueError("all document chunks must belong to the provided project_id")
            if not document.embedding:
                self._log_failed("add_documents", normalized_project_id, "document embedding must not be empty")
                raise ValueError("document embedding must not be empty")

        project_documents = self._documents_by_project.setdefault(normalized_project_id, [])
        project_documents.extend(documents)

        logger.info(
            "vector_document_added",
            extra={
                "event": "vector_document_added",
                "project_id": normalized_project_id,
                "count": len(documents),
            },
        )

    def search(self, project_id: str, query_embedding: list[float], top_k: int = 5) -> list[DocumentChunk]:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            self._log_failed("search", project_id, "project_id must be a non-empty string")
            raise ValueError("project_id must be a non-empty string")
        if not query_embedding:
            self._log_failed("search", normalized_project_id, "query_embedding must not be empty")
            raise ValueError("query_embedding must not be empty")
        if top_k <= 0:
            self._log_failed("search", normalized_project_id, "top_k must be greater than 0")
            raise ValueError("top_k must be greater than 0")

        project_documents = self._documents_by_project.get(normalized_project_id, [])
        ranked = []
        for chunk in project_documents:
            if len(chunk.embedding) != len(query_embedding):
                continue
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            ranked.append((similarity, chunk))

        ranked.sort(key=lambda item: item[0], reverse=True)
        results = [chunk for _, chunk in ranked[:top_k]]

        logger.info(
            "vector_search",
            extra={
                "event": "vector_search",
                "project_id": normalized_project_id,
                "top_k": top_k,
                "returned": len(results),
            },
        )
        return results

    def delete_document(self, project_id: str, document_id: str) -> None:
        normalized_project_id = project_id.strip()
        normalized_document_id = document_id.strip()
        if not normalized_project_id:
            self._log_failed("delete_document", project_id, "project_id must be a non-empty string")
            raise ValueError("project_id must be a non-empty string")
        if not normalized_document_id:
            self._log_failed("delete_document", normalized_project_id, "document_id must be a non-empty string")
            raise ValueError("document_id must be a non-empty string")

        project_documents = self._documents_by_project.get(normalized_project_id, [])
        retained = [chunk for chunk in project_documents if chunk.document_id != normalized_document_id]
        self._documents_by_project[normalized_project_id] = retained

        logger.info(
            "vector_deleted",
            extra={
                "event": "vector_deleted",
                "project_id": normalized_project_id,
                "document_id": normalized_document_id,
                "deleted_count": len(project_documents) - len(retained),
            },
        )

    def clear_project(self, project_id: str) -> None:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            self._log_failed("clear_project", project_id, "project_id must be a non-empty string")
            raise ValueError("project_id must be a non-empty string")

        removed_count = len(self._documents_by_project.get(normalized_project_id, []))
        self._documents_by_project.pop(normalized_project_id, None)

        logger.info(
            "vector_project_cleared",
            extra={
                "event": "vector_project_cleared",
                "project_id": normalized_project_id,
                "cleared_count": removed_count,
            },
        )

    @staticmethod
    def _cosine_similarity(query_embedding: list[float], chunk_embedding: list[float]) -> float:
        query_norm = math.sqrt(sum(value * value for value in query_embedding))
        chunk_norm = math.sqrt(sum(value * value for value in chunk_embedding))
        if query_norm == 0.0 or chunk_norm == 0.0:
            return 0.0

        dot_product = sum(left * right for left, right in zip(query_embedding, chunk_embedding, strict=True))
        return dot_product / (query_norm * chunk_norm)

    @staticmethod
    def _log_failed(operation: str, project_id: str, message: str) -> None:
        logger.error(
            "vector_failed",
            extra={
                "event": "vector_failed",
                "operation": operation,
                "project_id": project_id,
                "reason": message,
            },
        )
