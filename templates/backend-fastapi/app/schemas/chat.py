"""Chat request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request with optional context."""
    message: str
    conversation_id: Optional[str] = None
    include_sources: bool = True
    filters: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the main features of the product?",
                "include_sources": True
            }
        }


class Source(BaseModel):
    """A source document."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Chat response with sources."""
    response: str
    sources: List[Source] = []
    conversation_id: Optional[str] = None
    created_at: datetime = None

    def __init__(self, **data):
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()
        super().__init__(**data)


class ConversationMessage(BaseModel):
    """A message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    sources: List[Source] = []
    created_at: datetime = None


class Conversation(BaseModel):
    """A conversation with message history."""
    id: str
    messages: List[ConversationMessage] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
