"""Provider factory for creating AI provider instances.

This module centralizes provider construction so agents depend only on the
provider abstraction and never instantiate concrete providers directly.
"""

import logging

from app.engine.providers.base import BaseProvider
from app.engine.providers.gemini import GeminiProvider


logger = logging.getLogger(__name__)


class ProviderFactory:
	"""Factory for creating configured provider instances.

	The factory resolves provider names via an internal registry and returns
	instances that implement ``BaseProvider``.
	"""

	PROVIDERS: dict[str, type[BaseProvider]] = {
		"gemini": GeminiProvider,
	}

	@staticmethod
	def supported_providers() -> list[str]:
		"""Return provider names supported by the factory.

		Returns:
			A sorted list of supported provider identifiers.
		"""
		return sorted(ProviderFactory.PROVIDERS.keys())

	@staticmethod
	def create(provider_name: str) -> BaseProvider:
		"""Create a provider instance from a provider name.

		Args:
			provider_name: Provider identifier, normalized case-insensitively
				after trimming surrounding whitespace.

		Returns:
			A provider instance implementing ``BaseProvider``.

		Raises:
			ValueError: If the provider is unsupported.
		"""
		normalized_name = provider_name.strip().lower()
		supported = ProviderFactory.supported_providers()

		provider_class = ProviderFactory.PROVIDERS.get(normalized_name)
		if provider_class is None:
			logger.error(
				"provider_creation_unsupported",
				extra={
					"event": "provider_creation_unsupported",
					"provider": normalized_name,
					"supported_providers": supported,
				},
			)
			raise ValueError(
				"Unsupported provider: "
				f"{provider_name!r}. Supported providers: {', '.join(supported)}"
			)

		logger.info(
			"provider_creation_started",
			extra={"event": "provider_creation_started", "provider": normalized_name},
		)
		provider = provider_class()
		logger.info(
			"provider_creation_succeeded",
			extra={"event": "provider_creation_succeeded", "provider": normalized_name},
		)
		return provider
