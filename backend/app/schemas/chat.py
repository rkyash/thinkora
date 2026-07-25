import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (user, assistant, system)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., description="Chat history including the latest user message"
    )
    model: str | None = Field(None, description="Optional LLM model override")


class ChatResponse(BaseModel):
    """Fallback schema for non-streaming response if needed"""

    message: ChatMessage
    citations: list[dict] = []


class ChatSessionCreate(BaseModel):
    title: str = "New Chat"


class ChatSessionResponse(BaseModel):
    id: str
    notebook_id: str
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
