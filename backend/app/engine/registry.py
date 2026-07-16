"""Centralized registry for available AI agents.

This module defines the single source of truth for constructing and exposing
registered planning agents.
"""

import logging

from app.engine.agents.architect_agent import ArchitectAgent
from app.engine.agents.backend_agent import BackendAgent
from app.engine.agents.ceo_agent import CEOAgent
from app.engine.agents.database_agent import DatabaseAgent
from app.engine.agents.devops_agent import DevOpsAgent
from app.engine.agents.frontend_agent import FrontendAgent
from app.engine.agents.qa_agent import QAAgent
from app.engine.core.base_agent import BaseAgent
from app.engine.parser import ResponseParser
from app.services.planning_service import PlanningService


logger = logging.getLogger(__name__)


class AgentRegistry:
    """Construct and expose registered AI agents.

    The registry owns agent instantiation and provides normalized lookup by
    agent name.
    """

    def __init__(self, planning_service: PlanningService, response_parser: ResponseParser) -> None:
        """Initialize the registry with shared planning dependencies.

        Args:
            planning_service: Service used by planning agents.
            response_parser: Parser used by planning agents.
        """
        self._agents: dict[str, BaseAgent] = {
            CEOAgent.ROLE_NAME: CEOAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            ArchitectAgent.ROLE_NAME: ArchitectAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            BackendAgent.ROLE_NAME: BackendAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            FrontendAgent.ROLE_NAME: FrontendAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            DatabaseAgent.ROLE_NAME: DatabaseAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            QAAgent.ROLE_NAME: QAAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
            DevOpsAgent.ROLE_NAME: DevOpsAgent(
                planning_service=planning_service,
                response_parser=response_parser,
            ),
        }

        logger.info(
            "registry_initialized",
            extra={
                "event": "registry_initialized",
                "agent_count": len(self._agents),
                "agent_names": sorted(self._agents.keys()),
            },
        )

    def get(self, name: str) -> BaseAgent:
        """Return a registered agent by name.

        Args:
            name: Agent name to resolve.

        Returns:
            The resolved ``BaseAgent`` instance.

        Raises:
            ValueError: If the name is empty or unknown.
        """
        normalized_name = name.strip().lower() if isinstance(name, str) else ""
        if not normalized_name:
            logger.error(
                "registry_failed",
                extra={"event": "registry_failed", "reason": "invalid_name"},
            )
            raise ValueError("name must be a non-empty string")

        agent = self._agents.get(normalized_name)
        if agent is None:
            logger.error(
                "registry_failed",
                extra={
                    "event": "registry_failed",
                    "reason": "unknown_agent",
                    "agent_name": normalized_name,
                },
            )
            raise ValueError(f"Unknown agent: {name!r}")

        logger.info(
            "registry_lookup",
            extra={"event": "registry_lookup", "agent_name": normalized_name},
        )
        return agent

    def all(self) -> dict[str, BaseAgent]:
        """Return all registered agents.

        Returns:
            A shallow copy of the internal agent registry.
        """
        return self._agents.copy()
