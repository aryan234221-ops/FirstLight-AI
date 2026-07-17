from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session


STARTED_AT = datetime.now(timezone.utc)
router = APIRouter(prefix="/api/v2/observability", tags=["Observability"])


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.now(timezone.utc) - STARTED_AT).total_seconds()),
    }


@router.get("/readiness")
def readiness(db: Session = Depends(get_db_session)) -> dict[str, object]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@router.get("/metrics")
def metrics(
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("dashboard:read")),
) -> dict[str, object]:
    return {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "labels": {
            "service": "firstlight-backend",
            "version": "2.0.0-enterprise",
        },
    }
