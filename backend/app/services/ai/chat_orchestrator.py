"""
AI Chat Orchestrator for Chow Zoon RAG
Connects vector retrieval, citation extraction, prompt augmentation,
streaming SSE responses with automated provider fallback, and Redis response caching.
Enhanced with intelligent query intent classification, budget/price constraint filtering,
and polite handling for greetings and out-of-scope non-e-commerce queries.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
from typing import Any, AsyncGenerator, Callable

from ...core.config import settings
from .ai_cache import ai_cache
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
    High-level orchestrator for Chow Zoon AI Chat with RAG, Redis caching, and fallback.
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore | None = None,
        fallback_manager: AIFallbackManager | None = None,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.fallback_manager = fallback_manager or AIFallbackManager()

    def analyze_and_retrieve(
        self, clean_query: str, category_filter: str | None = None
    ) -> dict[str, Any]:
        """
        Intelligently analyzes user intent:
        1. Greetings & Small Talk -> Friendly greeting with ZERO citations.
        2. Out-of-Scope / Non-E-Commerce (e.g. food, cars, medicines, jokes) -> Polite 'not available' message with ZERO citations.
        3. Price Budget Filtering (e.g. 'under 2000', 'shoes below 1500') -> Strictly returns products matching the price limit.
        4. Irrelevant / Nonsense Queries -> 'Not available in catalogue' with ZERO citations.
        5. In-Scope Product Queries -> ChromaDB retrieval with verified citations.
        """
        text = clean_query.strip().lower()
        clean_words = re.findall(r"\b[a-zA-Z0-9]+\b", text)

        # 1. Greetings & Small-Talk Intent
        greeting_words = {
            "hi", "hello", "hloo", "hlw", "hey", "heyy", "helo", "hii", "hiii",
            "good morning", "good afternoon", "good evening", "good day",
            "how are you", "who are you", "what is your name", "what can you do",
            "help", "test", "testing", "ok", "okay", "thanks", "thank you", "bye", "goodbye"
        }
        is_greeting = (
            text in greeting_words or
            (len(clean_words) <= 2 and any(text.startswith(g) for g in ["hi", "hello", "hloo", "hey", "helo"])) or
            text in ["hi there", "hello there", "hey assistant", "yo", "wassup"]
        )
        if is_greeting:
            return {
                "type": "greeting",
                "answer": (
                    "Hello! 👋 Welcome to GenZ Zone. I am your AI Shopping Assistant! "
                    "I can help you browse products, compare prices, or find items by budget "
                    "(for example, try asking 'Show me kurtis under ₹2,000' or 'Suggest running shoes'). "
                    "What would you like to shop for today?"
                ),
                "citations": [],
                "docs": [],
            }

        # 2. Out-of-Scope / Non-E-Commerce Requests
        out_of_scope_keywords = [
            "pizza", "burger", "biryani", "food", "grocery", "vegetable", "fruit",
            "medicine", "tablet", "pharma", "car", "bike", "vehicle", "real estate",
            "house", "apartment", "flat for rent", "flight", "train", "hotel", "weather",
            "stock market", "crypto", "bitcoin", "homework", "math", "joke", "movie ticket",
            "cricket bat", "football", "guitar", "washing machine", "refrigerator", "tv", "television"
        ]
        if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in out_of_scope_keywords):
            return {
                "type": "out_of_scope",
                "answer": (
                    "No, that item is not available in our GenZ Zone catalogue. "
                    "We specialize in trending fashion apparel, footwear, jewellery, bags, and consumer electronics. "
                    "Please let me know if you would like to explore any of our clothing, shoe, or tech collections!"
                ),
                "citations": [],
                "docs": [],
            }

        # 3. Detect Budget / Price Constraints
        m_max = re.search(
            r"(?:under|below|less than|within|upto|up to|budget of|max(?:imum)?)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)",
            text
        )
        if not m_max:
            m_max = re.search(r"(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:lopu|varaku|under|below|budget|or less|kante thakkuva)", text)
        max_price = float(m_max.group(1).replace(",", "")) if m_max else None

        m_min = re.search(
            r"(?:above|more than|greater than|over|min(?:imum)?|starting from)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)",
            text
        )
        min_price = float(m_min.group(1).replace(",", "")) if m_min else None

        # 4. Detect Specific Category Focus
        category_keywords = {
            "shoes": ["shoe", "footwear", "sneaker", "flat", "heel", "mule", "loafer", "sandal", "pumps"],
            "laptops": ["laptop", "computer", "macbook", "notebook", "pc"],
            "phones": ["phone", "mobile", "iphone", "smartphone"],
            "audio": ["headphone", "earbud", "audio", "airpod", "tws", "earphones"],
            "bags": ["bag", "tote", "handbag", "satchel", "backpack", "purse", "clutch", "hobo", "crossbody"],
            "jewellery": ["jewel", "earring", "necklace", "ring", "bracelet", "choker", "pendant"],
            "apparel": ["dress", "kurti", "shirt", "tee", "jean", "hoodie", "apparel", "top", "anarkali", "pant", "denim", "tank", "vest", "clothing"],
        }
        required_keywords: list[str] | None = None
        for cat_name, kw_list in category_keywords.items():
            if any(re.search(rf"\b{re.escape(k)}\b", text) or k in text for k in kw_list):
                required_keywords = kw_list
                break

        # 5. Retrieve from Vector Store
        where_clause = {"category": category_filter} if category_filter else None
        try:
            raw_docs = self.vector_store.query_similar(
                query=clean_query,
                top_k=25 if (max_price is not None or required_keywords) else settings.RAG_TOP_K,
                where_filter=where_clause,
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s; proceeding with empty context", exc)
            raw_docs = []

        # Helper to test candidate compliance
        def is_candidate_valid(p_name: str, p_cat: str, p_price: float) -> bool:
            if max_price is not None and p_price > max_price:
                return False
            if min_price is not None and p_price < min_price:
                return False
            if required_keywords:
                # If specifically looking for laptop/computer, don't include backpack even if title says laptop backpack
                if "laptop" in text or "computer" in text:
                    if not any(k in text for k in ["bag", "backpack", "case", "sleeve"]):
                        if p_cat.lower() == "bags" or "backpack" in p_name.lower():
                            return False
                target_str = f"{p_name} {p_cat}".lower()
                if not any(k in target_str for k in required_keywords):
                    return False
            return True

        candidates: list[dict[str, Any]] = []
        for d in raw_docs:
            meta = d.get("metadata", {})
            p_name = str(meta.get("product_name", ""))
            p_cat = str(meta.get("category", ""))
            p_price = float(meta.get("price", 999999))
            if is_candidate_valid(p_name, p_cat, p_price):
                candidates.append(d)

        # If price filter or category focus is active and candidates < 4, augment from catalog DB
        if (max_price is not None or required_keywords) and len(candidates) < 4:
            try:
                from ..product_service import get_products
                db_prods = get_products(0, 100)
                for p in db_prods:
                    p_price = float(p.get("price", 0))
                    if is_candidate_valid(p["name"], p["category"], p_price):
                        doc_id = f"prod_{p['id']}_chunk_0"
                        if not any(c.get("id") == doc_id or c.get("metadata", {}).get("product_id") == p["id"] for c in candidates):
                            candidates.append({
                                "id": doc_id,
                                "document": f"{p['name']} in category {p['category']}. Price: ₹{p_price}. {p.get('description', '')}",
                                "metadata": {
                                    "product_id": p["id"],
                                    "product_name": p["name"],
                                    "category": p["category"],
                                    "price": p_price,
                                    "stock": p.get("stock", 50),
                                    "url": f"/products/{p['id']}",
                                },
                                "distance": 0.5,
                            })
            except Exception as db_err:
                logger.warning("Database fallback augmentation error: %s", db_err)

        # 6. Check if price-filtered query found 0 matching items
        if max_price is not None and not candidates:
            return {
                "type": "no_results_price",
                "answer": (
                    f"No, we searched our GenZ Zone catalogue, but do not have items in that category under ₹{int(max_price):,} in stock. "
                    f"Our items in that collection start at a slightly higher price point. "
                    f"Would you like to explore our other categories or adjust your budget range?"
                ),
                "citations": [],
                "docs": [],
            }

        # 7. Check if non-price query returned no relevant items or poor vector similarity
        if not candidates or (not required_keywords and max_price is None and all(d.get("distance", 0) > 1.68 for d in candidates)):
            return {
                "type": "no_results",
                "answer": (
                    f"No, I searched our GenZ Zone catalogue, but could not find matching products for '{clean_query}'. "
                    f"That product is currently not available in our store. "
                    f"Feel free to explore our trending apparel, footwear, jewellery, bags, or electronics!"
                ),
                "citations": [],
                "docs": [],
            }

        final_docs = candidates[:settings.RAG_TOP_K]
        citations = format_citations_from_retrieved(final_docs)
        return {
            "type": "product_search",
            "docs": final_docs,
            "citations": citations,
            "max_price": max_price,
        }

    async def stream_rag_chat(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        category_filter: str | None = None,
        is_client_disconnected: Callable[[], bool] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        End-to-end RAG stream generator yielding SSE formatted strings.
        Checks Redis response cache first to achieve ultra-low latency and $0 API cost.
        """
        clean_query = sanitize_user_input(query)
        if not clean_query:
            yield sse_event("error", {"error": "Message cannot be empty."})
            return

        # 1. Check Redis Cache for repeated question
        cached_result = ai_cache.get_cached_chat(clean_query, category_filter)
        if cached_result:
            yield sse_event("provider", {
                "provider": f"{cached_result.get('provider', 'AI')} (Redis Cached)",
                "model": cached_result.get("model", ""),
            })
            yield sse_event("citations", cached_result.get("citations", []))

            # Stream cached chunks smoothly
            answer_text = cached_result.get("answer", "")
            tokens = answer_text.split(" ")
            for token in tokens:
                yield sse_event("chunk", {"text": token + " ", "chunk": token + " "})
                await asyncio.sleep(0.01)

            yield sse_event("done", {
                "finish_reason": "stop",
                "provider": "Redis Cache",
                "citations_count": len(cached_result.get("citations", [])),
                "cached": True,
            })
            return

        # 2. Analyze Query Intent, Filter Price Constraints, and Retrieve Documents
        analysis = self.analyze_and_retrieve(clean_query, category_filter)

        # If Greeting, Out-of-Scope, or No Results: Stream friendly direct message with ZERO citations
        if analysis["type"] in ("greeting", "out_of_scope", "no_results", "no_results_price"):
            direct_msg = analysis["answer"]
            yield sse_event("provider", {
                "provider": "GenZ Zone Assistant",
                "model": "catalogue-grounded-v1",
            })
            yield sse_event("citations", [])

            words = direct_msg.split(" ")
            for w in words:
                yield sse_event("chunk", {"text": w + " ", "chunk": w + " "})
                await asyncio.sleep(0.015)

            ai_cache.set_cached_chat(
                clean_query,
                {
                    "answer": direct_msg,
                    "provider": "GenZ Zone Assistant",
                    "model": "catalogue-grounded-v1",
                    "citations": [],
                },
                category_filter,
            )
            yield sse_event("done", {
                "finish_reason": "stop",
                "provider": "GenZ Zone Assistant",
                "citations_count": 0,
                "cached": False,
            })
            return

        # 3. Product Search Intent: Extract Verified Citations
        retrieved_docs = analysis.get("docs", [])
        citations = analysis.get("citations", [])
        max_price = analysis.get("max_price")

        yield sse_event("citations", citations)

        # 4. Construct prompt messages with grounding and security fences
        messages = build_augmented_prompt(
            user_query=clean_query,
            retrieved_docs=retrieved_docs,
            conversation_history=conversation_history,
        )

        # 5. Stream response from fallback manager
        active_provider = "unknown"
        active_model = ""
        accumulated_chunks: list[str] = []

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
                    active_model = event_dict.get("model", "")
                    yield sse_event("provider", {
                        "provider": active_provider,
                        "model": active_model,
                    })

                elif event_type == "chunk":
                    token_text = event_dict.get("text", "")
                    accumulated_chunks.append(token_text)
                    yield sse_event("chunk", {"text": token_text, "chunk": token_text})

                elif event_type == "provider_fallback":
                    yield sse_event("provider_change", {
                        "from": event_dict.get("from_provider"),
                        "to": event_dict.get("to_provider"),
                        "reason": event_dict.get("reason"),
                    })

            # Stream finished cleanly - cache in Redis
            full_text = "".join(accumulated_chunks)
            if full_text.strip():
                ai_cache.set_cached_chat(
                    clean_query,
                    {
                        "answer": full_text,
                        "provider": active_provider,
                        "model": active_model,
                        "citations": citations,
                    },
                    category_filter,
                )
                ai_cache.record_ai_call(active_provider, active_model)

            yield sse_event("done", {
                "finish_reason": "stop",
                "provider": active_provider,
                "citations_count": len(citations),
                "cached": False,
            })

        except (AllProvidersFailedError, Exception) as exc:
            logger.warning("All LLM providers unavailable for stream: %s. Using catalogue-grounded fallback stream.", exc)
            fallback_provider = "GenZ Zone Assistant"
            fallback_model = "catalogue-grounded-v1"
            yield sse_event("provider", {
                "provider": fallback_provider,
                "model": fallback_model,
            })

            if max_price is not None:
                header_text = f"Here are the verified items currently in stock under ₹{int(max_price):,} from our GenZ Zone catalogue matching your request:"
            else:
                header_text = "Here are the verified items currently in stock from our GenZ Zone catalogue matching your request:"

            items_summary = "\n".join([
                f"• {c.get('product_name') or c.get('name', 'Product')} — ₹{int(c.get('price', 0)):,} (Category: {c.get('category', 'General')})"
                for c in citations
            ])
            fallback_message = (
                f"{header_text}\n\n"
                f"{items_summary}\n\n"
                f"You can explore all high-definition angles, detailed specs, and customer reviews below!"
            )

            words = fallback_message.split(" ")
            for w in words:
                yield sse_event("chunk", {"text": w + " ", "chunk": w + " "})
                await asyncio.sleep(0.015)

            # Cache fallback response for performance
            ai_cache.set_cached_chat(
                clean_query,
                {
                    "answer": fallback_message,
                    "provider": fallback_provider,
                    "model": fallback_model,
                    "citations": citations,
                },
                category_filter,
            )
            ai_cache.record_ai_call(fallback_provider, fallback_model)

            yield sse_event("done", {
                "finish_reason": "stop",
                "provider": fallback_provider,
                "citations_count": len(citations),
                "cached": False,
            })

    async def generate_rag_chat(
        self,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        category_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Non-streaming RAG chat generation for testing and programmatic use.
        Uses Redis response cache for repeat queries.
        """
        clean_query = sanitize_user_input(query)

        # Check Redis Cache
        cached = ai_cache.get_cached_chat(clean_query, category_filter)
        if cached:
            return cached

        # Analyze intent and retrieve documents
        analysis = self.analyze_and_retrieve(clean_query, category_filter)
        if analysis["type"] in ("greeting", "out_of_scope", "no_results", "no_results_price"):
            result = {
                "answer": analysis["answer"],
                "provider": "GenZ Zone Assistant",
                "model": "catalogue-grounded-v1",
                "citations": [],
            }
            ai_cache.set_cached_chat(clean_query, result, category_filter)
            return result

        retrieved_docs = analysis.get("docs", [])
        citations = analysis.get("citations", [])
        max_price = analysis.get("max_price")

        messages = build_augmented_prompt(
            user_query=clean_query,
            retrieved_docs=retrieved_docs,
            conversation_history=conversation_history,
        )

        try:
            response = await self.fallback_manager.generate_chat_with_fallback(messages)
            content = response.get("content", "")
            successful_provider = response.get("successful_provider", "")
            model = response.get("model", "")
        except Exception as err:
            logger.warning("LLM providers unavailable for chat: %s. Using catalogue-grounded fallback.", err)
            successful_provider = "GenZ Zone Assistant"
            model = "catalogue-grounded-v1"
            if max_price is not None:
                header = f"Here are the items under ₹{int(max_price):,} from our catalogue:"
            else:
                header = "Based on our current GenZ Zone catalogue, here are relevant items:"
            items_text = ", ".join(
                f"{c.get('product_name') or c.get('name', 'Product')} (₹{int(c.get('price', 0)):,})"
                for c in citations[:4]
            )
            content = f"{header} {items_text}. Let me know if you need further details!"

        result = {
            "answer": content,
            "provider": successful_provider,
            "model": model,
            "citations": citations,
        }

        # Cache response
        if result["answer"]:
            ai_cache.set_cached_chat(clean_query, result, category_filter)
            ai_cache.record_ai_call(result["provider"], result["model"])

        return result
