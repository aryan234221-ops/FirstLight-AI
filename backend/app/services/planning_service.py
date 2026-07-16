"""Planning service orchestration for AI employees.

This module coordinates prompt loading and AI generation while keeping
provider-specific concerns out of service logic.
"""

import logging

from app.engine.core.engine import AIEngine
from app.engine.prompts import PromptManager


logger = logging.getLogger(__name__)


class PlanningService:
    """Coordinate planning prompt orchestration and AI generation.

    This service validates input, loads role-specific system prompts, builds
    the final prompt payload, and delegates generation to the AI engine.
    """

    def __init__(self, prompt_manager: PromptManager, ai_engine: AIEngine) -> None:
        """Initialize the planning service dependencies.

        Args:
            prompt_manager: Prompt manager used to load system prompts.
            ai_engine: AI engine used to generate text output.
        """
        self._prompt_manager: PromptManager = prompt_manager
        self._ai_engine: AIEngine = ai_engine

    def generate_plan(self, agent_name: str, goal: str) -> str:
        """Generate a plan for an AI employee and user goal.

        Args:
            agent_name: Prompt name for the target AI employee.
            goal: User objective that the plan should address.

        Returns:
            The generated plan text.

        Raises:
            ValueError: If ``agent_name`` or ``goal`` is empty.
            FileNotFoundError: If the requested prompt file does not exist.
            Exception: Re-raises downstream orchestration failures.
        """
        normalized_agent_name = agent_name.strip()
        normalized_goal = goal.strip()

        if not normalized_agent_name:
            raise ValueError("agent_name must be a non-empty string")
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")

        logger.info(
            "planning_started",
            extra={"event": "planning_started", "agent_name": normalized_agent_name},
        )

        try:
            system_prompt = self._prompt_manager.load(prompt_name=normalized_agent_name)
            final_prompt = f"{system_prompt}\n\nUser Goal:\n{normalized_goal}"
            result = self._ai_engine.generate(final_prompt)
        except Exception as exc:
            logger.exception(
                "planning_failed",
                extra={
                    "event": "planning_failed",
                    "agent_name": normalized_agent_name,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "planning_completed",
            extra={"event": "planning_completed", "agent_name": normalized_agent_name},
        )
        return result
