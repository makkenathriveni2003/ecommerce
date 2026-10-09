"""
AI Provider Factory
Instantiates and configures LLM providers based on application configuration.
"""
from __future__ import annotations

import logging
from typing import Any

from ...core.config import settings
from .provider_interface import (
    GeminiProvider,
    GroqProvider,
    LLMProviderInterface,
    MistralProvider,
    OpenAICompatibleProvider,
    AIProviderError,
)

logger = logging.getLogger("shopzone_ai.factory")


def create_llm_provider(
    provider_name: str,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> LLMProviderInterface:
    """
    Factory function to construct a configured LLM provider.
    Falls back to `settings` defaults for any omitted parameters.
    """
    name = (provider_name or "").strip().lower()
    t = timeout if timeout is not None else settings.AI_REQUEST_TIMEOUT

    if name == "groq":
        return GroqProvider(
            api_key=api_key if api_key is not None else settings.GROQ_API_KEY,
            model=model if model is not None else settings.GROQ_MODEL,
            base_url=base_url if base_url is not None else settings.GROQ_BASE_URL,
            timeout=t,
        )
    elif name == "gemini":
        return GeminiProvider(
            api_key=api_key if api_key is not None else settings.GEMINI_API_KEY,
            model=model if model is not None else settings.GEMINI_MODEL,
            timeout=t,
        )
    elif name == "mistral":
        return MistralProvider(
            api_key=api_key if api_key is not None else settings.MISTRAL_API_KEY,
            model=model if model is not None else settings.MISTRAL_MODEL,
            base_url=base_url if base_url is not None else settings.MISTRAL_BASE_URL,
            timeout=t,
        )
    elif name in ("openai", "openai_compatible", "openai-compatible"):
        return OpenAICompatibleProvider(
            api_key=api_key if api_key is not None else settings.OPENAI_API_KEY,
            model=model if model is not None else settings.OPENAI_MODEL,
            base_url=base_url if base_url is not None else settings.OPENAI_BASE_URL,
            timeout=t,
            provider_label="openai_compatible",
        )
    else:
        raise AIProviderError(
            f"Unsupported AI provider '{provider_name}'. Supported: groq, gemini, mistral, openai_compatible",
            provider=provider_name,
        )
