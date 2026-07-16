from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """Domain model for project knowledge metadata."""

    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    file_type: str = Field(min_length=1)
    file_size: int = Field(ge=0)
    uploaded_at: datetime

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
