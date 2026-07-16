"""Shared workflow context passed across multi-agent workflow steps."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from typing import Any

from app.engine.core.task import Plan


@dataclass(slots=True)
class WorkflowContext:
    """Holds shared workflow state and completed step outputs."""

    goal: str
    project_id: str | None
    workflow_id: str
    execution_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_agent_plans: dict[str, Plan] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    _allowed_agents: set[str] = field(default_factory=set, repr=False)
    _merge_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        normalized_goal = self.goal.strip() if isinstance(self.goal, str) else ""
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")
        self.goal = normalized_goal

        normalized_workflow_id = (
            self.workflow_id.strip() if isinstance(self.workflow_id, str) else ""
        )
        if not normalized_workflow_id:
            raise ValueError("workflow_id must be a non-empty string")
        self.workflow_id = normalized_workflow_id

        if self.project_id is not None and not isinstance(self.project_id, str):
            raise ValueError("project_id must be a string when provided")
        if isinstance(self.project_id, str):
            self.project_id = self.project_id.strip() or None

        normalized_execution_order = [
            name.strip().lower()
            for name in self.execution_order
            if isinstance(name, str) and name.strip()
        ]
        if len(normalized_execution_order) != len(self.execution_order):
            raise ValueError("execution_order contains invalid agent names")

        if len(normalized_execution_order) != len(set(normalized_execution_order)):
            raise ValueError("execution_order contains duplicate agent names")
        self.execution_order = normalized_execution_order

        self._allowed_agents = {
            name.strip().lower()
            for name in self._allowed_agents
            if isinstance(name, str) and name.strip()
        }
        if self._allowed_agents:
            unknown = [
                name for name in self.execution_order if name not in self._allowed_agents
            ]
            if unknown:
                raise ValueError(
                    f"execution_order contains unknown agents: {', '.join(unknown)}"
                )

    @property
    def completed_steps(self) -> list[str]:
        """Return ordered names of completed workflow steps."""
        return [
            name for name in self.execution_order if name in self.completed_agent_plans
        ]

    def add_plan(self, agent_name: str, plan: Plan) -> None:
        """Append a completed plan for an agent.

        Raises:
            ValueError: If agent name is invalid, unknown, or duplicate.
        """
        normalized_agent_name = agent_name.strip().lower() if isinstance(agent_name, str) else ""
        if not normalized_agent_name:
            raise ValueError("agent_name must be a non-empty string")

        if self._allowed_agents and normalized_agent_name not in self._allowed_agents:
            raise ValueError(f"unknown agent name: {normalized_agent_name}")

        if normalized_agent_name in self.completed_agent_plans:
            raise ValueError(f"duplicate completed plan for agent: {normalized_agent_name}")

        self.completed_agent_plans[normalized_agent_name] = plan

    async def add_plan_async(
        self,
        agent_name: str,
        plan: Plan,
        required_dependencies: set[str] | None = None,
    ) -> None:
        """Atomically append a completed plan while validating dependencies.

        Raises:
            ValueError: If completion is duplicate, unknown, or races dependencies.
        """
        normalized_agent_name = agent_name.strip().lower() if isinstance(agent_name, str) else ""
        if not normalized_agent_name:
            raise ValueError("agent_name must be a non-empty string")

        async with self._merge_lock:
            if self._allowed_agents and normalized_agent_name not in self._allowed_agents:
                raise ValueError(f"unknown agent name: {normalized_agent_name}")

            if normalized_agent_name not in self.execution_order:
                raise ValueError(f"unknown agent completion: {normalized_agent_name}")

            if normalized_agent_name in self.completed_agent_plans:
                raise ValueError(f"duplicate completed plan for agent: {normalized_agent_name}")

            missing_dependencies = [
                name
                for name in (required_dependencies or set())
                if name not in self.completed_agent_plans
            ]
            if missing_dependencies:
                raise ValueError(
                    "race-condition update detected; missing dependencies: "
                    + ", ".join(sorted(missing_dependencies))
                )

            self.completed_agent_plans[normalized_agent_name] = plan

    def build_agent_goal(self, agent_name: str) -> str:
        """Build a structured goal payload for the next agent."""
        normalized_agent_name = agent_name.strip().lower() if isinstance(agent_name, str) else ""
        if not normalized_agent_name:
            raise ValueError("agent_name must be a non-empty string")

        previous_plans: dict[str, dict[str, Any]] = {}
        for name, plan in self.completed_agent_plans.items():
            previous_plans[name] = {
                "goal": plan.goal,
                "tasks": [
                    {
                        "title": task.title,
                        "description": task.description,
                    }
                    for task in plan.tasks
                ],
            }

        payload = {
            "goal": self.goal,
            "project_id": self.project_id,
            "workflow_id": self.workflow_id,
            "execution_timestamp": self.execution_timestamp.isoformat(),
            "current_agent": normalized_agent_name,
            "completed_steps": self.completed_steps,
            "previous_agent_plans": previous_plans,
            "project_knowledge": self.metadata.get("project_knowledge", {}),
            "metadata": self.metadata,
        }

        return (
            "Workflow Context (JSON):\n"
            f"{json.dumps(payload, ensure_ascii=True)}\n\n"
            "Instructions: Use the original goal, project knowledge, and previous "
            "agent plans when creating the next plan."
        )
