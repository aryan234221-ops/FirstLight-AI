from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session
from app.repositories.sql_repositories import WorkflowRepository
from app.schemas.enterprise import WorkflowHistoryItem


router = APIRouter(prefix="/api/v2/workflow-history", tags=["Workflow History"])


@router.get("", response_model=list[WorkflowHistoryItem])
def list_workflow_history(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("history:read")),
) -> list[WorkflowHistoryItem]:
    repository = WorkflowRepository(db)
    rows = repository.list_execution_history(project_id=project_id, limit=limit)
    result: list[WorkflowHistoryItem] = []
    for row in rows:
        result.append(
            WorkflowHistoryItem(
                id=row.id,
                project_id=row.project_id,
                execution_type=row.execution_type,
                status=row.status,
                duration_ms=row.duration_ms,
                token_usage=row.token_usage,
                cost=float(row.cost),
                error_message=row.error_message,
                created_at=row.created_at,
                input=json.loads(row.input_json),
                output=json.loads(row.output_json),
            )
        )
    return result


@router.get("/{run_id}/export")
def export_workflow_json(
    run_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("history:export")),
) -> dict[str, object]:
    repository = WorkflowRepository(db)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    outputs = repository.list_outputs(run_id)
    events = repository.list_events(run_id)
    return {
        "run": {
            "id": run.id,
            "project_id": run.project_id,
            "goal": run.goal,
            "status": run.status,
            "approval_state": run.approval_state,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_ms": run.duration_ms,
            "error_message": run.error_message,
        },
        "outputs": [
            {
                "agent_name": output.agent_name,
                "goal": output.goal,
                "tasks": json.loads(output.tasks_json),
                "status": output.status,
                "latency_ms": output.latency_ms,
                "token_usage": output.token_usage,
                "cost": float(output.cost),
                "error_message": output.error_message,
                "created_at": output.created_at.isoformat(),
            }
            for output in outputs
        ],
        "events": [
            {
                "event_type": event.event_type,
                "agent_name": event.agent_name,
                "status": event.status,
                "message": event.message,
                "progress": event.progress,
                "payload": json.loads(event.payload_json),
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    }
