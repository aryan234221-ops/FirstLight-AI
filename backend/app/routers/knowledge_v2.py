from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session
from app.repositories.sql_repositories import KnowledgeRepository
from app.schemas.enterprise import KnowledgeSearchRequest, KnowledgeUploadResponse


router = APIRouter(prefix="/api/v2/projects/{project_id}/knowledge", tags=["Knowledge V2"])

SUPPORTED_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/webp",
}


def _extract_text(content_type: str, raw: bytes) -> tuple[str, dict[str, object]]:
    if content_type in {"text/plain", "text/markdown"}:
        text = raw.decode("utf-8", errors="ignore")
        return text, {"parser": "utf8"}
    if content_type == "text/csv":
        decoded = raw.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(decoded))
        rows = [", ".join(row) for row in reader]
        return "\n".join(rows), {"parser": "csv", "rows": len(rows)}
    if content_type == "application/pdf":
        return "PDF extraction placeholder. OCR/Parser can be plugged in.", {"parser": "pdf-placeholder"}
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "DOCX extraction placeholder. Parser can be plugged in.", {"parser": "docx-placeholder"}
    if content_type.startswith("image/"):
        return "Image OCR placeholder. OCR provider can be plugged in.", {"parser": "image-ocr-placeholder"}
    return "", {"parser": "unsupported"}


@router.post("/upload", response_model=KnowledgeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("knowledge:write")),
) -> KnowledgeUploadResponse:
    content_type = file.content_type or "application/octet-stream"
    if content_type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {content_type}")

    raw = await file.read()
    text, metadata = _extract_text(content_type, raw)

    repository = KnowledgeRepository(db)
    created = repository.create(
        project_id=project_id,
        name=file.filename or "upload.bin",
        description=f"Uploaded by {current_user.get('username', 'unknown')}",
        file_type=content_type,
        file_size=len(raw),
        text_content=text,
        metadata={
            **metadata,
            "uploaded_by": current_user.get("username"),
            "file_name": file.filename,
        },
    )

    return KnowledgeUploadResponse(
        id=created.id,
        project_id=created.project_id,
        name=created.name,
        description=created.description,
        file_type=created.file_type,
        file_size=created.file_size,
        version=created.version,
        status=created.status,
        metadata=json.loads(created.metadata_json),
        uploaded_at=created.uploaded_at,
    )


@router.get("", response_model=list[KnowledgeUploadResponse])
def list_knowledge(
    project_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("knowledge:read")),
) -> list[KnowledgeUploadResponse]:
    rows = KnowledgeRepository(db).list(project_id)
    return [
        KnowledgeUploadResponse(
            id=row.id,
            project_id=row.project_id,
            name=row.name,
            description=row.description,
            file_type=row.file_type,
            file_size=row.file_size,
            version=row.version,
            status=row.status,
            metadata=json.loads(row.metadata_json),
            uploaded_at=row.uploaded_at,
        )
        for row in rows
    ]


@router.post("/search")
def search_knowledge(
    project_id: str,
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("knowledge:read")),
) -> dict[str, object]:
    rows = KnowledgeRepository(db).list(project_id)
    query = payload.query.lower()
    matches = []
    for row in rows:
        text = row.text_content.lower()
        if query in text or query in row.name.lower() or query in row.description.lower():
            matches.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "version": row.version,
                    "snippet": row.text_content[:220],
                    "uploaded_at": row.uploaded_at.isoformat(),
                }
            )
        if len(matches) >= payload.top_k:
            break

    return {"results": matches, "count": len(matches)}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("knowledge:write")),
) -> None:
    deleted = KnowledgeRepository(db).delete(project_id, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.post("/{document_id}/reindex")
def reindex_knowledge(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("knowledge:write")),
) -> dict[str, object]:
    repository = KnowledgeRepository(db)
    row = repository.get(project_id, document_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    row.status = "indexed"
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status, "updated_at": row.updated_at.isoformat()}
