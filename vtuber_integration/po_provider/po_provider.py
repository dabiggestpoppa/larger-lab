"""
PO Provider Adapter — OpenAI-compatible LLM provider for Open-LLM-VTuber.

Implements StatelessLLMInterface so VTuber treats PO as a normal LLM provider.
Internally routes all requests through OCE's cognitive field runtime.

Phase 1 of PO × Open-LLM-VTuber Integration.
"""

from typing import AsyncIterator, List, Dict, Any
import logging

# Use standard logging instead of loguru for test compatibility
logger = logging.getLogger("po_provider")

# Import VTuber's StatelessLLMInterface
# VTuber is cloned at vtuber_integration/Open-LLM-VTuber/src/open_llm_vtuber/
try:
    from open_llm_vtuber.agent.stateless_llm.stateless_llm_interface import (
        StatelessLLMInterface,
    )
except ImportError:
    # Fallback: define minimal interface for testing
    import abc
    class StatelessLLMInterface(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        async def chat_completion(self, messages, system=None, tools=None):
            ...

# Fallback if direct import fails (dev/testing)
try:
    from openai import AsyncOpenAI, NotGiven, NOT_GIVEN
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False

import httpx
import json
import os


class POProviderConfig:
    """Configuration for the PO Provider adapter."""

    oce_url: str = "http://localhost:8000"
    oce_token: str = ""
    model: str = "po"
    temperature: float = 0.7
    timeout: float = 300.0

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class POProvider(StatelessLLMInterface):
    """
    PO Provider — routes LLM calls through OCE cognitive field.

    Implements the StatelessLLMInterface so Open-LLM-VTuber's BasicMemoryAgent
    can use it as a drop-in replacement for OpenAI/Ollama/Claude providers.

    Wire format: OCE /api/po/chat accepts OpenAI-shape requests and returns
    OpenAI-shape SSE streams (chat.completion.chunk format).
    """

    def __init__(
        self,
        model: str = "po",
        base_url: str = "http://localhost:8000",
        llm_api_key: str = "",
        organization_id: str = "",
        project_id: str = "",
        temperature: float = 0.7,
        **kwargs,
    ):
        self.config = POProviderConfig(
            oce_url=base_url or "http://localhost:8000",
            oce_token=llm_api_key or "",
            model=model,
            temperature=temperature,
        )
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(
            connect=10.0, read=60.0, write=60.0, pool=None
        )
        logger.info(
            f"POProvider initialized: model={model}, oce_url={self.config.oce_url}"
        )

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.oce_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self.config.oce_token}" if self.config.oce_token else "",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        system: str = None,
        tools: List[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Send a chat request to OCE and stream the response.

        Parameters:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt (passed as first message if provided)
            tools: Tool definitions (passed through to OCE)

        Yields:
            str: Text content chunks from the OCE streaming response
        """
        # Build OpenAI-shape request
        formatted_messages = []

        if system:
            formatted_messages.append({"role": "system", "content": system})

        formatted_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": formatted_messages,
            "stream": True,
            "temperature": self.config.temperature,
        }

        if tools:
            payload["tools"] = tools

        logger.debug(
            f"POProvider: sending chat to OCE ({len(formatted_messages)} messages)"
        )

        try:
            async with self.client.stream(
                "POST",
                "/api/po/chat",
                json=payload,
                headers={"Accept": "text/event-stream"},
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_text():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        # Skip empty lines and SSE comments
                        continue

                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # Strip "data: " prefix
                    if data_str.strip() == "[DONE]":
                        logger.debug("POProvider: stream complete")
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning(f"POProvider: invalid JSON chunk: {data_str[:100]}")
                        continue

                    # Extract content from OpenAI-shape chunk
                    content = self._extract_content(chunk)
                    if content:
                        yield content

        except httpx.ConnectError as e:
            logger.error(f"POProvider: connection failed - {e}")
            raise ConnectionError(f"Cannot connect to OCE at {self.config.oce_url}: {e}")
        except httpx.ReadTimeout as e:
            logger.error(f"POProvider: read timeout - {e}")
            raise TimeoutError(f"OCE response timed out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"POProvider: HTTP {e.response.status_code} - {e}")
            raise RuntimeError(f"OCE returned error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"POProvider: unexpected error - {type(e).__name__}: {e}")
            raise

    def _extract_content(self, chunk: dict) -> str | None:
        """Extract text content from an OpenAI-shape chunk."""
        # Standard OpenAI chat completion chunk format
        choices = chunk.get("choices", [])
        if not choices:
            return None

        for choice in choices:
            delta = choice.get("delta", {})
            content = delta.get("content")
            if content:
                return content

        return None

    def __repr__(self) -> str:
        return f"POProvider(model={self.config.model}, oce={self.config.oce_url})"