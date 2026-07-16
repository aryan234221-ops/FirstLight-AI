"""Prompt loading utilities for system prompts.

This module provides a prompt manager that loads Markdown prompt files from a
single configurable directory and caches loaded prompt content in memory.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Central prompt directory for system prompts.
# This can be replaced by the project's centralized configuration layer later.
SYSTEM_PROMPTS_DIR: Path = Path(
    os.getenv("FIRSTLIGHT_SYSTEM_PROMPTS_DIR", "backend/prompts/system")
)


class PromptManager:
    """Load and cache system prompt files.

    Prompts are loaded from Markdown files in the configured prompt directory.
    Loaded prompt content is cached in memory for subsequent requests.
    """

    def __init__(self, prompt_dir: Path | None = None) -> None:
        """Initialize the prompt manager.

        Args:
            prompt_dir: Optional override for the system prompt directory.
                When not provided, ``SYSTEM_PROMPTS_DIR`` is used.
        """
        self._prompt_dir: Path = prompt_dir or SYSTEM_PROMPTS_DIR
        self._cache: dict[str, str] = {}

    def load(self, prompt_name: str) -> str:
        """Load a system prompt by name.

        Example:
            ``load(prompt_name="ceo")`` resolves to ``ceo.md`` in the
            configured prompt directory.

        Args:
            prompt_name: Prompt identifier without file extension.

        Returns:
            The prompt file content as text.

        Raises:
            ValueError: If ``prompt_name`` is empty.
            FileNotFoundError: If the target prompt file does not exist.
        """
        normalized_name = prompt_name.strip()
        if not normalized_name:
            raise ValueError("prompt_name must be a non-empty string")

        cached = self._cache.get(normalized_name)
        if cached is not None:
            logger.info(
                "prompt_loaded",
                extra={
                    "event": "prompt_loaded",
                    "prompt_name": normalized_name,
                    "source": "cache",
                },
            )
            return cached

        prompt_path = self._prompt_dir / f"{normalized_name}.md"
        if not prompt_path.is_file():
            logger.warning(
                "prompt_missing",
                extra={
                    "event": "prompt_missing",
                    "prompt_name": normalized_name,
                    "prompt_path": str(prompt_path),
                },
            )
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8")
        self._cache[normalized_name] = content

        logger.info(
            "prompt_loaded",
            extra={
                "event": "prompt_loaded",
                "prompt_name": normalized_name,
                "source": "filesystem",
            },
        )
        return content
