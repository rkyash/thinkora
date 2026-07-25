import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_for_sse, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.chat_session import ChatSession
from app.models.message import ChatMessage
from app.models.notebook import Notebook
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories import notebook_repo, workspace_repo
from app.repositories.chat_session import ChatSessionRepo
from app.repositories.message import MessageRepo
from app.schemas.chat import ChatMessageResponse, ChatSessionCreate, ChatSessionResponse
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiError, ApiResponse, PaginatedResponse
from app.services.rag import RAGService

router = APIRouter(tags=["Chat"])
session_repo = ChatSessionRepo()
message_repo = MessageRepo()


async def _verify_workspace_ownership(
    workspace_id: str, db: AsyncSession, current_user: User
) -> Workspace:
    """Verify the workspace exists and is owned by the current user."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")
    return workspace


async def _verify_notebook_access(
    notebook_id: str, db: AsyncSession, current_user: User
) -> Notebook:
    """Verify notebook access via workspace ownership."""
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


@router.get(
    "/notebooks/{notebook_id}/chat/sessions",
    response_model=PaginatedResponse[ChatSessionResponse],
)
async def list_chat_sessions(
    notebook_id: UUID,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List chat sessions in a notebook with pagination."""
    notebook = await _verify_notebook_access(str(notebook_id), db, current_user)
    sessions = await session_repo.list_by_notebook(
        db, str(notebook_id), offset=offset_params.offset, limit=offset_params.limit
    )
    total = await session_repo.count(db, notebook_id=str(notebook_id))
    return {
        "success": True,
        "data": [ChatSessionResponse.model_validate(s) for s in sessions],
        "total": total,
        "offset": offset_params.offset,
        "limit": offset_params.limit,
        "has_next": (offset_params.offset + offset_params.limit) < total,
    }


@router.post(
    "/notebooks/{notebook_id}/chat/sessions",
    response_model=ApiResponse[ChatSessionResponse],
)
async def create_chat_session(
    notebook_id: UUID,
    payload: ChatSessionCreate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session in a notebook."""
    notebook = await _verify_notebook_access(str(notebook_id), db, current_user)
    title = (payload.title if payload else None) or "New Chat"
    try:
        session = await session_repo.create(
            db, {"notebook_id": str(notebook_id), "title": title}
        )
        return ApiResponse(success=True, data=ChatSessionResponse.model_validate(session), message="Chat session created")

    except Exception as e:
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail=f"Failed to create chat session: {str(e)}",
        # )
        raise ApiError(success=False, error=f"Failed to create chat session: {str(e)}", code="chat_session_creation_failed")

@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=PaginatedResponse[ChatMessageResponse],
)
async def list_messages(
    session_id: str,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages in a chat session with pagination."""
    session = await session_repo.get_or_404(db, session_id)
    notebook = await _verify_notebook_access(str(session.notebook_id), db, current_user)
    messages = await message_repo.list_by_session(
        db, session_id, offset=offset_params.offset, limit=offset_params.limit
    )
    total = await message_repo.count(db, session_id=session_id)
    return {
        "success": True,
        "data": [ChatMessageResponse.model_validate(m) for m in messages],
        "total": total,
        "offset": offset_params.offset,
        "limit": offset_params.limit,
        "has_next": (offset_params.offset + offset_params.limit) < total,
    }


@router.delete(
    "/chat/sessions/{session_id}",
    response_model=ApiResponse[None],
)
async def delete_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session."""
    session = await session_repo.get_or_404(db, session_id)
    notebook = await _verify_notebook_access(str(session.notebook_id), db, current_user)
    await session_repo.delete(db, session_id)
    return {
        "success": True,
        "data": None,
        "message": "Chat session deleted",
    }


@router.get(
    "/chat/sessions/{session_id}/ask",
    summary="Stream AI response for a question",
)
async def stream_ask(
    session_id: str,
    question: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_for_sse),
):
    """Stream AI response for a question in a chat session."""
    session = await session_repo.get_or_404(db, session_id)
    notebook = await _verify_notebook_access(str(session.notebook_id), db, current_user)
    notebook_id = str(session.notebook_id)

    # Save user message
    user_msg = await message_repo.create(
        db,
        {
            "session_id": session_id,
            "role": "user",
            "content": question,
        }
    )

    # Get bounded history — last 20 messages, excluding the user message we just saved
    history = await message_repo.get_recent(db, session_id, k=21)
    # Drop the just-inserted user message to avoid duplication
    history = [m for m in history if m.id != user_msg.id]
    # RAGService.stream_chat expects messages[-1] to be the current user query
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": question})

    rag_service = RAGService(db)

    async def event_generator():
        full_response = ""
        try:
            async for chunk_str in rag_service.stream_chat(notebook_id, messages):
                data = json.loads(chunk_str)
                if data.get("type") == "chunk":
                    chunk_text = data["data"]
                    full_response += chunk_text
                    yield f"event: chunk\ndata: {json.dumps(chunk_text)}\n\n"
                elif data.get("type") == "citations":
                    yield f"event: citations\ndata: {json.dumps(data['data'])}\n\n"
                elif data.get("type") == "error":
                    yield f"event: error\ndata: {json.dumps(data['data'])}\n\n"

            yield f"event: done\ndata: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
        finally:
            if full_response.strip():
                await message_repo.create(
                    db,
                    {
                        "session_id": session_id,
                        "role": "assistant",
                        "content": full_response,
                    },
                )

    return StreamingResponse(event_generator(), media_type="text/event-stream")