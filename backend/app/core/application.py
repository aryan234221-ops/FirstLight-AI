"""Application composition root for shared services.

This module defines the application context responsible for assembling and
exposing shared dependencies through lazy initialization.
"""

import logging
from pathlib import Path
from sqlalchemy.orm import Session

from dotenv import load_dotenv

from app.auth.service import AuthService
from app.core.config import PlatformConfig, load_config
from app.db.database import SessionLocal, init_db
from app.engine.core.engine import AIEngine
from app.engine.dispatcher import AgentDispatcher
from app.engine.parser import ResponseParser
from app.engine.prompts import PromptManager
from app.engine.providers.base import BaseProvider
from app.engine.providers.provider_factory import ProviderFactory
from app.engine.registry import AgentRegistry
from app.rag.document_chunker import DocumentChunker
from app.rag.knowledge_indexing_service import KnowledgeIndexingService
from app.rag.prompt_augmentation_service import PromptAugmentationService
from app.rag.providers.gemini_embedding_provider import GeminiEmbeddingProvider
from app.rag.providers.in_memory_vector_store import InMemoryVectorStore
from app.rag.retrieval_service import RetrievalService
from app.services.knowledge_service import KnowledgeService
from app.services.planning_service import PlanningService
from app.repositories.sql_repositories import AuthRepository, KnowledgeRepository
from app.workflows.workflow_planner import WorkflowPlanner
from app.workflows.workflow_orchestrator import WorkflowOrchestrator


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

        init_db()

        self._config: PlatformConfig = load_config()
        self._prompt_manager: PromptManager | None = None
        self._provider: BaseProvider | None = None
        self._ai_engine: AIEngine | None = None
        self._embedding_provider: GeminiEmbeddingProvider | None = None
        self._vector_store: InMemoryVectorStore | None = None
        self._document_chunker: DocumentChunker | None = None
        self._retrieval_service: RetrievalService | None = None
        self._prompt_augmentation_service: PromptAugmentationService | None = None
        self._knowledge_indexing_service: KnowledgeIndexingService | None = None
        self._knowledge_service: KnowledgeService | None = None
        self._workflow_planner: WorkflowPlanner | None = None
        self._planning_service: PlanningService | None = None
        self._auth_service: AuthService | None = None
        self.__response_parser: ResponseParser | None = None
        self.__agent_registry: AgentRegistry | None = None
        self.__agent_dispatcher: AgentDispatcher | None = None
        self._workflow_orchestrator: WorkflowOrchestrator | None = None

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
    def embedding_provider(self) -> GeminiEmbeddingProvider:
        """Return the shared embedding provider instance."""
        if self._embedding_provider is None:
            self._embedding_provider = GeminiEmbeddingProvider()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "embedding_provider",
                },
            )
        return self._embedding_provider

    @property
    def vector_store(self) -> InMemoryVectorStore:
        """Return the shared vector store instance."""
        if self._vector_store is None:
            self._vector_store = InMemoryVectorStore()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "vector_store",
                },
            )
        return self._vector_store

    @property
    def document_chunker(self) -> DocumentChunker:
        """Return the shared document chunker instance."""
        if self._document_chunker is None:
            self._document_chunker = DocumentChunker()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "document_chunker",
                },
            )
        return self._document_chunker

    @property
    def retrieval_service(self) -> RetrievalService:
        """Return the shared retrieval service instance."""
        if self._retrieval_service is None:
            self._retrieval_service = RetrievalService(
                embedding_provider=self.embedding_provider,
                vector_store=self.vector_store,
            )
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "retrieval_service",
                },
            )
        return self._retrieval_service

    @property
    def prompt_augmentation_service(self) -> PromptAugmentationService:
        """Return the shared prompt augmentation service instance."""
        if self._prompt_augmentation_service is None:
            self._prompt_augmentation_service = PromptAugmentationService(
                prompt_manager=self.prompt_manager,
                retrieval_service=self.retrieval_service,
            )
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "prompt_augmentation_service",
                },
            )
        return self._prompt_augmentation_service

    @property
    def knowledge_indexing_service(self) -> KnowledgeIndexingService:
        """Return the shared knowledge indexing service instance."""
        if self._knowledge_indexing_service is None:
            self._knowledge_indexing_service = KnowledgeIndexingService(
                embedding_provider=self.embedding_provider,
                vector_store=self.vector_store,
                chunker=self.document_chunker,
            )
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "knowledge_indexing_service",
                },
            )
        return self._knowledge_indexing_service

    @property
    def knowledge_service(self) -> KnowledgeService:
        """Return the shared knowledge service instance."""
        if self._knowledge_service is None:
            self._knowledge_service = KnowledgeService(
                indexing_service=self.knowledge_indexing_service,
            )
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "knowledge_service",
                },
            )
        return self._knowledge_service

    @property
    def workflow_planner(self) -> WorkflowPlanner:
        """Return the shared workflow planner instance."""
        if self._workflow_planner is None:
            self._workflow_planner = WorkflowPlanner()
            logger.info(
                "application_context_dependency_created",
                extra={
                    "event": "application_context_dependency_created",
                    "dependency": "workflow_planner",
                },
            )
        return self._workflow_planner

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
                prompt_augmentation_service: PromptAugmentationService | None
                try:
                    prompt_augmentation_service = self.prompt_augmentation_service
                except Exception:
                    prompt_augmentation_service = None

                self._planning_service = PlanningService(
                    prompt_manager=self.prompt_manager,
                    ai_engine=self.ai_engine,
                    prompt_augmentation_service=prompt_augmentation_service,
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

    @property
    def workflow_orchestrator(self) -> WorkflowOrchestrator:
        """Return the shared workflow orchestrator instance.

        Returns:
            The lazily initialized ``WorkflowOrchestrator``.

        Raises:
            Exception: Re-raises orchestrator construction failures.
        """
        if self._workflow_orchestrator is None:
            try:
                self._workflow_orchestrator = WorkflowOrchestrator(
                    dispatcher=self.agent_dispatcher,
                    planner=self.workflow_planner,
                )
                logger.info(
                    "application_context_dependency_created",
                    extra={
                        "event": "application_context_dependency_created",
                        "dependency": "workflow_orchestrator",
                    },
                )
            except Exception as exc:
                logger.exception(
                    "application_context_failed",
                    extra={
                        "event": "application_context_failed",
                        "dependency": "workflow_orchestrator",
                        "error_type": type(exc).__name__,
                    },
                )
                raise
        return self._workflow_orchestrator

    @property
    def config(self) -> PlatformConfig:
        return self._config

    @property
    def session_factory(self):
        return SessionLocal

    @property
    def auth_service(self) -> AuthService:
        """Return singleton auth service backed by a scoped session."""
        if self._auth_service is None:
            session = SessionLocal()
            repository = AuthRepository(session)
            self._auth_service = AuthService(repository=repository, config=self.config)
            self._auth_service.bootstrap_defaults()
            session.close()
        return self._auth_service

    def auth_service_for_session(self, db: Session) -> AuthService:
        """Build an auth service bound to the provided session."""
        service = AuthService(repository=AuthRepository(db), config=self.config)
        service.bootstrap_defaults()
        return service

    def knowledge_repository_for_session(self, db: Session) -> KnowledgeRepository:
        return KnowledgeRepository(db)
