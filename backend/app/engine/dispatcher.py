"""Agent dispatching utilities for planning workflows.

This module provides a provider-independent dispatcher that routes planning
requests to registered AI agents by name.
"""

import logging

from app.engine.core.base_agent import BaseAgent
from app.engine.core.task import Plan


logger = logging.getLogger(__name__)


class AgentDispatcher:
    """Dispatch planning requests to registered agents.

    The dispatcher validates request input, resolves a registered agent by
    normalized name, and delegates planning execution to that agent.
    """

    def __init__(self, agents: dict[str, BaseAgent]) -> None:
        """Initialize the dispatcher with an agent registry.

        Args:
            agents: Mapping of agent names to agent instances.
        """
        self._agents: dict[str, BaseAgent] = {
            name.strip().lower(): agent for name, agent in agents.items()
        }

    def dispatch(self, agent_name: str, goal: str) -> Plan:
        """Dispatch a planning request to the selected agent.

        Args:
            agent_name: Name of the target agent.
            goal: User goal to pass to the agent.

        Returns:
            The ``Plan`` returned by ``agent.plan(goal)``.

        Raises:
            ValueError: If input is invalid or the agent is unknown.
            Exception: Re-raises agent planning failures.
        """
        normalized_agent_name = agent_name.strip().lower()

        if not normalized_agent_name:
            logger.error(
                "dispatcher_failed",
                extra={"event": "dispatcher_failed", "reason": "invalid_agent_name"},
            )
            raise ValueError("agent_name must be a non-empty string")

        if not isinstance(goal, str) or not goal.strip():
            logger.error(
                "dispatcher_failed",
                extra={"event": "dispatcher_failed", "reason": "invalid_goal"},
            )
            raise ValueError("goal must be a non-empty string")

        agent = self._agents.get(normalized_agent_name)
        if agent is None:
            logger.error(
                "dispatcher_failed",
                extra={
                    "event": "dispatcher_failed",
                    "reason": "unknown_agent",
                    "agent_name": normalized_agent_name,
                },
            )
            raise ValueError(f"Unknown agent: {agent_name!r}")

        logger.info(
            "dispatcher_started",
            extra={"event": "dispatcher_started", "agent_name": normalized_agent_name},
        )

        try:
            plan = agent.plan(goal)
        except Exception as exc:
            logger.exception(
                "dispatcher_failed",
                extra={
                    "event": "dispatcher_failed",
                    "reason": "agent_plan_failed",
                    "agent_name": normalized_agent_name,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "dispatcher_completed",
            extra={"event": "dispatcher_completed", "agent_name": normalized_agent_name},
        )
        return plan
