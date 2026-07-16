from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, StrictStr

from app.models.knowledge import KnowledgeDocument


class KnowledgeCreateRequest(BaseModel):
    """Request payload for creating knowledge metadata."""

    name: StrictStr = Field(min_length=1)
    description: StrictStr = ""
    file_type: StrictStr = Field(min_length=1)
    file_size: int = Field(ge=0)


class KnowledgeCreateWithTextRequest(KnowledgeCreateRequest):
    """Request payload for creating and indexing knowledge metadata."""

    text: StrictStr = Field(min_length=1)


class KnowledgeDocumentResponse(BaseModel):
    """API response payload for a knowledge document."""

    id: str
    project_id: str
    name: str
    description: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    @classmethod
    def from_model(cls, document: KnowledgeDocument) -> "KnowledgeDocumentResponse":
        return cls.model_validate(document.model_dump())


class KnowledgeIndexedResponse(KnowledgeDocumentResponse):
    """Response payload when metadata creation and indexing both succeed."""

    status: Literal["indexed"]


class KnowledgeIndexPendingResponse(KnowledgeDocumentResponse):
    """Response payload when metadata is stored but indexing is deferred."""

    status: Literal["index_pending"]
