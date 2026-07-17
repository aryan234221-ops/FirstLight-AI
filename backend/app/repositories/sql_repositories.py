from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityEventModel,
    AgentOutputModel,
    ApprovalGateModel,
    ChatMessageModel,
    ExecutionHistoryModel,
    KnowledgeDocumentModel,
    ProjectModel,
    RefreshTokenModel,
    RoleModel,
    UserModel,
    UserRoleModel,
    WorkflowEventModel,
    WorkflowRunModel,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def ensure_role(self, name: str, description: str) -> RoleModel:
        role = self._db.scalar(select(RoleModel).where(RoleModel.name == name))
        if role is not None:
            return role
        role = RoleModel(name=name, description=description)
        self._db.add(role)
        self._db.commit()
        self._db.refresh(role)
        return role

    def create_user(self, user: UserModel) -> UserModel:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_user_by_username(self, username: str) -> UserModel | None:
        return self._db.scalar(select(UserModel).where(UserModel.username == username))

    def get_user_by_id(self, user_id: str) -> UserModel | None:
        return self._db.scalar(select(UserModel).where(UserModel.id == user_id))

    def assign_role(self, user_id: str, role_name: str) -> None:
        role = self._db.scalar(select(RoleModel).where(RoleModel.name == role_name))
        if role is None:
            raise ValueError(f"Unknown role {role_name}")
        existing = self._db.scalar(
            select(UserRoleModel).where(UserRoleModel.user_id == user_id, UserRoleModel.role_id == role.id)
        )
        if existing is not None:
            return
        self._db.add(UserRoleModel(user_id=user_id, role_id=role.id))
        self._db.commit()

    def get_user_role_names(self, user_id: str) -> list[str]:
        rows = self._db.execute(
            select(RoleModel.name)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user_id)
        ).all()
        return [row[0] for row in rows]

    def create_refresh_token(self, token: RefreshTokenModel) -> RefreshTokenModel:
        self._db.add(token)
        self._db.commit()
        self._db.refresh(token)
        return token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshTokenModel | None:
        return self._db.scalar(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash))

    def revoke_refresh_token(self, token_id: str) -> None:
        token = self._db.scalar(select(RefreshTokenModel).where(RefreshTokenModel.id == token_id))
        if token is None:
            return
        token.revoked = True
        self._db.add(token)
        self._db.commit()


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 10) -> list[ProjectModel]:
        rows = self._db.execute(
            select(ProjectModel).order_by(desc(ProjectModel.updated_at)).limit(limit)
        ).all()
        return [row[0] for row in rows]

    def upsert(self, project_id: str, name: str, description: str, settings: dict[str, object] | None = None) -> ProjectModel:
        project = self._db.scalar(select(ProjectModel).where(ProjectModel.id == project_id))
        if project is None:
            project = ProjectModel(id=project_id, name=name, description=description, settings_json=json.dumps(settings or {}))
        else:
            project.name = name
            project.description = description
            if settings is not None:
                project.settings_json = json.dumps(settings)
            project.updated_at = _utcnow()
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        project_id: str,
        name: str,
        description: str,
        file_type: str,
        file_size: int,
        text_content: str,
        metadata: dict[str, object] | None = None,
    ) -> KnowledgeDocumentModel:
        current_max = self._db.scalar(
            select(func.max(KnowledgeDocumentModel.version)).where(
                KnowledgeDocumentModel.project_id == project_id,
                KnowledgeDocumentModel.name == name,
            )
        )
        doc = KnowledgeDocumentModel(
            project_id=project_id,
            name=name,
            description=description,
            file_type=file_type,
            file_size=file_size,
            text_content=text_content,
            metadata_json=json.dumps(metadata or {}),
            version=(current_max or 0) + 1,
        )
        self._db.add(doc)
        self._db.commit()
        self._db.refresh(doc)
        return doc

    def list(self, project_id: str) -> list[KnowledgeDocumentModel]:
        rows = self._db.execute(
            select(KnowledgeDocumentModel)
            .where(KnowledgeDocumentModel.project_id == project_id)
            .order_by(desc(KnowledgeDocumentModel.uploaded_at))
        ).all()
        return [row[0] for row in rows]

    def get(self, project_id: str, document_id: str) -> KnowledgeDocumentModel | None:
        return self._db.scalar(
            select(KnowledgeDocumentModel).where(
                KnowledgeDocumentModel.project_id == project_id,
                KnowledgeDocumentModel.id == document_id,
            )
        )

    def delete(self, project_id: str, document_id: str) -> bool:
        doc = self.get(project_id, document_id)
        if doc is None:
            return False
        self._db.delete(doc)
        self._db.commit()
        return True


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_run(self, project_id: str, goal: str, requested_by: str | None) -> WorkflowRunModel:
        run = WorkflowRunModel(project_id=project_id, goal=goal, requested_by=requested_by)
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    def get_run(self, run_id: str) -> WorkflowRunModel | None:
        return self._db.scalar(select(WorkflowRunModel).where(WorkflowRunModel.id == run_id))

    def update_run(self, run: WorkflowRunModel) -> WorkflowRunModel:
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    def add_event(
        self,
        run_id: str,
        event_type: str,
        message: str,
        status: str = "info",
        agent_name: str | None = None,
        progress: int = 0,
        payload: dict[str, object] | None = None,
    ) -> WorkflowEventModel:
        event = WorkflowEventModel(
            workflow_run_id=run_id,
            event_type=event_type,
            message=message,
            status=status,
            agent_name=agent_name,
            progress=progress,
            payload_json=json.dumps(payload or {}),
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event

    def list_events(self, run_id: str, after: datetime | None = None) -> list[WorkflowEventModel]:
        query = select(WorkflowEventModel).where(WorkflowEventModel.workflow_run_id == run_id)
        if after is not None:
            query = query.where(WorkflowEventModel.created_at > after)
        rows = self._db.execute(query.order_by(WorkflowEventModel.created_at)).all()
        return [row[0] for row in rows]

    def add_agent_output(
        self,
        run_id: str,
        agent_name: str,
        goal: str,
        tasks: list[dict[str, str]],
        latency_ms: int,
        status: str = "completed",
        error_message: str | None = None,
    ) -> AgentOutputModel:
        output = AgentOutputModel(
            workflow_run_id=run_id,
            agent_name=agent_name,
            goal=goal,
            tasks_json=json.dumps(tasks),
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
        )
        self._db.add(output)
        self._db.commit()
        self._db.refresh(output)
        return output

    def list_outputs(self, run_id: str) -> list[AgentOutputModel]:
        rows = self._db.execute(
            select(AgentOutputModel)
            .where(AgentOutputModel.workflow_run_id == run_id)
            .order_by(AgentOutputModel.created_at)
        ).all()
        return [row[0] for row in rows]

    def list_runs(self, project_id: str | None = None, limit: int = 50) -> list[WorkflowRunModel]:
        query = select(WorkflowRunModel)
        if project_id:
            query = query.where(WorkflowRunModel.project_id == project_id)
        rows = self._db.execute(query.order_by(desc(WorkflowRunModel.started_at)).limit(limit)).all()
        return [row[0] for row in rows]

    def add_approval_gate(self, run_id: str, gate_name: str = "CEO_PLAN") -> ApprovalGateModel:
        gate = ApprovalGateModel(workflow_run_id=run_id, gate_name=gate_name)
        self._db.add(gate)
        self._db.commit()
        self._db.refresh(gate)
        return gate

    def get_latest_gate(self, run_id: str) -> ApprovalGateModel | None:
        return self._db.scalar(
            select(ApprovalGateModel)
            .where(ApprovalGateModel.workflow_run_id == run_id)
            .order_by(desc(ApprovalGateModel.created_at))
            .limit(1)
        )

    def update_gate(self, gate: ApprovalGateModel) -> ApprovalGateModel:
        self._db.add(gate)
        self._db.commit()
        self._db.refresh(gate)
        return gate

    def add_execution_history(
        self,
        project_id: str,
        execution_type: str,
        status: str,
        input_payload: dict[str, object],
        output_payload: dict[str, object],
        duration_ms: int,
        token_usage: int = 0,
        cost: float = 0.0,
        error_message: str | None = None,
    ) -> ExecutionHistoryModel:
        history = ExecutionHistoryModel(
            project_id=project_id,
            execution_type=execution_type,
            status=status,
            input_json=json.dumps(input_payload),
            output_json=json.dumps(output_payload),
            duration_ms=duration_ms,
            token_usage=token_usage,
            cost=cost,
            error_message=error_message,
        )
        self._db.add(history)
        self._db.commit()
        self._db.refresh(history)
        return history

    def list_execution_history(self, project_id: str | None = None, limit: int = 100) -> list[ExecutionHistoryModel]:
        query = select(ExecutionHistoryModel)
        if project_id:
            query = query.where(ExecutionHistoryModel.project_id == project_id)
        rows = self._db.execute(query.order_by(desc(ExecutionHistoryModel.created_at)).limit(limit)).all()
        return [row[0] for row in rows]


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_message(self, project_id: str, role: str, content: str, user_id: str | None = None, metadata: dict[str, object] | None = None) -> ChatMessageModel:
        msg = ChatMessageModel(
            project_id=project_id,
            user_id=user_id,
            role=role,
            content=content,
            metadata_json=json.dumps(metadata or {}),
        )
        self._db.add(msg)
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def list_messages(self, project_id: str, limit: int = 50) -> list[ChatMessageModel]:
        rows = self._db.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.project_id == project_id)
            .order_by(desc(ChatMessageModel.created_at))
            .limit(limit)
        ).all()
        return [row[0] for row in reversed(rows)]


class ActivityRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log(
        self,
        event_type: str,
        message: str,
        project_id: str | None = None,
        user_id: str | None = None,
        status: str = "info",
        payload: dict[str, object] | None = None,
    ) -> ActivityEventModel:
        event = ActivityEventModel(
            event_type=event_type,
            message=message,
            project_id=project_id,
            user_id=user_id,
            status=status,
            payload_json=json.dumps(payload or {}),
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event

    def list_recent(self, limit: int = 25) -> list[ActivityEventModel]:
        rows = self._db.execute(select(ActivityEventModel).order_by(desc(ActivityEventModel.created_at)).limit(limit)).all()
        return [row[0] for row in rows]
