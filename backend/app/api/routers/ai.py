"""
FastAPI Router for ShopZone AI Assistant
Provides SSE streaming chat, non-streaming chat, catalog reindexing, and status endpoints.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ...core.config import settings
from ...core.rate_limit import limiter
from ...core.security import require_admin
from ...schemas.ai_schemas import (
    AIChatRequest,
    AIChatResponse,
    AIIndexResponse,
    AIStatusResponse,
)
from ...services.ai import AIChatOrchestrator, CatalogIndexer, ChromaVectorStore

logger = logging.getLogger("shopzone_api.ai")

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

_orchestrator: AIChatOrchestrator | None = None
_indexer: CatalogIndexer | None = None


def get_orchestrator() -> AIChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIChatOrchestrator()
    return _orchestrator


def get_indexer() -> CatalogIndexer:
    global _indexer
    if _indexer is None:
        _indexer = CatalogIndexer()
    return _indexer


@router.post(
    "/chat/stream",
    summary="Stream AI Shopping Assistant response via Server-Sent Events (SSE)",
)
@limiter.limit(settings.AI_RATE_LIMIT)
async def stream_ai_chat(
    request: Request,
    payload: AIChatRequest,
    orchestrator: AIChatOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    """
    Progressively streams AI answers token-by-token using Server-Sent Events (SSE).
    Emits events:
    - 'provider': Active LLM provider and model
    - 'citations': Verified product source cards from catalogue
    - 'chunk': Streaming text fragment
    - 'provider_change': Triggered when automated fallback occurs
    - 'error': Clean, non-leaking error description
    - 'done': Completion signal
    """
    # Transform history to dict format
    history = [
        {"role": item.role, "content": item.content}
        for item in payload.conversation_history
    ]

    async def event_generator():
        async for event_line in orchestrator.stream_rag_chat(
            query=payload.message,
            conversation_history=history,
            category_filter=payload.category,
            is_client_disconnected=request.is_disconnected,
        ):
            yield event_line

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Synchronous / non-streaming AI chat for programmatic access",
)
@limiter.limit(settings.AI_RATE_LIMIT)
async def generate_ai_chat(
    request: Request,
    payload: AIChatRequest,
    orchestrator: AIChatOrchestrator = Depends(get_orchestrator),
) -> AIChatResponse:
    history = [
        {"role": item.role, "content": item.content}
        for item in payload.conversation_history
    ]

    result = await orchestrator.generate_rag_chat(
        query=payload.message,
        conversation_history=history,
        category_filter=payload.category,
    )

    return AIChatResponse(
        answer=result.get("answer", ""),
        provider=result.get("provider", "unknown"),
        model=result.get("model", ""),
        citations=result.get("citations", []),
    )


@router.post(
    "/index/reindex",
    response_model=AIIndexResponse,
    summary="Admin-only endpoint to sync database products into ChromaDB vector store",
)
def reindex_catalog(
    admin_user: dict[str, Any] = Depends(require_admin),
    indexer: CatalogIndexer = Depends(get_indexer),
) -> AIIndexResponse:
    """
    Loads all products from the PostgreSQL / SQLite database and indexes them into ChromaDB.
    Strictly protected by admin role authentication.
    """
    logger.info("Admin %s triggered catalogue reindexing", admin_user.get("email"))
    summary = indexer.reindex_all_products(clear_existing=True)
    return AIIndexResponse(
        products_indexed=summary["products_indexed"],
        chunks_indexed=summary["chunks_indexed"],
        total_vectors=summary["total_vectors"],
        message=summary["message"],
    )


@router.get(
    "/status",
    response_model=AIStatusResponse,
    summary="Get operational status of AI providers and ChromaDB vectors",
)
def get_ai_status(
    orchestrator: AIChatOrchestrator = Depends(get_orchestrator),
) -> AIStatusResponse:
    """
    Public diagnostic endpoint reporting vector count and provider configuration.
    Never exposes raw API keys.
    """
    count = orchestrator.vector_store.count()
    return AIStatusResponse(
        primary_provider=settings.AI_PRIMARY_PROVIDER,
        fallback_providers=settings.fallback_providers,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        indexed_vectors_count=count,
        configured_providers={
            "groq": bool(settings.GROQ_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "mistral": bool(settings.MISTRAL_API_KEY),
            "openai_compatible": bool(settings.OPENAI_API_KEY),
        },
    )
