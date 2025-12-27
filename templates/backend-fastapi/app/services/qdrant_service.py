"""Qdrant service using LangChain for vector store operations."""

from typing import Optional, List, Dict, Any
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models
import uuid
from app.core.config import get_settings


class QdrantService:
    """Service for Qdrant vector store using LangChain."""

    def __init__(self):
        self.settings = get_settings()
        self._async_client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None
        self._vectorstore: Optional[QdrantVectorStore] = None
        self._embeddings: Optional[Embeddings] = None

    @property
    def async_client(self) -> AsyncQdrantClient:
        """Get async Qdrant client for admin operations."""
        if self._async_client is None:
            self._async_client = AsyncQdrantClient(
                host=self.settings.QDRANT_HOST,
                port=self.settings.QDRANT_PORT
            )
        return self._async_client

    @property
    def sync_client(self) -> QdrantClient:
        """Get sync Qdrant client for LangChain integration."""
        if self._sync_client is None:
            self._sync_client = QdrantClient(
                host=self.settings.QDRANT_HOST,
                port=self.settings.QDRANT_PORT
            )
        return self._sync_client

    def set_embeddings(self, embeddings: Embeddings) -> None:
        """Set embeddings model for vector store operations."""
        self._embeddings = embeddings
        # Reset vectorstore to use new embeddings
        self._vectorstore = None

    def get_vectorstore(
        self,
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None
    ) -> QdrantVectorStore:
        """Get or create LangChain vector store instance."""
        collection = collection or self.settings.QDRANT_COLLECTION
        emb = embeddings or self._embeddings

        if emb is None:
            raise ValueError(
                "Embeddings not set. Call set_embeddings() first or pass embeddings parameter."
            )

        # Create new vectorstore if collection changed or not initialized
        if self._vectorstore is None or embeddings is not None:
            self._vectorstore = QdrantVectorStore(
                client=self.sync_client,
                collection_name=collection,
                embedding=emb,
            )

        return self._vectorstore

    def get_retriever(
        self,
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None
    ) -> VectorStoreRetriever:
        """Get LangChain retriever for use in chains.

        Args:
            collection: Qdrant collection name
            embeddings: Embeddings model to use
            search_type: "similarity", "mmr", or "similarity_score_threshold"
            search_kwargs: Additional search parameters
                - k: Number of documents to retrieve (default: 5)
                - score_threshold: Minimum score for similarity_score_threshold
                - fetch_k: Number of docs to fetch before MMR reranking
                - lambda_mult: Diversity factor for MMR (0=max diversity, 1=min)
        """
        vectorstore = self.get_vectorstore(collection, embeddings)

        kwargs = search_kwargs or {}
        if "k" not in kwargs:
            kwargs["k"] = self.settings.RETRIEVAL_K

        return vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=kwargs
        )

    async def add_documents(
        self,
        documents: List[Document],
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to vector store using LangChain."""
        vectorstore = self.get_vectorstore(collection, embeddings)

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # LangChain's add_documents is sync, run in executor
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: vectorstore.add_documents(documents, ids=ids)
        )

        return ids

    async def similarity_search(
        self,
        query: str,
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents using LangChain."""
        vectorstore = self.get_vectorstore(collection, embeddings)

        # Build Qdrant filter if provided
        qdrant_filter = None
        if filter:
            must_conditions = [
                models.FieldCondition(
                    key=f"metadata.{key}",
                    match=models.MatchValue(value=value)
                )
                for key, value in filter.items()
            ]
            qdrant_filter = models.Filter(must=must_conditions)

        # Run sync method in executor
        import asyncio
        loop = asyncio.get_event_loop()

        if qdrant_filter:
            results = await loop.run_in_executor(
                None,
                lambda: vectorstore.similarity_search(
                    query, k=k, filter=qdrant_filter
                )
            )
        else:
            results = await loop.run_in_executor(
                None,
                lambda: vectorstore.similarity_search(query, k=k)
            )

        return results

    async def similarity_search_with_score(
        self,
        query: str,
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """Search with relevance scores."""
        vectorstore = self.get_vectorstore(collection, embeddings)

        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: vectorstore.similarity_search_with_score(query, k=k)
        )

    async def mmr_search(
        self,
        query: str,
        collection: Optional[str] = None,
        embeddings: Optional[Embeddings] = None,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5
    ) -> List[Document]:
        """Maximal Marginal Relevance search for diverse results."""
        vectorstore = self.get_vectorstore(collection, embeddings)

        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: vectorstore.max_marginal_relevance_search(
                query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
            )
        )

    # --- Admin operations (using async client directly) ---

    async def ensure_collection(
        self,
        collection: Optional[str] = None,
        vector_size: int = 768
    ):
        """Ensure collection exists with proper configuration."""
        collection = collection or self.settings.QDRANT_COLLECTION

        collections = await self.async_client.get_collections()
        exists = any(c.name == collection for c in collections.collections)

        if not exists:
            await self.async_client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    async def delete_by_ids(
        self,
        ids: List[str],
        collection: Optional[str] = None
    ) -> bool:
        """Delete documents by IDs."""
        collection = collection or self.settings.QDRANT_COLLECTION

        await self.async_client.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=ids)
        )
        return True

    async def delete_by_filter(
        self,
        filter_conditions: Dict[str, Any],
        collection: Optional[str] = None
    ) -> bool:
        """Delete documents matching filter conditions."""
        collection = collection or self.settings.QDRANT_COLLECTION

        must_conditions = [
            models.FieldCondition(
                key=f"metadata.{key}",
                match=models.MatchValue(value=value)
            )
            for key, value in filter_conditions.items()
        ]

        await self.async_client.delete(
            collection_name=collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=must_conditions)
            )
        )
        return True

    async def list_collections(self) -> List[str]:
        """List all collections."""
        collections = await self.async_client.get_collections()
        return [c.name for c in collections.collections]

    async def delete_collection(self, collection_name: str):
        """Delete a collection."""
        await self.async_client.delete_collection(collection_name)
        # Reset vectorstore if it was using deleted collection
        if (self._vectorstore and
            collection_name == self.settings.QDRANT_COLLECTION):
            self._vectorstore = None

    async def get_collection_info(
        self,
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get collection statistics."""
        collection = collection or self.settings.QDRANT_COLLECTION

        info = await self.async_client.get_collection(collection)
        return {
            "name": collection,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
            "config": {
                "size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance)
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get stats for all collections."""
        collections = await self.async_client.get_collections()

        stats = {}
        for col in collections.collections:
            info = await self.async_client.get_collection(col.name)
            stats[col.name] = {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status)
            }

        return stats

    async def health_check(self) -> bool:
        """Check if Qdrant is available."""
        try:
            await self.async_client.get_collections()
            return True
        except Exception:
            return False


# Singleton
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
