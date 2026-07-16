"""Planning service orchestration for AI employees.

This module coordinates prompt loading and AI generation while keeping
provider-specific concerns out of service logic.
"""

import logging
from contextvars import ContextVar, Token

from app.engine.core.engine import AIEngine
from app.engine.prompts import PromptManager
from app.rag.prompt_augmentation_service import PromptAugmentationService


logger = logging.getLogger(__name__)

_CURRENT_PROJECT_ID: ContextVar[str | None] = ContextVar("current_project_id", default=None)


def set_current_project_id(project_id: str | None) -> Token[str | None]:
    """Set request-scoped project identifier for planning operations."""
    return _CURRENT_PROJECT_ID.set(project_id)


def reset_current_project_id(token: Token[str | None]) -> None:
    """Reset request-scoped project identifier using a context token."""
    _CURRENT_PROJECT_ID.reset(token)


def get_current_project_id() -> str | None:
    """Return the active request-scoped project identifier, if any."""
    return _CURRENT_PROJECT_ID.get()


class PlanningService:
    """Coordinate planning prompt orchestration and AI generation.

    This service validates input, loads role-specific system prompts, builds
    the final prompt payload, and delegates generation to the AI engine.
    """

    def __init__(
        self,
        prompt_manager: PromptManager,
        ai_engine: AIEngine,
        prompt_augmentation_service: PromptAugmentationService | None = None,
    ) -> None:
        """Initialize the planning service dependencies.

        Args:
            prompt_manager: Prompt manager used to load system prompts.
            ai_engine: AI engine used to generate text output.
            prompt_augmentation_service: Optional RAG prompt builder.
        """
        self._prompt_manager: PromptManager = prompt_manager
        self._ai_engine: AIEngine = ai_engine
        self._prompt_augmentation_service: PromptAugmentationService | None = (
            prompt_augmentation_service
        )

    def generate_plan(
        self,
        agent_name: str,
        goal: str,
        project_id: str | None = None,
    ) -> str:
        """Generate a plan for an AI employee and user goal.

        Args:
            agent_name: Prompt name for the target AI employee.
            goal: User objective that the plan should address.
            project_id: Optional project identifier used to enable RAG mode.

        Returns:
            The generated plan text.

        Raises:
            ValueError: If ``agent_name`` or ``goal`` is empty.
            FileNotFoundError: If the requested prompt file does not exist.
            Exception: Re-raises downstream orchestration failures.
        """
        normalized_agent_name = agent_name.strip()
        normalized_goal = goal.strip()
        resolved_project_id = project_id if project_id is not None else get_current_project_id()
        rag_enabled = resolved_project_id is not None
        normalized_project_id = resolved_project_id.strip() if resolved_project_id is not None else None

        if not normalized_agent_name:
            raise ValueError("agent_name must be a non-empty string")
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")
        if rag_enabled and not normalized_project_id:
            raise ValueError("project_id must be a non-empty string when RAG mode is enabled")

        logger.info(
            "planning_started",
            extra={
                "event": "planning_started",
                "agent_name": normalized_agent_name,
                "rag_enabled": rag_enabled,
            },
        )

        try:
            if rag_enabled and self._prompt_augmentation_service is not None:
                final_prompt = self._prompt_augmentation_service.build_prompt(
                    agent_name=normalized_agent_name,
                    project_id=normalized_project_id,
                    goal=normalized_goal,
                )
            else:
                system_prompt = self._prompt_manager.load(prompt_name=normalized_agent_name)
                final_prompt = f"{system_prompt}\n\nUser Goal:\n{normalized_goal}"

            result = self._ai_engine.generate(final_prompt)
        except Exception as exc:
            logger.exception(
                "planning_failed",
                extra={
                    "event": "planning_failed",
                    "agent_name": normalized_agent_name,
                    "rag_enabled": rag_enabled,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "planning_completed",
            extra={
                "event": "planning_completed",
                "agent_name": normalized_agent_name,
                "rag_enabled": rag_enabled,
            },
        )
        return result
