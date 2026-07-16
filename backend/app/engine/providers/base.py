"""Base provider contract for AI model integrations.

This module defines the abstract interface that all provider adapters must
implement. Providers are responsible for transforming a prompt and optional
provider-specific parameters into a text response.

Provider implementations must remain stateless. Runtime configuration such as
API keys, model names, endpoints, and other environment-specific values must
be supplied through configuration systems or dependency injection, not through
hardcoded constants in provider classes.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
	"""Abstract contract for AI text-generation providers.

	Concrete providers should implement this interface to expose a consistent
	generation API across multiple backends.

	Implementations must be stateless and rely on external configuration or
	dependency injection for all environment-specific settings.
	"""

	@abstractmethod
	def generate(self, prompt: str, **kwargs: Any) -> str:
		"""Generate a text response for a given prompt.

		Args:
			prompt: The input text sent to the provider.
			**kwargs: Additional provider-specific options such as generation
				parameters, request metadata, or invocation controls.

		Returns:
			The generated text response.

		Raises:
			NotImplementedError: Raised by abstract providers that do not
				override this method.
		"""
		raise NotImplementedError
