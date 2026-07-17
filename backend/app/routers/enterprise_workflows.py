from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.core.application import ApplicationContext
from app.db.database import get_db_session
from app.repositories.sql_repositories import ActivityRepository, WorkflowRepository
from app.schemas.enterprise import (
    AgentOutputResponse,
    ApprovalActionRequest,
    WorkflowEventResponse,
    WorkflowRunCreateRequest,
    WorkflowRunDetailResponse,
    WorkflowRunResponse,
)
from app.services.workflow_execution_service import WorkflowExecutionService


router = APIRouter(prefix="/api/v2/workflows", tags=["Enterprise Workflows"])
context = ApplicationContext()


def _to_run_response(run) -> WorkflowRunResponse:
    return WorkflowRunResponse(
        run_id=run.id,
        project_id=run.project_id,
        goal=run.goal,
        status=run.status,
        approval_state=run.approval_state,
        current_agent=run.current_agent,
        estimated_ms=run.estimated_ms,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
    )


@router.post("/runs", response_model=dict[str, object], status_code=status.HTTP_201_CREATED)
def create_run(
    payload: WorkflowRunCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("workflows:write")),
) -> dict[str, object]:
    workflow_repository = WorkflowRepository(db)
    activity_repository = ActivityRepository(db)
    service = WorkflowExecutionService(
        planner=context.workflow_planner,
        dispatcher=context.agent_dispatcher,
        workflow_repository=workflow_repository,
        activity_repository=activity_repository,
    )

    run_id, ceo_plan = service.create_run_with_ceo_gate(
        project_id=payload.project_id,
        goal=payload.goal,
        requested_by=str(current_user.get("sub", "")) or None,
    )

    run = workflow_repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Run creation failed")

    return {
        "run": _to_run_response(run).model_dump(mode="json"),
        "ceo_plan": ceo_plan.model_dump(mode="json"),
        "approval_required": True,
    }


@router.post("/runs/{run_id}/approval", response_model=WorkflowRunResponse)
def handle_approval(
    run_id: str,
    payload: ApprovalActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("approvals:review")),
) -> WorkflowRunResponse:
    workflow_repository = WorkflowRepository(db)
    activity_repository = ActivityRepository(db)
    service = WorkflowExecutionService(
        planner=context.workflow_planner,
        dispatcher=context.agent_dispatcher,
        workflow_repository=workflow_repository,
        activity_repository=activity_repository,
    )

    run = workflow_repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    gate = workflow_repository.get_latest_gate(run_id)
    if gate is None:
        gate = workflow_repository.add_approval_gate(run_id, gate_name="CEO_PLAN")

    gate.comment = payload.comment
    gate.reviewer_id = str(current_user.get("sub", "")) or None

    if payload.action == "reject":
        gate.status = "rejected"
        run.status = "rejected"
        run.approval_state = "rejected"
        workflow_repository.update_gate(gate)
        workflow_repository.update_run(run)
        workflow_repository.add_event(run.id, "approval_rejected", "Review rejected workflow", status="failed", progress=100)
        return _to_run_response(run)

    if payload.action == "edit":
        gate.status = "edited"
        gate.edited_goal = payload.edited_goal
        run.approval_state = "edited"
        workflow_repository.update_gate(gate)
        workflow_repository.update_run(run)
        workflow_repository.add_event(run.id, "approval_edited", "Workflow goal edited by reviewer", status="info", progress=20)
        return _to_run_response(run)

    gate.status = "approved"
    run.approval_state = "approved"
    workflow_repository.update_gate(gate)
    workflow_repository.update_run(run)
    workflow_repository.add_event(run.id, "approval_approved", "Workflow approved; execution resumed", status="running", progress=20)

    edited_goal = payload.edited_goal if payload.action in {"approve", "resume"} else None

    async def _resume() -> None:
        fresh_db: Session = context.session_factory()
        try:
            fresh_workflow_repo = WorkflowRepository(fresh_db)
            fresh_activity_repo = ActivityRepository(fresh_db)
            fresh_service = WorkflowExecutionService(
                planner=context.workflow_planner,
                dispatcher=context.agent_dispatcher,
                workflow_repository=fresh_workflow_repo,
                activity_repository=fresh_activity_repo,
            )
            await fresh_service.continue_run(run_id, edited_goal=edited_goal)
        finally:
            fresh_db.close()

    background_tasks.add_task(asyncio.run, _resume())
    return _to_run_response(run)


@router.get("/runs/{run_id}", response_model=WorkflowRunDetailResponse)
def get_run_detail(
    run_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("workflows:read")),
) -> WorkflowRunDetailResponse:
    repository = WorkflowRepository(db)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    outputs = repository.list_outputs(run_id)
    events = repository.list_events(run_id)

    return WorkflowRunDetailResponse(
        **_to_run_response(run).model_dump(),
        outputs=[
            AgentOutputResponse(
                id=output.id,
                agent_name=output.agent_name,
                goal=output.goal,
                tasks=json.loads(output.tasks_json),
                status=output.status,
                latency_ms=output.latency_ms,
                token_usage=output.token_usage,
                cost=float(output.cost),
                error_message=output.error_message,
                created_at=output.created_at,
            )
            for output in outputs
        ],
        events=[
            WorkflowEventResponse(
                id=event.id,
                event_type=event.event_type,
                status=event.status,
                message=event.message,
                agent_name=event.agent_name,
                progress=event.progress,
                payload=json.loads(event.payload_json),
                created_at=event.created_at,
            )
            for event in events
        ],
    )


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("workflows:read")),
):
    repository = WorkflowRepository(db)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    async def event_stream():
        cursor = datetime.fromtimestamp(0, tz=timezone.utc)
        finished = False
        while not finished:
            poll_db: Session = context.session_factory()
            try:
                poll_repository = WorkflowRepository(poll_db)
                events = poll_repository.list_events(run_id, after=cursor)
            finally:
                poll_db.close()
            for event in events:
                payload = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "status": event.status,
                    "message": event.message,
                    "agent_name": event.agent_name,
                    "progress": event.progress,
                    "payload": json.loads(event.payload_json),
                    "created_at": event.created_at.isoformat(),
                }
                yield f"data: {json.dumps(payload, ensure_ascii=True)}\\n\\n"
                cursor = event.created_at
                if event.event_type in {"execution_completed", "execution_failed"}:
                    finished = True
            if not finished:
                await asyncio.sleep(0.5)

        yield "event: done\\ndata: [DONE]\\n\\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/runs", response_model=list[WorkflowRunResponse])
def list_runs(
    project_id: str | None = None,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("workflows:read")),
) -> list[WorkflowRunResponse]:
    repository = WorkflowRepository(db)
    runs = repository.list_runs(project_id=project_id, limit=100)
    return [_to_run_response(run) for run in runs]


@router.post("/runs/{run_id}/replay", response_model=WorkflowRunResponse)
def replay_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("workflows:write")),
) -> WorkflowRunResponse:
    repository = WorkflowRepository(db)
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    new_run = repository.create_run(project_id=run.project_id, goal=run.goal, requested_by=str(current_user.get("sub", "")) or None)
    repository.add_approval_gate(new_run.id, gate_name="CEO_PLAN")
    repository.add_event(new_run.id, "replay_created", "Replay created from previous run", status="info")

    return _to_run_response(new_run)
