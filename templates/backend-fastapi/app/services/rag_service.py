"""Core RAG service using LangChain chains and retrievers."""

from typing import AsyncGenerator, List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from app.services.ollama_service import get_ollama_service
from app.services.qdrant_service import get_qdrant_service
from app.core.config import get_settings


class RAGService:
    """RAG service using LangChain chains and LCEL."""

    def __init__(self):
        self.settings = get_settings()
        self.ollama = get_ollama_service()
        self.qdrant = get_qdrant_service()

        # Initialize embeddings in qdrant service
        self.qdrant.set_embeddings(self.ollama.embeddings)

        # Prompt templates
        self._qa_prompt = self._create_qa_prompt()
        self._contextualize_prompt = self._create_contextualize_prompt()

    def _create_qa_prompt(self) -> ChatPromptTemplate:
        """Create QA prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant utile. Réponds à la question en utilisant uniquement le contexte fourni.
Si tu utilises des informations du contexte, cite la source avec [n].
Si le contexte ne contient pas la réponse, dis-le clairement.

Contexte:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}")
        ])

    def _create_contextualize_prompt(self) -> ChatPromptTemplate:
        """Create prompt for contextualizing questions with history."""
        return ChatPromptTemplate.from_messages([
            ("system", """Étant donné l'historique de conversation et une question de suivi,
reformule la question pour qu'elle soit autonome et compréhensible sans l'historique.
Ne réponds PAS à la question, reformule-la seulement si nécessaire, sinon retourne-la telle quelle."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    def get_retriever(
        self,
        search_type: str = "similarity",
        k: Optional[int] = None,
        **kwargs
    ):
        """Get configured retriever."""
        search_kwargs = {"k": k or self.settings.RETRIEVAL_K}
        search_kwargs.update(kwargs)

        return self.qdrant.get_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )

    def create_rag_chain(
        self,
        search_type: str = "similarity",
        k: Optional[int] = None,
        with_sources: bool = True
    ):
        """Create a RAG chain for question answering.

        Returns a chain that takes {"input": str} and returns answer with sources.
        """
        retriever = self.get_retriever(search_type=search_type, k=k)
        llm = self.ollama.chat

        # Create document chain
        document_chain = create_stuff_documents_chain(llm, self._qa_prompt)

        # Create retrieval chain
        rag_chain = create_retrieval_chain(retriever, document_chain)

        return rag_chain

    def create_conversational_chain(
        self,
        search_type: str = "similarity",
        k: Optional[int] = None
    ):
        """Create a conversational RAG chain with history awareness.

        Returns a chain that takes {"input": str, "chat_history": list} and returns answer.
        """
        retriever = self.get_retriever(search_type=search_type, k=k)
        llm = self.ollama.chat

        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, self._contextualize_prompt
        )

        # Create document chain
        document_chain = create_stuff_documents_chain(llm, self._qa_prompt)

        # Create full chain
        return create_retrieval_chain(history_aware_retriever, document_chain)

    async def query(
        self,
        question: str,
        stream: bool = True,
        include_sources: bool = True,
        k: Optional[int] = None,
        search_type: str = "similarity",
        chat_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[dict, None]:
        """Query RAG with streaming.

        Yields:
            - {"type": "sources", "data": [...]} if include_sources
            - {"type": "token", "data": "..."} for each token
            - {"type": "done", "data": None} when complete
        """
        retriever = self.get_retriever(search_type=search_type, k=k)

        # First, retrieve documents
        import asyncio
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            None,
            lambda: retriever.invoke(question)
        )

        # Emit sources if requested
        if include_sources:
            sources = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("score")
                }
                for doc in docs
            ]
            yield {"type": "sources", "data": sources}

        # Build context from documents
        context = self._format_docs(docs)

        # Convert chat history to messages if provided
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Create prompt with context
        prompt_messages = self._qa_prompt.format_messages(
            context=context,
            input=question,
            chat_history=messages
        )

        # Stream response
        if stream:
            async for chunk in self.ollama.chat.astream(prompt_messages):
                if chunk.content:
                    yield {"type": "token", "data": chunk.content}
        else:
            response = await self.ollama.chat.ainvoke(prompt_messages)
            yield {"type": "token", "data": response.content}

        yield {"type": "done", "data": None}

    async def query_simple(
        self,
        question: str,
        k: Optional[int] = None,
        search_type: str = "similarity"
    ) -> Dict[str, Any]:
        """Simple non-streaming query that returns complete response."""
        chain = self.create_rag_chain(search_type=search_type, k=k)

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: chain.invoke({"input": question})
        )

        return {
            "answer": result["answer"],
            "sources": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result.get("context", [])
            ]
        }

    async def search(
        self,
        query: str,
        k: int = 5,
        search_type: str = "similarity",
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search without generation."""
        docs = await self.qdrant.similarity_search(
            query=query,
            k=k,
            filter=filters
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]

    async def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5
    ) -> List[Dict]:
        """MMR search for diverse results."""
        docs = await self.qdrant.mmr_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]

    async def index_documents(
        self,
        documents: List[Document],
        collection: Optional[str] = None
    ) -> int:
        """Index LangChain documents into the vector store."""
        ids = await self.qdrant.add_documents(
            documents=documents,
            collection=collection
        )
        return len(ids)

    async def index_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        collection: Optional[str] = None
    ) -> int:
        """Index raw texts into the vector store."""
        documents = [
            Document(
                page_content=text,
                metadata=metadatas[i] if metadatas and i < len(metadatas) else {}
            )
            for i, text in enumerate(texts)
        ]

        return await self.index_documents(documents, collection)

    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents for context."""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source_info = ""
            if doc.metadata.get("source"):
                source_info = f" (source: {doc.metadata['source']})"
            formatted.append(f"[{i}]{source_info} {doc.page_content}")
        return "\n\n".join(formatted)


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
