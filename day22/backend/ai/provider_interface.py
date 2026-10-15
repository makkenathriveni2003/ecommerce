"""
Modular LLM Provider Interface and Concrete Implementations
Supports: Groq, Google Gemini, Mistral, and OpenAI-Compatible APIs.
"""
from __future__ import annotations

import abc
import json
import logging
from typing import Any, AsyncGenerator

import httpx

logger = logging.getLogger("shopzone_ai.providers")


class AIProviderError(Exception):
    """Base exception for AI provider operations."""

    def __init__(self, message: str, provider: str = "unknown", status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code


class AIProviderTimeoutError(AIProviderError):
    """Raised when an AI provider call times out."""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Raised when an AI provider returns HTTP 429 (Rate Limit)."""
    pass


class AIProviderAuthError(AIProviderError):
    """Raised when an AI provider authentication fails (401/403 or missing key)."""
    pass


class AIProviderServerError(AIProviderError):
    """Raised when an AI provider returns 5xx server error."""
    pass


class AIProviderInvalidRequestError(AIProviderError):
    """Raised when a request is rejected by provider with 4xx client error."""
    pass


class LLMProviderInterface(abc.ABC):
    """Abstract interface that all LLM providers must implement."""

    def __init__(self, api_key: str, model: str, base_url: str = "", timeout: float = 30.0):
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.base_url = (base_url or "").strip().rstrip("/")
        self.timeout = timeout

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier (e.g. 'groq', 'gemini', 'mistral')."""
        pass

    def validate_configuration(self) -> None:
        """Validate that provider has an API key configured."""
        if not self.api_key:
            raise AIProviderAuthError(
                f"API key is not configured for provider '{self.provider_name}'.",
                provider=self.provider_name,
                status_code=401,
            )

    @abc.abstractmethod
    async def stream_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks (text tokens) from the provider."""
        yield ""

    @abc.abstractmethod
    async def generate_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> dict[str, Any]:
        """Generate a complete non-streaming response from the provider."""
        pass


class OpenAICompatibleProvider(LLMProviderInterface):
    """
    Standard OpenAI-compatible provider.
    Works for OpenAI, Groq, Mistral, Together, vLLM, Ollama, etc.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
        provider_label: str = "openai_compatible",
    ):
        super().__init__(api_key=api_key, model=model, base_url=base_url, timeout=timeout)
        self._provider_label = provider_label

    @property
    def provider_name(self) -> str:
        return self._provider_label

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ShopZone-AI/1.0",
        }

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        try:
            err_data = exc.response.json()
            err_msg = err_data.get("error", {}).get("message") or exc.response.text
        except Exception:
            err_msg = exc.response.text or str(exc)

        # Sanitize error message to avoid leaking any credentials
        safe_msg = f"{self.provider_name} API error (HTTP {status}): {err_msg[:200]}"
        if status == 429:
            raise AIProviderRateLimitError(safe_msg, provider=self.provider_name, status_code=status) from exc
        if status in (401, 403):
            raise AIProviderAuthError(safe_msg, provider=self.provider_name, status_code=status) from exc
        if 500 <= status < 600:
            raise AIProviderServerError(safe_msg, provider=self.provider_name, status_code=status) from exc
        raise AIProviderInvalidRequestError(safe_msg, provider=self.provider_name, status_code=status) from exc

    async def stream_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        self.validate_configuration()
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        timeout_config = httpx.Timeout(self.timeout, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream(
                    "POST", endpoint, headers=self._get_headers(), json=payload
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        response.raise_for_status()

                    buffer = ""
                    async for raw_bytes in response.aiter_bytes():
                        buffer += raw_bytes.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                return
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError(
                f"{self.provider_name} request timed out after {self.timeout}s",
                provider=self.provider_name,
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (AIProviderError, GeneratorExit):
            raise
        except Exception as exc:
            raise AIProviderServerError(
                f"Unexpected {self.provider_name} client error: {str(exc)[:150]}",
                provider=self.provider_name,
            ) from exc

    async def generate_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> dict[str, Any]:
        self.validate_configuration()
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        timeout_config = httpx.Timeout(self.timeout, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    endpoint, headers=self._get_headers(), json=payload
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "provider": self.provider_name,
                    "model": self.model,
                    "content": content,
                    "usage": data.get("usage", {}),
                }
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError(
                f"{self.provider_name} request timed out", provider=self.provider_name
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderServerError(
                f"Unexpected {self.provider_name} failure: {str(exc)[:150]}",
                provider=self.provider_name,
            ) from exc


class GroqProvider(OpenAICompatibleProvider):
    """Groq Cloud API provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 30.0,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.groq.com/openai/v1",
            timeout=timeout,
            provider_label="groq",
        )


class MistralProvider(OpenAICompatibleProvider):
    """Mistral AI API provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "mistral-small-latest",
        base_url: str = "https://api.mistral.ai/v1",
        timeout: float = 30.0,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://api.mistral.ai/v1",
            timeout=timeout,
            provider_label="mistral",
        )


class GeminiProvider(LLMProviderInterface):
    """Google Gemini API provider (Google Generative Language REST v1beta)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout: float = 30.0,
    ):
        super().__init__(api_key=api_key, model=model, timeout=timeout)
        self._base_api = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _convert_messages_to_gemini(
        self, messages: list[dict[str, str]]
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Separate system instruction and convert conversation history to Gemini contents format."""
        system_instruction: dict[str, Any] | None = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role in ("assistant", "model"):
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        # Gemini requires at least one user turn
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        return system_instruction, contents

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        try:
            err_data = exc.response.json()
            err_msg = err_data.get("error", {}).get("message") or exc.response.text
        except Exception:
            err_msg = exc.response.text or str(exc)

        safe_msg = f"Gemini API error (HTTP {status}): {err_msg[:200]}"
        if status == 429:
            raise AIProviderRateLimitError(safe_msg, provider="gemini", status_code=status) from exc
        if status in (401, 403):
            raise AIProviderAuthError(safe_msg, provider="gemini", status_code=status) from exc
        if 500 <= status < 600:
            raise AIProviderServerError(safe_msg, provider="gemini", status_code=status) from exc
        raise AIProviderInvalidRequestError(safe_msg, provider="gemini", status_code=status) from exc

    async def stream_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> AsyncGenerator[str, None]:
        self.validate_configuration()
        endpoint = f"{self._base_api}/{self.model}:streamGenerateContent"
        params = {"alt": "sse", "key": self.api_key}

        sys_inst, contents = self._convert_messages_to_gemini(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if sys_inst:
            payload["systemInstruction"] = sys_inst

        timeout_config = httpx.Timeout(self.timeout, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream(
                    "POST", endpoint, params=params, json=payload
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        response.raise_for_status()

                    buffer = ""
                    async for raw_bytes in response.aiter_bytes():
                        buffer += raw_bytes.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            try:
                                chunk = json.loads(data_str)
                                candidates = chunk.get("candidates", [])
                                if candidates:
                                    content = candidates[0].get("content", {})
                                    parts = content.get("parts", [])
                                    for part in parts:
                                        text_piece = part.get("text")
                                        if text_piece:
                                            yield text_piece
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError(
                f"Gemini request timed out after {self.timeout}s", provider="gemini"
            ) from exc
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except (AIProviderError, GeneratorExit):
            raise
        except Exception as exc:
            raise AIProviderServerError(
                f"Unexpected Gemini client error: {str(exc)[:150]}", provider="gemini"
            ) from exc

    async def generate_chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> dict[str, Any]:
        self.validate_configuration()
        endpoint = f"{self._base_api}/{self.model}:generateContent"
        params = {"key": self.api_key}

        sys_inst, contents = self._convert_messages_to_gemini(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if sys_inst:
            payload["systemInstruction"] = sys_inst

        timeout_config = httpx.Timeout(self.timeout, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(endpoint, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates", [])
                text_content = ""
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text_content = "".join(p.get("text", "") for p in parts)
                return {
                    "provider": "gemini",
                    "model": self.model,
                    "content": text_content,
                    "usage": data.get("usageMetadata", {}),
                }
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError("Gemini request timed out", provider="gemini") from exc
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderServerError(
                f"Unexpected Gemini failure: {str(exc)[:150]}", provider="gemini"
            ) from exc
