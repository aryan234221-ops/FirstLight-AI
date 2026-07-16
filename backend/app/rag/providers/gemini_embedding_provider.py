from __future__ import annotations

import logging
import os

from google import genai

from app.rag.embedding_provider import EmbeddingProvider


logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Gemini-based embedding provider implementation."""

    def __init__(self) -> None:
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self._model_name = (os.getenv("GEMINI_EMBEDDING_MODEL") or "models/gemini-embedding-001").strip()
        if not self._model_name:
            self._model_name = "models/gemini-embedding-001"

        self._client = genai.Client(api_key=api_key)

    def embed(self, text: str) -> list[float]:
        normalized_text = text.strip()
        if not normalized_text:
            self._log_failed(operation="embed", reason="text must be a non-empty string")
            raise ValueError("text must be a non-empty string")

        logger.info(
            "embedding_started",
            extra={
                "event": "embedding_started",
                "provider": "gemini",
                "operation": "embed",
                "model": self._model_name,
            },
        )

        try:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=[normalized_text],
            )

            embedding = response.embeddings[0].values
            vector = [float(value) for value in embedding]
        except Exception as exc:
            self._log_failed(operation="embed", reason=type(exc).__name__)
            raise

        logger.info(
            "embedding_completed",
            extra={
                "event": "embedding_completed",
                "provider": "gemini",
                "operation": "embed",
                "model": self._model_name,
                "count": 1,
            },
        )
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            self._log_failed(operation="embed_batch", reason="texts must not be empty")
            raise ValueError("texts must not be empty")

        normalized_texts = [text.strip() for text in texts]
        if any(not text for text in normalized_texts):
            self._log_failed(operation="embed_batch", reason="all texts must be non-empty strings")
            raise ValueError("all texts must be non-empty strings")

        logger.info(
            "embedding_started",
            extra={
                "event": "embedding_started",
                "provider": "gemini",
                "operation": "embed_batch",
                "model": self._model_name,
                "count": len(normalized_texts),
            },
        )

        try:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=normalized_texts,
            )
            vectors = [[float(value) for value in item.values] for item in response.embeddings]
        except Exception as exc:
            self._log_failed(operation="embed_batch", reason=type(exc).__name__)
            raise

        logger.info(
            "embedding_completed",
            extra={
                "event": "embedding_completed",
                "provider": "gemini",
                "operation": "embed_batch",
                "model": self._model_name,
                "count": len(vectors),
            },
        )
        return vectors

    @staticmethod
    def _log_failed(operation: str, reason: str) -> None:
        logger.error(
            "embedding_failed",
            extra={
                "event": "embedding_failed",
                "provider": "gemini",
                "operation": operation,
                "reason": reason,
            },
        )
