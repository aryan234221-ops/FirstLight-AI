"""Google Gemini provider implementation for FirstLight AI Studio.

This module contains a stateless provider adapter that integrates with the
Google GenAI SDK. Configuration is resolved during initialization and reused
for inference calls.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from google import genai

from app.engine.providers.base import BaseProvider


logger = logging.getLogger(__name__)


class ProviderConfigurationError(Exception):
	"""Raised when Gemini provider configuration is invalid or missing."""


class GeminiProvider(BaseProvider):
	"""Stateless Google Gemini provider.

	This provider validates configuration in ``__init__`` and creates one
	reusable ``genai.Client`` instance. The ``generate`` method only performs
	inference and returns generated text.

	Configuration is read from environment variables:
	- ``GEMINI_API_KEY``: Required API key.
	- ``GEMINI_MODEL``: Optional model name. Defaults to ``gemini-2.5-pro``.
	"""

	def __init__(self) -> None:
		"""Initialize the Gemini provider and validate configuration.

		Raises:
			ProviderConfigurationError: If the API key is missing, empty,
				or if client initialization fails.
		"""
		api_key = os.getenv("GEMINI_API_KEY", "").strip()
		model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip() or "gemini-2.5-pro"

		if not api_key:
			logger.error(
				"gemini_provider_configuration_invalid",
				extra={"event": "provider_config_invalid", "reason": "missing_api_key"},
			)
			raise ProviderConfigurationError("Missing required environment variable: GEMINI_API_KEY")

		self._model: str = model

		try:
			self._client: genai.Client = genai.Client(api_key=api_key)
		except Exception as exc:
			logger.exception(
				"gemini_provider_client_init_failed",
				extra={
					"event": "provider_client_init_failed",
					"model": self._model,
					"error_type": type(exc).__name__,
				},
			)
			raise ProviderConfigurationError("Failed to initialize Gemini client") from exc

		logger.info(
			"gemini_provider_initialized",
			extra={"event": "provider_initialized", "model": self._model},
		)

	def generate(self, prompt: str, **kwargs: Any) -> str:
		"""Generate text using the configured Gemini model.

		Args:
			prompt: Input prompt sent to the model.
			**kwargs: Optional provider-specific generation arguments forwarded
				to the SDK call.

		Returns:
			The generated text response.

		Raises:
			ValueError: If ``prompt`` is empty.
			RuntimeError: If inference fails or no text is returned.
		"""
		if not prompt or not prompt.strip():
			logger.error(
				"gemini_generate_invalid_input",
				extra={"event": "generate_invalid_input", "reason": "empty_prompt", "model": self._model},
			)
			raise ValueError("Prompt must be a non-empty string")

		logger.info(
			"gemini_generate_started",
			extra={"event": "generate_started", "model": self._model, "kwargs_count": len(kwargs)},
		)

		try:
			response = self._client.models.generate_content(
				model=self._model,
				contents=prompt,
				**kwargs,
			)
		except Exception as exc:
			logger.exception(
				"gemini_generate_failed",
				extra={"event": "generate_failed", "model": self._model, "error_type": type(exc).__name__},
			)
			raise RuntimeError("Gemini inference request failed") from exc

		text = getattr(response, "text", None)
		if isinstance(text, str) and text.strip():
			logger.info(
				"gemini_generate_succeeded",
				extra={"event": "generate_succeeded", "model": self._model},
			)
			return text

		logger.error(
			"gemini_generate_empty_response",
			extra={"event": "generate_empty_response", "model": self._model},
		)
		raise RuntimeError("Gemini returned an empty text response")
