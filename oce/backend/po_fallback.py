"""
PO Fallback Chain — multi-provider fallback for PO cognitive field.

When the primary PO model is unavailable or degraded, requests are
automatically routed through the fallback chain:
  1. OpenRouter (aggregator)
  2. Ollama (local)
  3. Error response

This ensures the VTuber always gets a response, even during PO outages.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger("oce.po_fallback")


class FallbackError(Exception):
    """All providers in the fallback chain failed."""

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        msg = f"All {len(errors)} providers failed: " + "; ".join(
            f"{e['provider']}: {e['error'][:100]}" for e in errors
        )
        super().__init__(msg)


class FallbackChain:
    """Manages the ordered fallback chain for PO requests."""

    def __init__(self, chain: List[Dict[str, Any]] | None = None):
        # Default chain: OpenRouter → Ollama → error
        self.chain = chain or [
            {
                "provider": "openrouter",
                "endpoint": "https://openrouter.ai/api/v1/chat/completions",
                "model": "openai/gpt-4o-mini",
                "timeout": 30,
                "api_key_env": "OPENROUTER_API_KEY",
            },
            {
                "provider": "ollama",
                "endpoint": "http://localhost:11434/api/chat",
                "model": "llama3.1",
                "timeout": 60,
            },
        ]
        self._errors: List[Dict[str, Any]] = []

    async def execute(
        self,
        messages: List[Dict[str, str]],
        model: str | None = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a non-streaming request through the fallback chain."""
        errors = []

        for provider_config in self.chain:
            provider = provider_config["provider"]
            try:
                result = await self._call_provider(provider_config, messages, **kwargs)
                result["_provider"] = provider
                return result

            except Exception as e:
                logger.warning(f"Fallback provider '{provider}' failed: {e}")
                errors.append({
                    "provider": provider,
                    "error": str(e),
                    "timestamp": time.time(),
                })
                continue

        self._errors.extend(errors)
        raise FallbackError(errors)

    async def stream_execute(
        self,
        messages: List[Dict[str, str]],
        model: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming request through the fallback chain."""
        errors = []

        for provider_config in self.chain:
            provider = provider_config["provider"]
            try:
                async for chunk in self._stream_provider(provider_config, messages, **kwargs):
                    yield chunk
                return

            except Exception as e:
                logger.warning(f"Fallback provider '{provider}' failed: {e}")
                errors.append({
                    "provider": provider,
                    "error": str(e),
                    "timestamp": time.time(),
                })
                continue

        self._errors.extend(errors)
        raise FallbackError(errors)

    async def _call_provider(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a non-streaming call to a provider."""
        import httpx

        provider = config["provider"]
        endpoint = config["endpoint"]
        timeout = config.get("timeout", 30)
        model = config.get("model", "llama3.1")

        headers = {"Content-Type": "application/json"}
        api_key_env = config.get("api_key_env")
        if api_key_env:
            import os
            key = os.environ.get(api_key_env, "")
            if key:
                headers["Authorization"] = f"Bearer {key}"

        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(endpoint, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if provider == "openrouter":
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "model": data.get("model", model),
                    "usage": data.get("usage", {}),
                }
            elif provider == "ollama":
                return {
                    "response": data.get("message", {}).get("content", ""),
                    "model": model,
                }
            else:
                return {"response": str(data), "model": model}

    async def _stream_provider(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chunks from a provider."""
        import httpx

        endpoint = config["endpoint"]
        timeout = config.get("timeout", 30)
        model = config.get("model", "llama3.1")

        headers = {"Content-Type": "application/json"}
        api_key_env = config.get("api_key_env")
        if api_key_env:
            import os
            key = os.environ.get(api_key_env, "")
            if key:
                headers["Authorization"] = f"Bearer {key}"

        body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", 0.7),
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", endpoint, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        yield chunk

    def get_errors(self) -> List[Dict[str, Any]]:
        """Return all accumulated errors."""
        return list(self._errors)

    def clear_errors(self):
        """Clear the error log."""
        self._errors.clear()

    def status(self) -> Dict[str, Any]:
        """Get fallback chain status."""
        return {
            "providers": [
                {"provider": p["provider"], "model": p.get("model", "unknown")}
                for p in self.chain
            ],
            "recent_errors": len(self._errors),
            "total_errors": len(self._errors),
        }