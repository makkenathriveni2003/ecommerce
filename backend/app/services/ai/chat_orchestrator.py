"""
AI Chat Orchestrator for ShopZone RAG
Connects vector retrieval, citation extraction, prompt augmentation,
and streaming SSE responses with automated provider fallback.
"""
from __future__ import annotations

import inspect
import json
import logging
from typing import Any, AsyncGenerator, Callable

from ...core.config import settings
from .citations import format_citations_from_retrieved
from .fallback_manager import AIFallbackManager, AllProvidersFailedError
from .prompts import build_augmented_prompt, sanitize_user_input
from .vector_store import ChromaVectorStore

logger = logging.getLogger("shopzone_ai.orchestrator")


def sse_event(event_name: str, data: Any) -> str:
    """Format data as a standard Server-Sent Event string."""
    data_str = json.dumps(data) if not isinstance(data, str) else json.dumps({"text": data})
    return f"event: {event_name}\ndata: {data_str}\n\n"


class AIChatOrchestrator:
    """
    High-level orchestrator for ShopZone AI Chat with RAG and fallback.
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        fallback_manager: AIFallbackManager | None = None,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.fallback_manager = fallback_manager or AIFallbackManager()

    async def stream_rag_chat(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        category_filter: str | None = None,
        is_client_disconnected: Callable[[], bool] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        End-to-end RAG stream generator yielding SSE formatted strings.
        """
        clean_query = sanitize_user_input(query)
        if not clean_query:
            yield sse_event("error", {"error": "Message cannot be empty."})
            return

        # 1. Retrieve relevant product documents from vector store
        where_clause = {"category": category_filter} if category_filter else None
        try:
            retrieved_docs = self.vector_store.query_similar(
                query=clean_query,
                top_k=settings.RAG_TOP_K,
                where_filter=where_clause,
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s; proceeding with empty context", exc)
            retrieved_docs = []

        # 2. Extract and emit source citations immediately so UI can display sources
        citations = format_citations_from_retrieved(retrieved_docs)
        yield sse_event("citations", citations)

        # 3. Construct prompt messages with grounding and security fences
        messages = build_augmented_prompt(
            user_query=clean_query,
            retrieved_docs=retrieved_docs,
            conversation_history=conversation_history,
        )

        # 4. Stream response from fallback manager
        active_provider = "unknown"
        try:
            async for event_dict in self.fallback_manager.stream_chat_with_fallback(messages):
                # Check for client disconnect
                if is_client_disconnected:
                    disconnected = False
                    try:
                        if inspect.iscoroutinefunction(is_client_disconnected):
                            disconnected = await is_client_disconnected()
                        elif callable(is_client_disconnected):
                            res = is_client_disconnected()
                            if inspect.isawaitable(res):
                                disconnected = await res
                            else:
                                disconnected = bool(res)
                    except Exception:
                        disconnected = False
                    if disconnected:
                        logger.info("Client disconnected. Aborting AI generation stream.")
                        return

                event_type = event_dict.get("type")
                if event_type == "provider_selected":
                    active_provider = event_dict.get("provider", "unknown")
                    yield sse_event("provider", {
                        "provider": active_provider,
                        "model": event_dict.get("model", ""),
                    })

                elif event_type == "chunk":
                    token_text = event_dict.get("text", "")
                    yield sse_event("chunk", {"text": token_text, "chunk": token_text})

                elif event_type == "provider_fallback":
                    yield sse_event("provider_change", {
                        "from": event_dict.get("from_provider"),
                        "to": event_dict.get("to_provider"),
                        "reason": event_dict.get("reason"),
                    })

                elif event_type == "error":
                    yield sse_event("error", {"error": event_dict.get("error")})

            # Stream finished cleanly
            yield sse_event("done", {
                "finish_reason": "stop",
                "provider": active_provider,
                "citations_count": len(citations),
            })

        except AllProvidersFailedError as exc:
            logger.error("All providers exhausted: %s", exc)
            yield sse_event("error", {
                "error": "We're experiencing high demand and our AI services are temporarily unavailable. Please try again shortly."
            })
        except Exception as exc:
            logger.exception("Unexpected error during RAG chat streaming: %s", exc)
            yield sse_event("error", {
                "error": "An error occurred while generating the response. Please try again."
            })

    async def generate_rag_chat(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        category_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Non-streaming RAG chat generation for testing and programmatic use.
        """
        clean_query = sanitize_user_input(query)
        where_clause = {"category": category_filter} if category_filter else None

        retrieved_docs = self.vector_store.query_similar(
            query=clean_query,
            top_k=settings.RAG_TOP_K,
            where_filter=where_clause,
        )
        citations = format_citations_from_retrieved(retrieved_docs)
        messages = build_augmented_prompt(
            user_query=clean_query,
            retrieved_docs=retrieved_docs,
            conversation_history=conversation_history,
        )

        response = await self.fallback_manager.generate_chat_with_fallback(messages)
        return {
            "answer": response.get("content", ""),
            "provider": response.get("successful_provider", ""),
            "model": response.get("model", ""),
            "citations": citations,
        }
