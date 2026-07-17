from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session
from app.repositories.sql_repositories import ActivityRepository, ProjectRepository
from app.schemas.enterprise import DashboardOverviewResponse
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/api/v2/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("dashboard:read")),
) -> DashboardOverviewResponse:
    service = DashboardService(
        db=db,
        project_repository=ProjectRepository(db),
        activity_repository=ActivityRepository(db),
    )
    return DashboardOverviewResponse.model_validate(service.overview())
