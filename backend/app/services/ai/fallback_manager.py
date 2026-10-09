"""
LLM Fallback Strategy Manager
Orchestrates primary and fallback LLM providers with bounded retries,
exponential backoff, and clean error recovery for streaming and non-streaming requests.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator

from ...core.config import settings
from .provider_factory import create_llm_provider
from .provider_interface import (
    AIProviderAuthError,
    AIProviderError,
    AIProviderInvalidRequestError,
    AIProviderRateLimitError,
    AIProviderServerError,
    AIProviderTimeoutError,
    LLMProviderInterface,
)

logger = logging.getLogger("shopzone_ai.fallback")


class AllProvidersFailedError(AIProviderError):
    """Raised when every configured LLM provider in the fallback chain has failed."""

    def __init__(self, message: str, errors: list[dict[str, Any]]):
        super().__init__(message, provider="fallback_orchestrator")
        self.errors = errors


class AIFallbackManager:
    """
    Manages primary and fallback LLM providers.
    Supports bounded retries, exponential backoff, and transparent failover.
    """

    def __init__(
        self,
        primary_provider: str | None = None,
        fallback_providers: list[str] | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
    ):
        self.primary_name = (
            primary_provider if primary_provider is not None else settings.AI_PRIMARY_PROVIDER
        ).lower()

        raw_fallbacks = (
            fallback_providers
            if fallback_providers is not None
            else settings.fallback_providers
        )
        # Deduplicate and remove primary from fallbacks
        self.fallback_names = [f.lower() for f in raw_fallbacks if f.lower() != self.primary_name]

        self.max_retries = max_retries if max_retries is not None else settings.AI_MAX_RETRIES
        self.backoff_factor = (
            backoff_factor if backoff_factor is not None else settings.AI_RETRY_BACKOFF_FACTOR
        )

    def get_provider_order(self) -> list[str]:
        """Return the prioritized list of provider names to try."""
        return [self.primary_name] + self.fallback_names

    def _is_retryable_error(self, exc: Exception) -> bool:
        """Determine if the specific error qualifies for a retry with backoff on the same provider."""
        if isinstance(exc, (AIProviderRateLimitError, AIProviderServerError, AIProviderTimeoutError)):
            return True
        # Auth errors (missing or invalid API key) and client-side bad requests must NOT be retried
        if isinstance(exc, (AIProviderAuthError, AIProviderInvalidRequestError)):
            return False
        return False

    async def stream_chat_with_fallback(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        custom_provider_instances: dict[str, LLMProviderInterface] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream chat responses with automated failover across providers.
        Yields dictionaries with:
        - {"type": "provider_selected", "provider": str, "model": str}
        - {"type": "chunk", "text": str, "provider": str}
        - {"type": "provider_fallback", "from_provider": str, "to_provider": str, "reason": str}
        - {"type": "error", "error": str}
        """
        provider_names = self.get_provider_order()
        attempt_errors: list[dict[str, Any]] = []

        for p_idx, provider_name in enumerate(provider_names):
            try:
                if custom_provider_instances and provider_name in custom_provider_instances:
                    provider = custom_provider_instances[provider_name]
                else:
                    provider = create_llm_provider(provider_name)
            except Exception as factory_err:
                logger.warning(
                    "Failed to construct provider '%s': %s. Moving to next fallback.",
                    provider_name,
                    str(factory_err),
                )
                attempt_errors.append({
                    "provider": provider_name,
                    "error": str(factory_err),
                    "type": "configuration_error",
                })
                continue

            # Bounded retry loop for the current provider
            for retry_attempt in range(self.max_retries + 1):
                try:
                    logger.info(
                        "Attempting AI chat stream via provider '%s' (model: %s, attempt %d/%d)",
                        provider_name,
                        provider.model,
                        retry_attempt + 1,
                        self.max_retries + 1,
                    )

                    yield {
                        "type": "provider_selected",
                        "provider": provider.provider_name,
                        "model": provider.model,
                    }

                    emitted_tokens = 0
                    async for chunk in provider.stream_chat(messages, temperature=temperature):
                        emitted_tokens += 1
                        yield {
                            "type": "chunk",
                            "text": chunk,
                            "provider": provider.provider_name,
                        }

                    # Stream completed successfully
                    return

                except Exception as exc:
                    logger.warning(
                        "Provider '%s' error on attempt %d: %s",
                        provider_name,
                        retry_attempt + 1,
                        str(exc),
                    )

                    # CRITICAL: If partial tokens were ALREADY yielded to the client,
                    # we must NOT switch providers silently because it would garble or duplicate output.
                    if "emitted_tokens" in locals() and emitted_tokens > 0:
                        logger.error(
                            "Provider '%s' stream failed mid-generation after %d tokens. Aborting cleanly.",
                            provider_name,
                            emitted_tokens,
                        )
                        yield {
                            "type": "error",
                            "error": "The AI stream connection was interrupted mid-generation. Please retry.",
                        }
                        return

                    # Record attempt failure
                    attempt_errors.append({
                        "provider": provider_name,
                        "attempt": retry_attempt + 1,
                        "error": str(exc),
                        "type": exc.__class__.__name__,
                    })

                    # Check if retryable on the same provider
                    if retry_attempt < self.max_retries and self._is_retryable_error(exc):
                        delay = self.backoff_factor * (2**retry_attempt)
                        logger.info(
                            "Retrying provider '%s' in %.2fs due to %s",
                            provider_name,
                            delay,
                            exc.__class__.__name__,
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Exceeded retries or non-retryable error (e.g. auth / 401). Break to next provider.
                        break

            # If there is another provider to try, announce fallback transition
            next_idx = p_idx + 1
            if next_idx < len(provider_names):
                next_provider = provider_names[next_idx]
                logger.warning(
                    "Failing over from '%s' to fallback provider '%s'",
                    provider_name,
                    next_provider,
                )
                yield {
                    "type": "provider_fallback",
                    "from_provider": provider_name,
                    "to_provider": next_provider,
                    "reason": f"Provider '{provider_name}' was unavailable or failed.",
                }

        # If we exhausted all providers without returning:
        logger.error("All configured LLM providers failed: %s", attempt_errors)
        yield {
            "type": "error",
            "error": "All AI service providers are currently unavailable. Please try again shortly.",
        }
        raise AllProvidersFailedError(
            "Every configured LLM provider failed to fulfill the request.", errors=attempt_errors
        )

    async def generate_chat_with_fallback(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        custom_provider_instances: dict[str, LLMProviderInterface] | None = None,
    ) -> dict[str, Any]:
        """
        Generate complete chat response with fallback orchestration.
        """
        provider_names = self.get_provider_order()
        attempt_errors: list[dict[str, Any]] = []

        for provider_name in provider_names:
            try:
                if custom_provider_instances and provider_name in custom_provider_instances:
                    provider = custom_provider_instances[provider_name]
                else:
                    provider = create_llm_provider(provider_name)
            except Exception as factory_err:
                attempt_errors.append({
                    "provider": provider_name,
                    "error": str(factory_err),
                    "type": "configuration_error",
                })
                continue

            for retry_attempt in range(self.max_retries + 1):
                try:
                    result = await provider.generate_chat(messages, temperature=temperature)
                    result["successful_provider"] = provider.provider_name
                    return result
                except Exception as exc:
                    attempt_errors.append({
                        "provider": provider_name,
                        "attempt": retry_attempt + 1,
                        "error": str(exc),
                        "type": exc.__class__.__name__,
                    })
                    if retry_attempt < self.max_retries and self._is_retryable_error(exc):
                        delay = self.backoff_factor * (2**retry_attempt)
                        await asyncio.sleep(delay)
                        continue
                    break

        raise AllProvidersFailedError(
            "All configured LLM providers failed to generate a response.", errors=attempt_errors
        )
