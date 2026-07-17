from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session
from app.repositories.sql_repositories import ProjectRepository


class ProjectUpsertRequest(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    settings: dict[str, object] = {}


router = APIRouter(prefix="/api/v2/projects", tags=["Projects"])


@router.get("")
def list_projects(
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("projects:read")),
) -> list[dict[str, object]]:
    rows = ProjectRepository(db).list_recent(limit=200)
    return [
        {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "settings": json.loads(row.settings_json),
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]


@router.put("/{project_id}")
def upsert_project(
    project_id: str,
    payload: ProjectUpsertRequest,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("projects:write")),
) -> dict[str, object]:
    row = ProjectRepository(db).upsert(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        settings=payload.settings,
    )
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "settings": json.loads(row.settings_json),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
