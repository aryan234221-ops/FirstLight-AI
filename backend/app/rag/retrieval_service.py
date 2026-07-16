from __future__ import annotations

import logging

from app.rag.embedding_provider import EmbeddingProvider
from app.rag.vector_store import DocumentChunk, VectorStore


logger = logging.getLogger(__name__)


class RetrievalService:
    """Provider-independent retrieval orchestration for RAG."""

    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(self, project_id: str, query: str, top_k: int = 5) -> list[DocumentChunk]:
        normalized_project_id = project_id.strip()
        normalized_query = query.strip()

        if not normalized_project_id:
            self._log_failed(normalized_project_id, top_k, "ValueError")
            raise ValueError("project_id must be a non-empty string")
        if not normalized_query:
            self._log_failed(normalized_project_id, top_k, "ValueError")
            raise ValueError("query must be a non-empty string")
        if top_k <= 0:
            self._log_failed(normalized_project_id, top_k, "ValueError")
            raise ValueError("top_k must be greater than 0")

        logger.info(
            "retrieval_started",
            extra={
                "event": "retrieval_started",
                "project_id": normalized_project_id,
                "top_k": top_k,
            },
        )

        try:
            query_embedding = self._embedding_provider.embed(normalized_query)
            results = self._vector_store.search(
                project_id=normalized_project_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        except Exception as exc:
            self._log_failed(normalized_project_id, top_k, type(exc).__name__)
            raise

        logger.info(
            "retrieval_completed",
            extra={
                "event": "retrieval_completed",
                "project_id": normalized_project_id,
                "top_k": top_k,
                "result_count": len(results),
            },
        )
        return results

    @staticmethod
    def _log_failed(project_id: str, top_k: int, error_type: str) -> None:
        logger.error(
            "retrieval_failed",
            extra={
                "event": "retrieval_failed",
                "project_id": project_id,
                "top_k": top_k,
                "error_type": error_type,
            },
        )
