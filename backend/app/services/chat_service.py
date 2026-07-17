from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.repositories.sql_repositories import ChatRepository, KnowledgeRepository, WorkflowRepository


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        knowledge_repository: KnowledgeRepository,
        workflow_repository: WorkflowRepository,
    ) -> None:
        self._chat_repository = chat_repository
        self._knowledge_repository = knowledge_repository
        self._workflow_repository = workflow_repository

    def _build_context_snippet(self, project_id: str, goal: str | None) -> str:
        docs = self._knowledge_repository.list(project_id)
        recent_runs = self._workflow_repository.list_runs(project_id=project_id, limit=5)
        recent_messages = self._chat_repository.list_messages(project_id, limit=8)

        knowledge_titles = ", ".join(doc.name for doc in docs[:5]) if docs else "none"
        run_statuses = ", ".join(run.status for run in recent_runs[:5]) if recent_runs else "none"
        conversation = " | ".join(message.content[:80] for message in recent_messages[-4:]) if recent_messages else "none"

        goal_text = goal.strip() if isinstance(goal, str) and goal.strip() else "No explicit goal"
        return (
            f"Project Context: {project_id}. "
            f"Current Goal: {goal_text}. "
            f"Knowledge: {knowledge_titles}. "
            f"Recent workflow statuses: {run_statuses}. "
            f"Previous conversation: {conversation}."
        )

    def respond(self, project_id: str, user_message: str, goal: str | None = None, user_id: str | None = None) -> str:
        self._chat_repository.add_message(project_id=project_id, role="user", content=user_message, user_id=user_id)
        context_text = self._build_context_snippet(project_id, goal)
        response = (
            "AI Workspace Response:\n"
            f"{context_text}\n\n"
            f"Requested: {user_message}\n"
            "Recommended next steps:\n"
            "1. Validate dependencies and approvals.\n"
            "2. Run targeted workflow and monitor live timeline.\n"
            "3. Review execution history for cost and token metrics."
        )
        self._chat_repository.add_message(project_id=project_id, role="assistant", content=response, user_id=user_id)
        return response

    async def stream_response(self, text: str) -> AsyncIterator[str]:
        words = text.split(" ")
        for index in range(0, len(words), 5):
            chunk = " ".join(words[index : index + 5])
            yield chunk + " "
            await asyncio.sleep(0.03)
