"""RAG operations endpoints - indexing, search, management."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.services.rag_service import RAGService, get_rag_service
from app.services.qdrant_service import QdrantService, get_qdrant_service

router = APIRouter(prefix="/rag", tags=["rag"])


class IndexRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[dict]] = None
    collection: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    k: int = 5
    score_threshold: Optional[float] = None
    filters: Optional[dict] = None


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict


@router.post("/index")
async def index_documents(
    request: IndexRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Index documents into the vector store."""
    count = await rag.index_documents(
        texts=request.texts,
        metadatas=request.metadatas,
        collection=request.collection
    )
    return {"indexed": count, "collection": request.collection or "default"}


@router.post("/search", response_model=List[SearchResult])
async def search(
    request: SearchRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Search similar documents."""
    results = await rag.search(
        query=request.query,
        k=request.k,
        score_threshold=request.score_threshold,
        filters=request.filters
    )
    return results


@router.get("/collections")
async def list_collections(
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """List all collections."""
    collections = await qdrant.list_collections()
    return {"collections": collections}


@router.delete("/collection/{collection_name}")
async def delete_collection(
    collection_name: str,
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """Delete a collection."""
    await qdrant.delete_collection(collection_name)
    return {"deleted": collection_name}


@router.get("/stats")
async def get_stats(
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """Get vector store statistics."""
    stats = await qdrant.get_stats()
    return stats
