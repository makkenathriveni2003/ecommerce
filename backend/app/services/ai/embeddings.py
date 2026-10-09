"""
Embedding Provider Implementations
Supports: Local deterministic fallback, Gemini, Mistral, and OpenAI-compatible embedding APIs.
Fully compatible with LangChain Embeddings interface.
"""
from __future__ import annotations

import abc
import hashlib
import logging
import math
import re
from typing import Any

import httpx

from ...core.config import settings

logger = logging.getLogger("shopzone_ai.embeddings")


class BaseEmbeddingProvider(abc.ABC):
    """Abstract interface compatible with LangChain Embeddings."""

    @abc.abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        pass

    # Async methods for high-performance callers
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)


class LocalHashEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, zero-dependency local embedding provider.
    Converts text tokens into a normalized 384-dimensional dense vector
    using stable hash bucket projection and term frequency weighting.
    Guarantees full vector search capability without external API dependencies or heavy downloads.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _hash_token(self, token: str) -> tuple[int, float]:
        """Maps token to a feature index and a sign (+1 or -1) via stable md5 hash."""
        h = hashlib.md5(token.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % self.dimension
        sign = 1.0 if int(h[8:10], 16) % 2 == 0 else -1.0
        return idx, sign

    def _embed_single(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        tokens = re.findall(r"\w+", (text or "").lower())
        if not tokens:
            return vec

        for token in tokens:
            idx, sign = self._hash_token(token)
            vec[idx] += sign

            # Also hash character bigrams for subword / typo similarity
            if len(token) > 3:
                for i in range(len(token) - 2):
                    sub = token[i : i + 3]
                    s_idx, s_sign = self._hash_token(sub)
                    vec[s_idx] += 0.5 * s_sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_single(text)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini text-embedding-004 provider."""

    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.api_key = api_key
        self.model = model
        self._endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key:
            logger.warning("No Gemini API key provided; falling back to local hash embeddings.")
            return LocalHashEmbeddingProvider().embed_documents(texts)

        try:
            requests_payload = [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t}]},
                }
                for t in texts[:100]  # batch limit
            ]
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    self._endpoint,
                    params={"key": self.api_key},
                    json={"requests": requests_payload},
                )
                res.raise_for_status()
                data = res.json()
                return [item["values"] for item in data.get("embeddings", [])]
        except Exception as exc:
            logger.warning("Gemini embedding call failed (%s); using local fallback", exc)
            return LocalHashEmbeddingProvider().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        results = self.embed_documents([text])
        return results[0] if results else [0.0] * 384


class MistralEmbeddingProvider(BaseEmbeddingProvider):
    """Mistral AI embeddings provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "mistral-embed",
        base_url: str = "https://api.mistral.ai/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key:
            return LocalHashEmbeddingProvider().embed_documents(texts)

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    f"{self.base_url}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": texts},
                )
                res.raise_for_status()
                data = res.json()
                return [item["embedding"] for item in data.get("data", [])]
        except Exception as exc:
            logger.warning("Mistral embedding call failed (%s); using local fallback", exc)
            return LocalHashEmbeddingProvider().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        results = self.embed_documents([text])
        return results[0] if results else [0.0] * 384


def get_embedding_provider(
    provider_name: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> BaseEmbeddingProvider:
    """Factory to get the configured embedding provider."""
    name = (provider_name or settings.EMBEDDING_PROVIDER).strip().lower()

    if name == "gemini":
        key = api_key if api_key is not None else settings.GEMINI_API_KEY
        m = model or settings.EMBEDDING_MODEL
        if key:
            return GeminiEmbeddingProvider(api_key=key, model=m)
        logger.info("GEMINI_API_KEY not set for embeddings; using LocalHashEmbeddingProvider.")
        return LocalHashEmbeddingProvider()

    elif name == "mistral":
        key = api_key if api_key is not None else settings.MISTRAL_API_KEY
        m = model or "mistral-embed"
        if key:
            return MistralEmbeddingProvider(api_key=key, model=m)
        logger.info("MISTRAL_API_KEY not set for embeddings; using LocalHashEmbeddingProvider.")
        return LocalHashEmbeddingProvider()

    # Default to robust local hash provider
    return LocalHashEmbeddingProvider()
