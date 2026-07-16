"""Application composition root for shared services.

This module defines the application context responsible for assembling and
exposing shared dependencies through lazy initialization.
"""

import logging
from pathlib import Path

from dotenv import load_dotenv

from app.engine.core.engine import AIEngine
from app.engine.dispatcher import AgentDispatcher
from app.engine.parser import ResponseParser
from app.engine.prompts import PromptManager
from app.engine.providers.base import BaseProvider
from app.engine.providers.provider_factory import ProviderFactory
from app.engine.registry import AgentRegistry
from app.services.planning_service import PlanningService


logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "gemini"
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
DOTENV_PATH: Path = PROJECT_ROOT / ".env"


class ApplicationContext:
    """Composition root for application-wide shared services.

    Dependencies are created lazily on first access and then reused for the
    lifetime of the context instance.
    """

    def __init__(self) -> None:
        """Initialize lazy dependency placeholders for the application context."""
        load_dotenv(dotenv_path=DOTENV_PATH)
        logger.info(
            "environment_loaded",
            extra={"event": "environment_loaded", "dotenv_path": str(DOTENV_PATH)},
        )

        logger.info(
            "application_context_initializing",
            extra={"event": "application_context_initializing"},
        )

        self._prompt_manager: PromptManager | None = None
        self._provider: BaseProvider | None = None
        self._ai_engine: AIEngine | None = None
        self._planning_service: PlanningService | None = None
        self.__response_parser: ResponseParser | None = None
        self.__agent_registry: AgentRegistry | None = None
        self.__agent_dispatcher: AgentDispatcher | None = None

        logger.info(
            "application_context_ready",
            extra={"event": "application_context_ready", "initialization": "lazy"},
        )

    @property
    def prompt_manager(self) -> PromptManager:
        """Return the shared prompt manager instance.

        Returns:
            The lazily initialized ``PromptManager``.
        """
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "prompt_manager",
                },
            )
        return self._prompt_manager

    @property
    def provider(self) -> BaseProvider:
        """Return the shared AI provider instance.

        Returns:
            The lazily initialized provider implementing ``BaseProvider``.

        Raises:
            Exception: Re-raises provider construction failures.
        """
        if self._provider is None:
            try:
                self._provider = ProviderFactory.create(DEFAULT_PROVIDER)
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "provider",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "provider",
                        "provider_name": DEFAULT_PROVIDER,
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self._provider

    @property
    def ai_engine(self) -> AIEngine:
        """Return the shared AI engine instance.

        Returns:
            The lazily initialized ``AIEngine``.

        Raises:
            Exception: Re-raises AI engine construction failures.
        """
        if self._ai_engine is None:
            try:
                self._ai_engine = AIEngine(provider=self.provider)
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "ai_engine",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "ai_engine",
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self._ai_engine

    @property
    def planning_service(self) -> PlanningService:
        """Return the shared planning service instance.

        Returns:
            The lazily initialized ``PlanningService``.

        Raises:
            Exception: Re-raises planning service construction failures.
        """
        if self._planning_service is None:
            try:
                self._planning_service = PlanningService(
                    prompt_manager=self.prompt_manager,
                    ai_engine=self.ai_engine,
                )
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "planning_service",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "planning_service",
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self._planning_service

    @property
    def response_parser(self) -> ResponseParser:
        """Return the shared response parser instance.

        Returns:
            The lazily initialized ``ResponseParser``.
        """
        if self.__response_parser is None:
            self.__response_parser = ResponseParser()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "response_parser",
                },
            )
        return self.__response_parser

    @property
    def agent_registry(self) -> AgentRegistry:
        """Return the shared agent registry instance.

        Returns:
            The lazily initialized ``AgentRegistry``.

        Raises:
            Exception: Re-raises registry construction failures.
        """
        if self.__agent_registry is None:
            try:
                self.__agent_registry = AgentRegistry(
                    planning_service=self.planning_service,
                    response_parser=self.response_parser,
                )
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "agent_registry",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "agent_registry",
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self.__agent_registry

    @property
    def agent_dispatcher(self) -> AgentDispatcher:
        """Return the shared agent dispatcher instance.

        Returns:
            The lazily initialized ``AgentDispatcher``.

        Raises:
            Exception: Re-raises dispatcher construction failures.
        """
        if self.__agent_dispatcher is None:
            try:
                self.__agent_dispatcher = AgentDispatcher(
                    agents=self.agent_registry.all(),
                )
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "agent_dispatcher",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "agent_dispatcher",
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self.__agent_dispatcher
