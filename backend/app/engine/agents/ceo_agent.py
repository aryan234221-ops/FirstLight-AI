import logging

from app.engine.core.base_agent import BaseAgent
from app.engine.core.task import Plan
from app.engine.parser import ResponseParser
from app.services.planning_service import PlanningService


logger = logging.getLogger(__name__)


class CEOAgent(BaseAgent):
    """CEO agent that orchestrates planning via shared services."""

    def __init__(self, planning_service: PlanningService, response_parser: ResponseParser) -> None:
        """Initialize CEO agent dependencies.

        Args:
            planning_service: Service used to generate role-based AI plans.
            response_parser: Parser used to convert AI JSON output to ``Plan``.
        """
        super().__init__("CEO AI")
        self._planning_service: PlanningService = planning_service
        self._response_parser: ResponseParser = response_parser

    def plan(self, goal: str) -> Plan:
        """Generate and parse a plan for the given goal.

        Args:
            goal: Planning objective to send to the orchestration service.

        Returns:
            A parsed ``Plan`` instance.

        Raises:
            ValueError: If ``goal`` is empty or whitespace.
            Exception: Re-raises downstream planning or parsing failures.
        """
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be a non-empty, non-whitespace string")

        logger.info(
            "ceo_plan_started",
            extra={"event": "ceo_plan_started", "agent": "ceo"},
        )

        try:
            response = self._planning_service.generate_plan(agent_name="ceo", goal=goal.strip())
            plan = self._response_parser.parse_plan(response)
        except Exception as exc:
            logger.exception(
                "ceo_plan_failed",
                extra={
                    "event": "ceo_plan_failed",
                    "agent": "ceo",
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "ceo_plan_completed",
            extra={"event": "ceo_plan_completed", "agent": "ceo"},
        )
        return plan