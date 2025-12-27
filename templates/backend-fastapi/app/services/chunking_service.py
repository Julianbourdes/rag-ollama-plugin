"""Chunking service using LangChain text splitters."""

from typing import List, Optional, Dict, Any, Literal
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
    SentenceTransformersTokenTextSplitter,
)
from app.core.config import get_settings


ChunkingStrategy = Literal[
    "recursive",      # Best for general text, respects structure
    "character",      # Simple fixed-size chunks
    "token",          # Token-based for LLM context limits
    "markdown",       # Preserves markdown structure
    "html",           # Preserves HTML structure
    "semantic"        # Sentence-level for embeddings
]


class ChunkingService:
    """Service for document chunking with multiple strategies."""

    def __init__(self):
        self.settings = get_settings()
        self._splitters: Dict[str, Any] = {}

    def get_splitter(
        self,
        strategy: ChunkingStrategy = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        **kwargs
    ):
        """Get or create a text splitter with specified configuration."""
        chunk_size = chunk_size or self.settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or self.settings.CHUNK_OVERLAP

        cache_key = f"{strategy}_{chunk_size}_{chunk_overlap}"

        if cache_key not in self._splitters:
            self._splitters[cache_key] = self._create_splitter(
                strategy, chunk_size, chunk_overlap, **kwargs
            )

        return self._splitters[cache_key]

    def _create_splitter(
        self,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
        **kwargs
    ):
        """Create a text splitter based on strategy."""
        if strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=kwargs.get("separators", [
                    "\n\n",      # Paragraphs
                    "\n",        # Lines
                    ". ",        # Sentences
                    ", ",        # Clauses
                    " ",         # Words
                    ""           # Characters
                ]),
                is_separator_regex=kwargs.get("is_separator_regex", False)
            )

        elif strategy == "character":
            return CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator=kwargs.get("separator", "\n\n"),
                length_function=len
            )

        elif strategy == "token":
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                encoding_name=kwargs.get("encoding_name", "cl100k_base")
            )

        elif strategy == "markdown":
            headers_to_split_on = kwargs.get("headers_to_split_on", [
                ("#", "header_1"),
                ("##", "header_2"),
                ("###", "header_3"),
            ])
            return MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on,
                strip_headers=kwargs.get("strip_headers", False)
            )

        elif strategy == "html":
            headers_to_split_on = kwargs.get("headers_to_split_on", [
                ("h1", "header_1"),
                ("h2", "header_2"),
                ("h3", "header_3"),
            ])
            return HTMLHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )

        elif strategy == "semantic":
            return SentenceTransformersTokenTextSplitter(
                chunk_overlap=min(chunk_overlap, 50),
                tokens_per_chunk=kwargs.get("tokens_per_chunk", 256)
            )

        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def split_text(
        self,
        text: str,
        strategy: ChunkingStrategy = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        """Split text into chunks as LangChain Documents."""
        splitter = self.get_splitter(strategy, chunk_size, chunk_overlap, **kwargs)

        # Create initial document
        doc = Document(page_content=text, metadata=metadata or {})

        # Split based on strategy type
        if strategy in ["markdown", "html"]:
            # These splitters work differently - they return docs directly from text
            chunks = splitter.split_text(text)
            # For markdown/html, chunks are already documents with metadata
            if isinstance(chunks[0], Document):
                docs = chunks
            else:
                docs = [Document(page_content=c, metadata=metadata or {}) for c in chunks]

            # Apply secondary recursive split if chunks are still too large
            if chunk_size:
                recursive_splitter = self.get_splitter("recursive", chunk_size, chunk_overlap)
                final_docs = []
                for d in docs:
                    if len(d.page_content) > chunk_size:
                        sub_chunks = recursive_splitter.split_documents([d])
                        final_docs.extend(sub_chunks)
                    else:
                        final_docs.append(d)
                docs = final_docs
        else:
            docs = splitter.split_documents([doc])

        # Add chunk index to metadata
        for i, d in enumerate(docs):
            d.metadata["chunk_index"] = i
            d.metadata["total_chunks"] = len(docs)

        return docs

    def split_documents(
        self,
        documents: List[Document],
        strategy: ChunkingStrategy = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        **kwargs
    ) -> List[Document]:
        """Split multiple documents into chunks."""
        splitter = self.get_splitter(strategy, chunk_size, chunk_overlap, **kwargs)

        if strategy in ["markdown", "html"]:
            # Process each document individually for structure-aware splitters
            all_chunks = []
            for doc in documents:
                chunks = self.split_text(
                    doc.page_content,
                    strategy=strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata=doc.metadata,
                    **kwargs
                )
                all_chunks.extend(chunks)
            return all_chunks
        else:
            return splitter.split_documents(documents)

    def estimate_chunks(
        self,
        text: str,
        strategy: ChunkingStrategy = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """Estimate chunking results without actually splitting."""
        chunk_size = chunk_size or self.settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or self.settings.CHUNK_OVERLAP

        text_length = len(text)
        effective_chunk = chunk_size - chunk_overlap

        if effective_chunk <= 0:
            estimated_chunks = 1
        else:
            estimated_chunks = max(1, (text_length - chunk_overlap) // effective_chunk)

        return {
            "text_length": text_length,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "estimated_chunks": estimated_chunks,
            "strategy": strategy
        }

    def get_optimal_strategy(
        self,
        content_type: str,
        avg_doc_length: int
    ) -> Dict[str, Any]:
        """Recommend optimal chunking strategy based on content.

        Args:
            content_type: "markdown", "html", "code", "conversation", "structured", "general"
            avg_doc_length: Average document length in characters
        """
        recommendations = {
            "markdown": {
                "strategy": "markdown",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "reason": "Preserves markdown structure and headers"
            },
            "html": {
                "strategy": "html",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "reason": "Preserves HTML structure and semantic tags"
            },
            "code": {
                "strategy": "recursive",
                "chunk_size": 1500,
                "chunk_overlap": 200,
                "separators": ["\n\n", "\ndef ", "\nclass ", "\n", " "],
                "reason": "Respects code block boundaries"
            },
            "conversation": {
                "strategy": "character",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "separator": "\n",
                "reason": "Keeps conversation turns together"
            },
            "structured": {
                "strategy": "semantic",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "reason": "Semantic boundaries for structured data"
            },
            "general": {
                "strategy": "recursive",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "reason": "Best general-purpose strategy"
            }
        }

        rec = recommendations.get(content_type, recommendations["general"])

        # Adjust based on document length
        if avg_doc_length < 500:
            rec["chunk_size"] = min(rec["chunk_size"], avg_doc_length)
            rec["chunk_overlap"] = min(rec["chunk_overlap"], rec["chunk_size"] // 5)

        return rec


# Singleton
_chunking_service: Optional[ChunkingService] = None


def get_chunking_service() -> ChunkingService:
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
