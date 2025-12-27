"""Ollama service using LangChain for LLM and embeddings."""

from typing import Optional, List, AsyncIterator
from langchain_ollama import OllamaLLM, OllamaEmbeddings, ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.callbacks import AsyncCallbackHandler
from app.core.config import get_settings
import asyncio


class StreamingCallback(AsyncCallbackHandler):
    """Callback handler for streaming tokens."""

    def __init__(self):
        self.tokens: asyncio.Queue = asyncio.Queue()
        self.done = False

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        await self.tokens.put(token)

    async def on_llm_end(self, response, **kwargs) -> None:
        self.done = True
        await self.tokens.put(None)  # Signal end


class OllamaService:
    """Service for Ollama LLM and embeddings using LangChain."""

    def __init__(self):
        self.settings = get_settings()
        self._llm: Optional[OllamaLLM] = None
        self._chat: Optional[ChatOllama] = None
        self._embeddings: Optional[OllamaEmbeddings] = None

    @property
    def llm(self) -> OllamaLLM:
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = OllamaLLM(
                base_url=self.settings.OLLAMA_BASE_URL,
                model=self.settings.OLLAMA_MODEL,
                temperature=0.7,
                num_ctx=4096,
            )
        return self._llm

    @property
    def chat(self) -> ChatOllama:
        """Get or create Chat model instance."""
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
        """Get or create embeddings instance."""
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
        """Generate response with optional streaming."""
        if stream:
            async for token in self._stream_generate(prompt, system):
                yield token
        else:
            response = await self._invoke(prompt, system)
            yield response

    async def _stream_generate(
        self,
        prompt: str,
        system: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM."""
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self.chat.astream(messages):
            if chunk.content:
                yield chunk.content

    async def _invoke(
        self,
        prompt: str,
        system: Optional[str] = None
    ) -> str:
        """Invoke LLM without streaming."""
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        response = await self.chat.ainvoke(messages)
        return response.content

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return await self.embeddings.aembed_query(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return await self.embeddings.aembed_documents(texts)

    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            # Quick embedding test
            await self.embeddings.aembed_query("test")
            return True
        except Exception:
            return False

    def get_llm_for_chain(self) -> ChatOllama:
        """Get LLM instance suitable for LangChain chains."""
        return self.chat

    def get_embeddings_for_vectorstore(self) -> OllamaEmbeddings:
        """Get embeddings instance suitable for vector stores."""
        return self.embeddings


# Singleton
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
