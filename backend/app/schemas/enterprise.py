from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.engine.core.task import Plan


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    user: dict[str, object]


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class WorkflowRunCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    goal: str = Field(min_length=1)


class WorkflowRunResponse(BaseModel):
    run_id: str
    project_id: str
    goal: str
    status: str
    approval_state: str
    current_agent: str | None
    estimated_ms: int
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int
    error_message: str | None


class ApprovalActionRequest(BaseModel):
    action: Literal["approve", "reject", "edit", "resume"]
    comment: str = ""
    edited_goal: str | None = None


class WorkflowEventResponse(BaseModel):
    id: str
    event_type: str
    status: str
    message: str
    agent_name: str | None
    progress: int
    payload: dict[str, object]
    created_at: datetime


class AgentOutputResponse(BaseModel):
    id: str
    agent_name: str
    goal: str
    tasks: list[dict[str, str]]
    status: str
    latency_ms: int
    token_usage: int
    cost: float
    error_message: str | None
    created_at: datetime


class WorkflowRunDetailResponse(WorkflowRunResponse):
    outputs: list[AgentOutputResponse]
    events: list[WorkflowEventResponse]


class DashboardOverviewResponse(BaseModel):
    recent_projects: list[dict[str, object]]
    running_workflows: int
    completed_workflows: int
    agent_utilization: list[dict[str, object]]
    knowledge_statistics: dict[str, object]
    execution_success_rate: float
    recent_activity: list[dict[str, object]]
    system_health: dict[str, object]


class KnowledgeUploadResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    file_type: str
    file_size: int
    version: int
    status: str
    metadata: dict[str, object]
    uploaded_at: datetime


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    goal: str | None = None
    stream: bool = True


class ChatMessageResponse(BaseModel):
    id: str
    project_id: str
    role: str
    content: str
    created_at: datetime


class WorkflowHistoryItem(BaseModel):
    id: str
    project_id: str
    execution_type: str
    status: str
    duration_ms: int
    token_usage: int
    cost: float
    error_message: str | None
    created_at: datetime
    input: dict[str, object]
    output: dict[str, object]
