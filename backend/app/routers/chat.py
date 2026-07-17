from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permissions
from app.db.database import get_db_session
from app.repositories.sql_repositories import ChatRepository, KnowledgeRepository, WorkflowRepository
from app.schemas.enterprise import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatService


router = APIRouter(prefix="/api/v2/projects/{project_id}/chat", tags=["Chat"])


@router.post("/messages")
async def chat_message(
    project_id: str,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("chat:write")),
):
    service = ChatService(
        chat_repository=ChatRepository(db),
        knowledge_repository=KnowledgeRepository(db),
        workflow_repository=WorkflowRepository(db),
    )

    response_text = service.respond(
        project_id=project_id,
        user_message=payload.message,
        goal=payload.goal,
        user_id=str(current_user.get("sub", "")) or None,
    )

    if not payload.stream:
        msg = ChatRepository(db).list_messages(project_id=project_id, limit=1)[-1]
        return ChatMessageResponse(
            id=msg.id,
            project_id=msg.project_id,
            role=msg.role,
            content=response_text,
            created_at=msg.created_at,
        )

    async def event_stream():
        async for chunk in service.stream_response(response_text):
            yield f"data: {chunk}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/messages", response_model=list[ChatMessageResponse])
def list_messages(
    project_id: str,
    db: Session = Depends(get_db_session),
    current_user: dict[str, object] = Depends(require_permissions("chat:read")),
) -> list[ChatMessageResponse]:
    rows = ChatRepository(db).list_messages(project_id=project_id, limit=100)
    return [
        ChatMessageResponse(
            id=row.id,
            project_id=row.project_id,
            role=row.role,
            content=row.content,
            created_at=row.created_at,
        )
        for row in rows
    ]
