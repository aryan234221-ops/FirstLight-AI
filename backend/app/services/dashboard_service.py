from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AgentOutputModel,
    ExecutionHistoryModel,
    KnowledgeDocumentModel,
    WorkflowRunModel,
)
from app.repositories.sql_repositories import ActivityRepository, ProjectRepository


class DashboardService:
    def __init__(self, db: Session, project_repository: ProjectRepository, activity_repository: ActivityRepository) -> None:
        self._db = db
        self._project_repository = project_repository
        self._activity_repository = activity_repository

    def overview(self) -> dict[str, object]:
        recent_projects = [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "updated_at": project.updated_at.isoformat(),
            }
            for project in self._project_repository.list_recent(limit=8)
        ]

        running_workflows = self._db.scalar(
            select(func.count()).select_from(WorkflowRunModel).where(WorkflowRunModel.status == "running")
        )
        completed_workflows = self._db.scalar(
            select(func.count()).select_from(WorkflowRunModel).where(WorkflowRunModel.status == "completed")
        )

        agent_rows = self._db.execute(
            select(AgentOutputModel.agent_name, func.count()).group_by(AgentOutputModel.agent_name)
        ).all()
        agent_utilization = [
            {"agent": row[0], "runs": int(row[1])}
            for row in sorted(agent_rows, key=lambda item: int(item[1]), reverse=True)
        ]

        doc_count = self._db.scalar(select(func.count()).select_from(KnowledgeDocumentModel))
        doc_projects = self._db.scalar(
            select(func.count(func.distinct(KnowledgeDocumentModel.project_id))).select_from(KnowledgeDocumentModel)
        )

        success = self._db.scalar(
            select(func.count()).select_from(ExecutionHistoryModel).where(ExecutionHistoryModel.status == "completed")
        )
        total = self._db.scalar(select(func.count()).select_from(ExecutionHistoryModel))
        success_rate = (float(success) / float(total) * 100.0) if total else 100.0

        recent_activity = [
            {
                "event_type": event.event_type,
                "message": event.message,
                "status": event.status,
                "created_at": event.created_at.isoformat(),
                "project_id": event.project_id,
            }
            for event in self._activity_repository.list_recent(limit=20)
        ]

        return {
            "recent_projects": recent_projects,
            "running_workflows": int(running_workflows or 0),
            "completed_workflows": int(completed_workflows or 0),
            "agent_utilization": agent_utilization,
            "knowledge_statistics": {
                "document_count": int(doc_count or 0),
                "project_count": int(doc_projects or 0),
            },
            "execution_success_rate": round(success_rate, 2),
            "recent_activity": recent_activity,
            "system_health": {
                "status": "healthy",
                "database": "ready",
            },
        }
