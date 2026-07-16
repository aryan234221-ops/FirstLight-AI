"""Dynamic workflow planning for adaptive multi-agent execution."""

from __future__ import annotations

import re


SUPPORTED_WORKFLOW_AGENTS: tuple[str, ...] = (
    "ceo",
    "architect",
    "backend",
    "frontend",
    "database",
    "qa",
    "devops",
)


class WorkflowPlanner:
    """Decide workflow agent order from a goal description."""

    def plan(self, goal: str) -> list[str]:
        """Plan agent execution order for a goal.

        Args:
            goal: User-provided workflow goal.

        Returns:
            Ordered list of agent names.

        Raises:
            ValueError: If goal is empty or whitespace-only.
        """
        normalized_goal = goal.strip() if isinstance(goal, str) else ""
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")

        lower_goal = normalized_goal.lower()
        ordered: list[str] = ["ceo"]

        if self._matches_deployment(lower_goal):
            ordered.extend(["architect", "devops"])
            return self._dedupe_preserve_order(ordered)

        if self._matches_frontend(lower_goal):
            ordered.extend(["architect", "frontend", "qa"])
            return self._dedupe_preserve_order(ordered)

        if self._matches_database(lower_goal):
            ordered.extend(["database", "backend", "qa"])
            return self._dedupe_preserve_order(ordered)

        if self._matches_backend_api(lower_goal):
            ordered.extend(["architect", "backend", "database", "qa"])
            return self._dedupe_preserve_order(ordered)

        ordered.extend(["architect", "qa"])
        return self._dedupe_preserve_order(ordered)

    @staticmethod
    def supported_agents() -> set[str]:
        """Return supported workflow agent names."""
        return set(SUPPORTED_WORKFLOW_AGENTS)

    @staticmethod
    def _dedupe_preserve_order(agent_names: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for name in agent_names:
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        return ordered

    @staticmethod
    def _matches_backend_api(goal: str) -> bool:
        keywords = (
            "rest api",
            "api",
            "endpoint",
            "backend",
            "fastapi",
            "laravel",
            "authentication",
            "authorization",
            "service",
        )
        return WorkflowPlanner._contains_keyword(goal, keywords)

    @staticmethod
    def _matches_frontend(goal: str) -> bool:
        keywords = (
            "frontend",
            "ui",
            "ux",
            "login page",
            "react",
            "next.js",
            "nextjs",
            "tailwind",
            "shadcn",
            "accessibility",
            "responsive",
        )
        return WorkflowPlanner._contains_keyword(goal, keywords)

    @staticmethod
    def _matches_deployment(goal: str) -> bool:
        keywords = (
            "deploy",
            "deployment",
            "production",
            "devops",
            "docker",
            "kubernetes",
            "ci/cd",
            "pipeline",
            "infrastructure",
            "monitoring",
            "reverse proxy",
            "nginx",
        )
        return WorkflowPlanner._contains_keyword(goal, keywords)

    @staticmethod
    def _matches_database(goal: str) -> bool:
        keywords = (
            "database",
            "schema",
            "sql",
            "migration",
            "index",
            "query",
            "normalize",
            "normalization",
            "postgresql",
            "mysql",
            "sqlite",
            "sql server",
        )
        return WorkflowPlanner._contains_keyword(goal, keywords)

    @staticmethod
    def _contains_keyword(goal: str, keywords: tuple[str, ...]) -> bool:
        for keyword in keywords:
            normalized_keyword = keyword.strip().lower()
            if not normalized_keyword:
                continue

            if re.search(rf"\b{re.escape(normalized_keyword)}\b", goal):
                return True

        return False
