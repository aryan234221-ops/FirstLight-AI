from __future__ import annotations

import json
from typing import Protocol
from uuid import uuid4

from app.db.database import SessionLocal
from app.db.models import KnowledgeDocumentModel
from app.models.knowledge import KnowledgeDocument
from app.rag.knowledge_indexing_service import KnowledgeIndexingService
from app.schemas.knowledge import KnowledgeCreateRequest


class KnowledgeRepository(Protocol):
    """Persistence boundary for knowledge documents."""

    def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        ...

    def list(self, project_id: str) -> list[KnowledgeDocument]:
        ...

    def delete(self, project_id: str, document_id: str) -> bool:
        ...


class InMemoryKnowledgeRepository:
    """In-memory implementation used until a database repository is introduced."""

    def __init__(self) -> None:
        self._documents_by_project: dict[str, dict[str, KnowledgeDocument]] = {}

    def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        project_documents = self._documents_by_project.setdefault(document.project_id, {})
        project_documents[document.id] = document
        return document

    def list(self, project_id: str) -> list[KnowledgeDocument]:
        project_documents = self._documents_by_project.get(project_id, {})
        return sorted(project_documents.values(), key=lambda value: value.uploaded_at, reverse=True)

    def delete(self, project_id: str, document_id: str) -> bool:
        project_documents = self._documents_by_project.get(project_id)
        if not project_documents:
            return False

        removed = project_documents.pop(document_id, None)
        if not project_documents:
            self._documents_by_project.pop(project_id, None)
        return removed is not None


class SqliteKnowledgeRepository:
    """SQLite-backed implementation for durable knowledge metadata storage."""

    def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        db = SessionLocal()
        try:
            row = KnowledgeDocumentModel(
                id=document.id,
                project_id=document.project_id,
                name=document.name,
                description=document.description,
                file_type=document.file_type,
                file_size=document.file_size,
                metadata_json=json.dumps({"source": "v1"}),
                text_content="",
                version=1,
                status="indexed",
                uploaded_at=document.uploaded_at,
            )
            db.add(row)
            db.commit()
            return document
        finally:
            db.close()

    def list(self, project_id: str) -> list[KnowledgeDocument]:
        db = SessionLocal()
        try:
            rows = (
                db.query(KnowledgeDocumentModel)
                .filter(KnowledgeDocumentModel.project_id == project_id)
                .order_by(KnowledgeDocumentModel.uploaded_at.desc())
                .all()
            )
            return [
                KnowledgeDocument(
                    id=row.id,
                    project_id=row.project_id,
                    name=row.name,
                    description=row.description,
                    file_type=row.file_type,
                    file_size=row.file_size,
                    uploaded_at=row.uploaded_at,
                )
                for row in rows
            ]
        finally:
            db.close()

    def delete(self, project_id: str, document_id: str) -> bool:
        db = SessionLocal()
        try:
            row = (
                db.query(KnowledgeDocumentModel)
                .filter(
                    KnowledgeDocumentModel.project_id == project_id,
                    KnowledgeDocumentModel.id == document_id,
                )
                .first()
            )
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()


class KnowledgeService:
    """Orchestrates knowledge document metadata CRUD operations."""

    def __init__(
        self,
        repository: KnowledgeRepository | None = None,
        indexing_service: KnowledgeIndexingService | None = None,
    ) -> None:
        self._repository: KnowledgeRepository = repository or SqliteKnowledgeRepository()
        self._indexing_service: KnowledgeIndexingService | None = indexing_service

    def create(self, project_id: str, payload: KnowledgeCreateRequest) -> KnowledgeDocument:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            raise ValueError("project_id must be a non-empty string")

        document = KnowledgeDocument(
            id=str(uuid4()),
            project_id=normalized_project_id,
            name=payload.name.strip(),
            description=payload.description.strip(),
            file_type=payload.file_type.strip().lower(),
            file_size=payload.file_size,
            uploaded_at=KnowledgeDocument.now_utc(),
        )

        return self._repository.create(document)

    def create_and_index(
        self,
        project_id: str,
        payload: KnowledgeCreateRequest,
        text: str,
    ) -> tuple[KnowledgeDocument, bool]:
        """Create metadata and trigger automatic indexing when configured.

        Returns:
            Tuple of (created_document, indexing_succeeded).
        """
        created = self.create(project_id=project_id, payload=payload)

        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("text must be a non-empty string")

        if self._indexing_service is None:
            return created, False

        try:
            self._indexing_service.index_document(
                project_id=created.project_id,
                document_id=created.id,
                text=normalized_text,
            )
        except Exception:
            return created, False

        return created, True

    def list(self, project_id: str) -> list[KnowledgeDocument]:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            raise ValueError("project_id must be a non-empty string")

        return self._repository.list(normalized_project_id)

    def delete(self, project_id: str, document_id: str) -> None:
        normalized_project_id = project_id.strip()
        normalized_document_id = document_id.strip()
        if not normalized_project_id:
            raise ValueError("project_id must be a non-empty string")
        if not normalized_document_id:
            raise ValueError("document_id must be a non-empty string")

        deleted = self._repository.delete(normalized_project_id, normalized_document_id)
        if not deleted:
            raise KeyError(f"Knowledge document '{normalized_document_id}' was not found")
