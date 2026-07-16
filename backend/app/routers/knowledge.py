import logging
import json
from json import JSONDecodeError

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.application import ApplicationContext
from app.schemas.knowledge import (
    KnowledgeCreateWithTextRequest,
    KnowledgeDocumentResponse,
    KnowledgeIndexedResponse,
    KnowledgeIndexPendingResponse,
)


logger = logging.getLogger(__name__)
MAX_KNOWLEDGE_PAYLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/knowledge",
    tags=["Knowledge"],
)

context = ApplicationContext()


def get_knowledge_service():
    return context.knowledge_service


@router.post(
    "",
    response_model=KnowledgeIndexedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_202_ACCEPTED: {"model": KnowledgeIndexPendingResponse}},
)
async def create_knowledge_document(
    project_id: str,
    raw_request: Request,
) -> KnowledgeIndexedResponse | JSONResponse:
    body_bytes = await raw_request.body()
    if len(body_bytes) > MAX_KNOWLEDGE_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload exceeds 5 MB limit",
        )

    try:
        payload_obj = json.loads(body_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request encoding") from exc
    except JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload") from exc

    if not isinstance(payload_obj, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON payload must be an object")

    try:
        request = KnowledgeCreateWithTextRequest.model_validate(payload_obj)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.errors()) from exc

    try:
        created, indexed = get_knowledge_service().create_and_index(
            project_id=project_id,
            payload=request,
            text=request.text,
        )
    except ValueError as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "operation": "create",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "operation": "create",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "operation": "create",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc

    logger.info(
        "knowledge_created",
        extra={
            "event": "knowledge_created",
            "project_id": project_id,
            "document_id": created.id,
            "file_type": created.file_type,
            "file_size": created.file_size,
        },
    )

    logger.info(
        "knowledge_index_started",
        extra={
            "event": "knowledge_index_started",
            "project_id": project_id,
            "document_id": created.id,
        },
    )

    response_payload = KnowledgeDocumentResponse.from_model(created).model_dump(mode="json")
    if indexed:
        logger.info(
            "knowledge_index_completed",
            extra={
                "event": "knowledge_index_completed",
                "project_id": project_id,
                "document_id": created.id,
            },
        )
        return KnowledgeIndexedResponse(**response_payload, status="indexed")

    logger.info(
        "knowledge_index_failed",
        extra={
            "event": "knowledge_index_failed",
            "project_id": project_id,
            "document_id": created.id,
            "chunk_count": 0,
        },
    )
    response = KnowledgeIndexPendingResponse(**response_payload, status="index_pending")
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=response.model_dump(mode="json"))


@router.get("", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(project_id: str) -> list[KnowledgeDocumentResponse]:
    try:
        documents = get_knowledge_service().list(project_id=project_id)
    except ValueError as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "operation": "list",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "operation": "list",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc

    logger.info(
        "knowledge_listed",
        extra={
            "event": "knowledge_listed",
            "project_id": project_id,
            "count": len(documents),
        },
    )
    return [KnowledgeDocumentResponse.from_model(document) for document in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(project_id: str, document_id: str) -> Response:
    try:
        get_knowledge_service().delete(project_id=project_id, document_id=document_id)
    except ValueError as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "document_id": document_id,
                "operation": "delete",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except KeyError as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "document_id": document_id,
                "operation": "delete",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "knowledge_failed",
            extra={
                "event": "knowledge_failed",
                "project_id": project_id,
                "document_id": document_id,
                "operation": "delete",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from exc

    logger.info(
        "knowledge_deleted",
        extra={
            "event": "knowledge_deleted",
            "project_id": project_id,
            "document_id": document_id,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
