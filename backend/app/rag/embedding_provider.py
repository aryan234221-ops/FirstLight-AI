from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Provider-independent contract for embedding generation."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text input."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of text inputs."""
