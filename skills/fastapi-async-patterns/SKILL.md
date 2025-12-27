---
name: fastapi-async-patterns
description: Best practices pour un backend FastAPI performant avec RAG
allowed-tools: Read, Write, Grep, Glob
---

# FastAPI Async Patterns pour RAG

Best practices pour un backend FastAPI performant avec RAG.

## Architecture de base

```
app/
├── main.py              # Point d'entrée
├── api/
│   ├── deps.py          # Dépendances injectables
│   └── routes/
│       ├── chat.py      # Endpoints chat
│       └── rag.py       # Endpoints RAG
├── core/
│   ├── config.py        # Configuration
│   └── logging.py       # Logging
├── services/
│   ├── rag_service.py
│   ├── ollama_service.py
│   └── qdrant_service.py
├── models/
│   └── conversation.py
└── schemas/
    └── chat.py
```

## Configuration

```python
# core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "RAG API"
    DEBUG: bool = False

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:7b-instruct-q4_0"
    OLLAMA_EMBEDDINGS_MODEL: str = "nomic-embed-text"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 5

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## Services Async avec LangChain

> **Note:** Les services complets sont dans `templates/backend-fastapi/app/services/`.
> Ils utilisent LangChain pour une intégration optimale.

### Ollama Service (LangChain)

```python
# services/ollama_service.py
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from typing import AsyncIterator, Optional

class OllamaService:
    """Service Ollama utilisant LangChain."""

    def __init__(self):
        self.settings = get_settings()
        self._chat: Optional[ChatOllama] = None
        self._embeddings: Optional[OllamaEmbeddings] = None

    @property
    def chat(self) -> ChatOllama:
        if self._chat is None:
            self._chat = ChatOllama(
                base_url=self.settings.OLLAMA_BASE_URL,
                model=self.settings.OLLAMA_MODEL,
                temperature=0.7,
                num_ctx=4096,
            )
        return self._chat

    @property
    def embeddings(self) -> OllamaEmbeddings:
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                base_url=self.settings.OLLAMA_BASE_URL,
                model=self.settings.OLLAMA_EMBEDDINGS_MODEL,
            )
        return self._embeddings

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Génère une réponse avec streaming LangChain."""
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        if stream:
            async for chunk in self.chat.astream(messages):
                if chunk.content:
                    yield chunk.content
        else:
            response = await self.chat.ainvoke(messages)
            yield response.content

    def get_llm_for_chain(self) -> ChatOllama:
        """Pour utilisation dans les chains LangChain."""
        return self.chat

    def get_embeddings_for_vectorstore(self) -> OllamaEmbeddings:
        """Pour utilisation avec les vector stores."""
        return self.embeddings
```

### Qdrant Service (LangChain)

```python
# services/qdrant_service.py
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import AsyncQdrantClient, QdrantClient
from typing import Optional, List, Dict, Any

class QdrantService:
    """Service Qdrant avec intégration LangChain."""

    def __init__(self):
        self.settings = get_settings()
        self._vectorstore: Optional[QdrantVectorStore] = None
        self._embeddings: Optional[Embeddings] = None

    def set_embeddings(self, embeddings: Embeddings) -> None:
        """Configure les embeddings pour le vector store."""
        self._embeddings = embeddings
        self._vectorstore = None

    def get_vectorstore(self, collection: Optional[str] = None) -> QdrantVectorStore:
        """Récupère le vector store LangChain."""
        if self._vectorstore is None:
            self._vectorstore = QdrantVectorStore(
                client=QdrantClient(
                    host=self.settings.QDRANT_HOST,
                    port=self.settings.QDRANT_PORT
                ),
                collection_name=collection or self.settings.QDRANT_COLLECTION,
                embedding=self._embeddings,
            )
        return self._vectorstore

    def get_retriever(
        self,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None
    ):
        """Récupère un retriever LangChain."""
        vectorstore = self.get_vectorstore()
        kwargs = search_kwargs or {"k": self.settings.RETRIEVAL_K}
        return vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=kwargs
        )

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Ajoute des documents au vector store."""
        vectorstore = self.get_vectorstore()
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: vectorstore.add_documents(documents)
        )
```

### RAG Service (LangChain Chains)

```python
# services/rag_service.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from typing import AsyncGenerator, Dict, Any

class RAGService:
    """Service RAG utilisant les chains LangChain."""

    def __init__(self):
        self.ollama = get_ollama_service()
        self.qdrant = get_qdrant_service()
        # Connecter embeddings au vector store
        self.qdrant.set_embeddings(self.ollama.embeddings)
        self._qa_prompt = self._create_qa_prompt()

    def _create_qa_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """Réponds à la question en utilisant le contexte fourni.
Si tu utilises des informations du contexte, cite la source avec [n].

Contexte:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}")
        ])

    def create_rag_chain(self, search_type: str = "similarity", k: int = 5):
        """Crée une chain RAG complète."""
        retriever = self.qdrant.get_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
        document_chain = create_stuff_documents_chain(
            self.ollama.chat,
            self._qa_prompt
        )
        return create_retrieval_chain(retriever, document_chain)

    async def query(
        self,
        question: str,
        stream: bool = True,
        include_sources: bool = True
    ) -> AsyncGenerator[dict, None]:
        """Query RAG avec streaming."""
        retriever = self.qdrant.get_retriever()

        # Récupérer les documents
        docs = retriever.invoke(question)

        if include_sources:
            yield {"type": "sources", "data": [
                {"content": d.page_content, "metadata": d.metadata}
                for d in docs
            ]}

        # Construire le contexte et streamer
        context = "\n\n".join(
            f"[{i}] {d.page_content}"
            for i, d in enumerate(docs, 1)
        )

        prompt_messages = self._qa_prompt.format_messages(
            context=context,
            input=question,
            chat_history=[]
        )

        async for chunk in self.ollama.chat.astream(prompt_messages):
            if chunk.content:
                yield {"type": "token", "data": chunk.content}

        yield {"type": "done", "data": None}
```

## Routes API

### Chat avec streaming

```python
# api/routes/chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from app.services.rag_service import get_rag_service, RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    include_sources: bool = True

@router.post("/")
async def chat(
    request: ChatRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Chat avec RAG et streaming SSE"""

    async def generate():
        async for chunk in rag.query(
            question=request.message,
            include_sources=request.include_sources
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

@router.post("/sync")
async def chat_sync(
    request: ChatRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Chat sans streaming (pour debug)"""
    response_text = ""
    sources = []

    async for chunk in rag.query(
        question=request.message,
        stream=False
    ):
        if chunk["type"] == "sources":
            sources = chunk["data"]
        elif chunk["type"] == "token":
            response_text += chunk["data"]

    return {
        "response": response_text,
        "sources": sources
    }
```

## Middleware et Error Handling

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

app = FastAPI(title="RAG API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logging.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {duration:.3f}s"
    )

    return response

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Include routers
from app.api.routes import chat, rag
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
```

## Gestion des connexions

```python
# api/deps.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.services.qdrant_service import get_qdrant_service
    from app.services.ollama_service import get_ollama_service

    # Préchauffer les services
    qdrant = get_qdrant_service()
    ollama = get_ollama_service()

    # Vérifier les connexions
    # await qdrant.client  # Initialise la connexion
    # await ollama.embed("warmup")  # Précharge le modèle

    yield

    # Shutdown
    # Cleanup si nécessaire

# Dans main.py
app = FastAPI(lifespan=lifespan)
```

## Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/")
@limiter.limit("10/minute")
async def chat(request: Request, data: ChatRequest):
    # ...
```
