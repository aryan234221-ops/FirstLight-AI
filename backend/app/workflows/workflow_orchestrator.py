"""Workflow orchestration for multi-agent planning flows."""

import logging

from app.engine.core.task import Plan
from app.engine.dispatcher import AgentDispatcher


logger = logging.getLogger(__name__)

CEO_STEP = "ceo"
ARCHITECT_STEP = "architect"


class WorkflowOrchestrator:
    """Coordinate multi-step planning workflows across registered agents."""

    def __init__(self, dispatcher: AgentDispatcher) -> None:
        """Initialize the workflow orchestrator.

        Args:
            dispatcher: Dispatcher used to route workflow steps to agents.
        """
        self.__dispatcher: AgentDispatcher = dispatcher

    def execute(self, goal: str) -> dict[str, Plan]:
        """Execute the CEO-to-Architect planning workflow.

        Args:
            goal: Initial workflow goal.

        Returns:
            Mapping containing typed plans for CEO and Architect stages.

        Raises:
            ValueError: If the goal is empty or whitespace-only.
            Exception: Re-raises dispatcher or downstream execution failures.
        """
        normalized_goal = goal.strip() if isinstance(goal, str) else ""
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")

        logger.info(
            "workflow_started",
            extra={"event": "workflow_started"},
        )

        try:
            logger.info(
                "workflow_step_started",
                extra={
                    "event": "workflow_step_started",
                    "step": CEO_STEP,
                    "agent_name": CEO_STEP,
                },
            )
            ceo_plan = self.__dispatcher.dispatch(
                agent_name=CEO_STEP,
                goal=normalized_goal,
            )
            logger.info(
                "workflow_step_completed",
                extra={
                    "event": "workflow_step_completed",
                    "step": CEO_STEP,
                    "agent_name": CEO_STEP,
                },
            )

            logger.info(
                "workflow_step_started",
                extra={
                    "event": "workflow_step_started",
                    "step": ARCHITECT_STEP,
                    "agent_name": ARCHITECT_STEP,
                },
            )
            architect_plan = self.__dispatcher.dispatch(
                agent_name=ARCHITECT_STEP,
                goal=ceo_plan.goal,
            )
            logger.info(
                "workflow_step_completed",
                extra={
                    "event": "workflow_step_completed",
                    "step": ARCHITECT_STEP,
                    "agent_name": ARCHITECT_STEP,
                },
            )
        except Exception as exc:
            logger.exception(
                "workflow_failed",
                extra={
                    "event": "workflow_failed",
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "workflow_completed",
            extra={"event": "workflow_completed"},
        )

        return {
            "ceo": ceo_plan,
            "architect": architect_plan,
        }
