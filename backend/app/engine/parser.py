"""Response parsing utilities for AI-generated planning payloads.

This module provides provider-independent parsing of JSON responses into the
engine's Plan and Task models.
"""

import json
import logging
from json import JSONDecodeError
from typing import Any

from app.engine.core.task import Plan, Task


logger = logging.getLogger(__name__)


class ResponseParser:
    """Parse JSON planning responses into typed plan models."""

    def parse_plan(self, response: str) -> Plan:
        """Parse a JSON response string into a ``Plan``.

        Args:
            response: JSON string containing a planning payload.

        Returns:
            A validated ``Plan`` instance.

        Raises:
            ValueError: If JSON is invalid, root element is not an object,
                required fields are missing, or field types are invalid.
        """
        logger.info(
            "plan_parse_started",
            extra={"event": "plan_parse_started"},
        )

        try:
            payload: Any = json.loads(response)
        except JSONDecodeError as exc:
            logger.exception(
                "plan_parse_failed",
                extra={"event": "plan_parse_failed", "reason": "invalid_json", "error_type": type(exc).__name__},
            )
            raise ValueError("Invalid JSON response") from exc

        if not isinstance(payload, dict):
            logger.error(
                "plan_parse_failed",
                extra={"event": "plan_parse_failed", "reason": "invalid_root_type"},
            )
            raise ValueError("Invalid plan format: root JSON element must be an object")

        goal = payload.get("goal")
        if goal is None or not isinstance(goal, str):
            logger.error(
                "plan_parse_failed",
                extra={"event": "plan_parse_failed", "reason": "invalid_goal"},
            )
            raise ValueError("Invalid plan format: goal is required and must be a string")

        tasks_value = payload.get("tasks")
        if tasks_value is None or not isinstance(tasks_value, list):
            logger.error(
                "plan_parse_failed",
                extra={"event": "plan_parse_failed", "reason": "invalid_tasks"},
            )
            raise ValueError("Invalid plan format: tasks is required and must be a list")

        tasks: list[Task] = []
        for task_item in tasks_value:
            if not isinstance(task_item, dict):
                logger.error(
                    "plan_parse_failed",
                    extra={"event": "plan_parse_failed", "reason": "invalid_task_format"},
                )
                raise ValueError("Invalid task format: each task must be an object")

            title = task_item.get("title")
            if title is None or not isinstance(title, str):
                logger.error(
                    "plan_parse_failed",
                    extra={"event": "plan_parse_failed", "reason": "invalid_task_title"},
                )
                raise ValueError("Invalid task format: title is required and must be a string")

            description = task_item.get("description")
            if description is None or not isinstance(description, str):
                logger.error(
                    "plan_parse_failed",
                    extra={"event": "plan_parse_failed", "reason": "invalid_task_description"},
                )
                raise ValueError("Invalid task format: description is required and must be a string")

            tasks.append(Task(title=title, description=description))

        plan = Plan(goal=goal, tasks=tasks)

        logger.info(
            "plan_parse_completed",
            extra={"event": "plan_parse_completed", "task_count": len(tasks)},
        )
        return plan
