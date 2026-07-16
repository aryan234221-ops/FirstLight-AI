"""Core AI engine orchestrator.

This module provides a provider-agnostic engine that delegates text generation
to an injected provider implementing the BaseProvider contract.
"""

import logging
from typing import Any

from app.engine.providers.base import BaseProvider


logger = logging.getLogger(__name__)


class AIEngine:
	"""Provider-agnostic AI generation engine.

	The engine depends only on BaseProvider and delegates generation calls to
	the injected provider implementation.
	"""

	def __init__(self, provider: BaseProvider) -> None:
		"""Initialize the engine with a provider dependency.

		Args:
			provider: Provider implementation used for text generation.
		"""
		self._provider: BaseProvider = provider

	def generate(self, prompt: str, **kwargs: Any) -> str:
		"""Generate text by delegating to the injected provider.

		Args:
			prompt: Prompt string to pass through to the provider.
			**kwargs: Provider-specific generation arguments.

		Returns:
			The generated text from the provider.

		Raises:
			Exception: Re-raises any exception from the provider.
		"""
		provider_type = type(self._provider).__name__
		logger.info(
			"ai_generation_started",
			extra={"event": "ai_generation_started", "provider_type": provider_type},
		)

		try:
			result = self._provider.generate(prompt, **kwargs)
		except Exception as exc:
			logger.exception(
				"ai_generation_failed",
				extra={
					"event": "ai_generation_failed",
					"provider_type": provider_type,
					"error_type": type(exc).__name__,
				},
			)
			raise

		logger.info(
			"ai_generation_succeeded",
			extra={"event": "ai_generation_succeeded", "provider_type": provider_type},
		)
		return result
