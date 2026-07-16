import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.application import ApplicationContext
from app.engine.core.task import Plan
from app.services.planning_service import reset_current_project_id, set_current_project_id


logger = logging.getLogger(__name__)


class WorkflowRequest(BaseModel):
    """Request payload for workflow execution."""

    goal: str
    project_id: str | None = None


router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows"],
)

context = ApplicationContext()
workflow = context.workflow_orchestrator


@router.post("/plan", response_model=dict[str, Plan])
def create_workflow_plan(request: WorkflowRequest) -> dict[str, Plan]:
    """Execute the default planning workflow."""
    request_id = None
    logger.info(
        "workflow_request_started",
        extra={
            "event": "workflow_request_started",
            "request_id": request_id,
        },
    )

    project_token = set_current_project_id(request.project_id)

    try:
        result = workflow.execute(request.goal)
    except ValueError as exc:
        logger.error(
            "workflow_request_failed",
            extra={
                "event": "workflow_request_failed",
                "request_id": request_id,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "workflow_request_failed",
            extra={
                "event": "workflow_request_failed",
                "request_id": request_id,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc
    finally:
        reset_current_project_id(project_token)

    logger.info(
        "workflow_request_completed",
        extra={
            "event": "workflow_request_completed",
            "request_id": request_id,
        },
    )
    return result
