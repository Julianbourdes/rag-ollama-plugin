"""Chat endpoints with RAG and streaming."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import json

from app.services.rag_service import RAGService, get_rag_service
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat(
    request: ChatRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Chat with RAG and SSE streaming."""

    async def generate():
        async for chunk in rag.query(
            question=request.message,
            include_sources=request.include_sources,
            filters=request.filters
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/sync", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Chat without streaming (for debugging)."""
    response_text = ""
    sources = []

    async for chunk in rag.query(
        question=request.message,
        include_sources=request.include_sources,
        stream=False
    ):
        if chunk["type"] == "sources":
            sources = chunk["data"]
        elif chunk["type"] == "token":
            response_text += chunk["data"]

    return ChatResponse(
        response=response_text,
        sources=sources,
        conversation_id=request.conversation_id
    )
