"""
ShopZone AI Package
Provides modular LLM providers, fallback orchestration, RAG indexing,
and SSE chat streaming grounded in the ShopZone product catalogue.
"""
from .chat_orchestrator import AIChatOrchestrator, sse_event
from .citations import format_citations_from_retrieved
from .embeddings import (
    BaseEmbeddingProvider,
    GeminiEmbeddingProvider,
    LocalHashEmbeddingProvider,
    MistralEmbeddingProvider,
    get_embedding_provider,
)
from .fallback_manager import AIFallbackManager, AllProvidersFailedError
from .prompts import (
    SHOPZONE_SYSTEM_PROMPT,
    build_augmented_prompt,
    sanitize_user_input,
)
from .provider_factory import create_llm_provider
from .provider_interface import (
    AIProviderAuthError,
    AIProviderError,
    AIProviderInvalidRequestError,
    AIProviderRateLimitError,
    AIProviderServerError,
    AIProviderTimeoutError,
    GeminiProvider,
    GroqProvider,
    LLMProviderInterface,
    MistralProvider,
    OpenAICompatibleProvider,
)
from .rag_indexer import CatalogIndexer
from .vector_store import ChromaVectorStore

__all__ = [
    "LLMProviderInterface",
    "OpenAICompatibleProvider",
    "GroqProvider",
    "MistralProvider",
    "GeminiProvider",
    "AIProviderError",
    "AIProviderTimeoutError",
    "AIProviderRateLimitError",
    "AIProviderAuthError",
    "AIProviderServerError",
    "AIProviderInvalidRequestError",
    "create_llm_provider",
    "AIFallbackManager",
    "AllProvidersFailedError",
    "BaseEmbeddingProvider",
    "LocalHashEmbeddingProvider",
    "GeminiEmbeddingProvider",
    "MistralEmbeddingProvider",
    "get_embedding_provider",
    "ChromaVectorStore",
    "CatalogIndexer",
    "SHOPZONE_SYSTEM_PROMPT",
    "sanitize_user_input",
    "build_augmented_prompt",
    "format_citations_from_retrieved",
    "AIChatOrchestrator",
    "sse_event",
]
