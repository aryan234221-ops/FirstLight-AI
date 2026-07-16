from __future__ import annotations

import logging

from app.rag.document_chunker import DocumentChunker
from app.rag.embedding_provider import EmbeddingProvider
from app.rag.vector_store import DocumentChunk, VectorStore


logger = logging.getLogger(__name__)


class KnowledgeIndexingService:
    """Provider-agnostic indexing pipeline for project knowledge documents."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        chunker: DocumentChunker,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._chunker = chunker

    def index_document(self, project_id: str, document_id: str, text: str) -> None:
        normalized_project_id = project_id.strip()
        normalized_document_id = document_id.strip()
        normalized_text = text.strip()

        if not normalized_project_id:
            self._log_failed(project_id=normalized_project_id, document_id=normalized_document_id, error_type="ValueError")
            raise ValueError("project_id must be a non-empty string")
        if not normalized_document_id:
            self._log_failed(project_id=normalized_project_id, document_id=normalized_document_id, error_type="ValueError")
            raise ValueError("document_id must be a non-empty string")
        if not normalized_text:
            self._log_failed(project_id=normalized_project_id, document_id=normalized_document_id, error_type="ValueError")
            raise ValueError("text must be a non-empty string")

        logger.info(
            "indexing_started",
            extra={
                "event": "indexing_started",
                "project_id": normalized_project_id,
                "document_id": normalized_document_id,
            },
        )

        try:
            base_chunks = self._chunker.chunk(
                document_id=normalized_document_id,
                project_id=normalized_project_id,
                text=normalized_text,
            )
            logger.info(
                "document_chunked",
                extra={
                    "event": "document_chunked",
                    "project_id": normalized_project_id,
                    "document_id": normalized_document_id,
                    "chunk_count": len(base_chunks),
                },
            )

            embeddings = self._embedding_provider.embed_batch([chunk.text for chunk in base_chunks])
            logger.info(
                "embedding_generated",
                extra={
                    "event": "embedding_generated",
                    "project_id": normalized_project_id,
                    "document_id": normalized_document_id,
                    "chunk_count": len(embeddings),
                },
            )

            if len(embeddings) != len(base_chunks):
                raise ValueError("embedding count must match chunk count")

            indexed_chunks: list[DocumentChunk] = []
            for chunk, embedding in zip(base_chunks, embeddings, strict=True):
                indexed_chunks.append(
                    DocumentChunk(
                        id=chunk.id,
                        project_id=chunk.project_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        embedding=embedding,
                        metadata=chunk.metadata,
                    )
                )

            self._vector_store.add_documents(
                project_id=normalized_project_id,
                documents=indexed_chunks,
            )
            logger.info(
                "vector_indexed",
                extra={
                    "event": "vector_indexed",
                    "project_id": normalized_project_id,
                    "document_id": normalized_document_id,
                    "chunk_count": len(indexed_chunks),
                },
            )
        except Exception as exc:
            self._log_failed(
                project_id=normalized_project_id,
                document_id=normalized_document_id,
                error_type=type(exc).__name__,
            )
            raise

        logger.info(
            "indexing_completed",
            extra={
                "event": "indexing_completed",
                "project_id": normalized_project_id,
                "document_id": normalized_document_id,
                "chunk_count": len(indexed_chunks),
            },
        )

    @staticmethod
    def _log_failed(project_id: str, document_id: str, error_type: str) -> None:
        logger.error(
            "indexing_failed",
            extra={
                "event": "indexing_failed",
                "project_id": project_id,
                "document_id": document_id,
                "error_type": error_type,
            },
        )
