from __future__ import annotations

import logging

from app.engine.prompts import PromptManager
from app.rag.retrieval_service import RetrievalService
from app.rag.vector_store import DocumentChunk


logger = logging.getLogger(__name__)


class PromptAugmentationService:
    """Build augmented prompts by composing system prompt, knowledge, and user goal."""

    def __init__(self, prompt_manager: PromptManager, retrieval_service: RetrievalService) -> None:
        self._prompt_manager = prompt_manager
        self._retrieval_service = retrieval_service

    def build_prompt(self, agent_name: str, project_id: str, goal: str) -> str:
        normalized_agent_name = agent_name.strip()
        normalized_project_id = project_id.strip()
        normalized_goal = goal.strip()

        if not normalized_agent_name:
            self._log_failed(agent_name=normalized_agent_name, project_id=normalized_project_id, error_type="ValueError")
            raise ValueError("agent_name must be a non-empty string")
        if not normalized_project_id:
            self._log_failed(agent_name=normalized_agent_name, project_id=normalized_project_id, error_type="ValueError")
            raise ValueError("project_id must be a non-empty string")
        if not normalized_goal:
            self._log_failed(agent_name=normalized_agent_name, project_id=normalized_project_id, error_type="ValueError")
            raise ValueError("goal must be a non-empty string")

        logger.info(
            "prompt_build_started",
            extra={
                "event": "prompt_build_started",
                "agent_name": normalized_agent_name,
                "project_id": normalized_project_id,
            },
        )

        try:
            system_prompt = self._prompt_manager.load(normalized_agent_name)
            knowledge_chunks = self._retrieval_service.retrieve(
                project_id=normalized_project_id,
                query=normalized_goal,
            )
            final_prompt = self._compose_prompt(
                system_prompt=system_prompt,
                goal=normalized_goal,
                chunks=knowledge_chunks,
            )
        except Exception as exc:
            self._log_failed(
                agent_name=normalized_agent_name,
                project_id=normalized_project_id,
                error_type=type(exc).__name__,
            )
            raise

        logger.info(
            "prompt_build_completed",
            extra={
                "event": "prompt_build_completed",
                "agent_name": normalized_agent_name,
                "project_id": normalized_project_id,
                "knowledge_count": len(knowledge_chunks),
            },
        )
        return final_prompt

    @staticmethod
    def _compose_prompt(system_prompt: str, goal: str, chunks: list[DocumentChunk]) -> str:
        lines: list[str] = [
            system_prompt,
            "",
            "------------------------",
            "",
        ]

        if chunks:
            lines.append("<Project Knowledge>")
            lines.append("")
            for chunk in chunks:
                lines.append(chunk.text)
                lines.append("")
            lines.append("------------------------")
            lines.append("")

        lines.extend(
            [
                "<User Goal>",
                "",
                goal,
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _log_failed(agent_name: str, project_id: str, error_type: str) -> None:
        logger.error(
            "prompt_build_failed",
            extra={
                "event": "prompt_build_failed",
                "agent_name": agent_name,
                "project_id": project_id,
                "error_type": error_type,
            },
        )
