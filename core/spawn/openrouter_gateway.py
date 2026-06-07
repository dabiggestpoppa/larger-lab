"""
O3-B4: OpenRouterGateway
=========================
Unified cognition-provider layer.

Routes spawn requests to appropriate LLM providers via OpenRouter.
Handles model selection, rate limiting, failover, and response parsing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("spawn.gateway")


@dataclass
class ProviderConfig:
    """Configuration for a cognition provider."""
    name: str
    model: str
    base_url: str = "https://openrouter.ai/api/v1"
    max_context: int = 32768
    cost_per_1k_tokens: float = 0.0
    priority: int = 0  # Lower = higher priority
    enabled: bool = True


@dataclass
class GatewayResponse:
    """Standardized response from any provider."""
    content: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


class OpenRouterGateway:
    """
    Unified gateway to cognition providers.
    
    Manages multiple model configurations, handles failover,
    rate limiting, and standardized response formatting.
    """

    # Default provider configurations - OWL Alpha primary, auto-failover on rate limit/error
    DEFAULT_PROVIDERS: list[dict[str, Any]] = [
        {
            "name": "owl-alpha",
            "model": "openrouter/owl-alpha",
            "max_context": 1000000,
            "cost_per_1k_tokens": 0.0,
            "priority": 1,
        },
        {
            "name": "nemotron",
            "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "max_context": 1000000,
            "cost_per_1k_tokens": 0.0,
            "priority": 2,
        },
        {
            "name": "laguna-m1",
            "model": "poolside/laguna-m.1:free",
            "max_context": 1000000,
            "cost_per_1k_tokens": 0.0,
            "priority": 3,
        },
        {
            "name": "qwen-coder",
            "model": "qwen/qwen-2.5-coder-32b-instruct",
            "max_context": 131072,
            "cost_per_1k_tokens": 0.002,
            "priority": 4,
        },
        {
            "name": "ring",
            "model": "inclusionai/ring-2.6-1t",
            "max_context": 131072,
            "cost_per_1k_tokens": 0.0,
            "priority": 5,
        },
    ]

    def __init__(self, providers: list[dict[str, Any]] | None = None):
        self.providers: dict[str, ProviderConfig] = {}
        for p in (providers or self.DEFAULT_PROVIDERS):
            cfg = ProviderConfig(**p)
            self.providers[cfg.name] = cfg
        self._request_counts: dict[str, int] = {}
        self._last_request_time: dict[str, float] = {}

    def get_provider(self, model_name: str) -> ProviderConfig | None:
        """Get provider config by model name or provider name."""
        # Direct name match
        if model_name in self.providers:
            return self.providers[model_name]
        # Model string match
        for cfg in self.providers.values():
            if cfg.model == model_name:
                return cfg
        # Partial match
        for cfg in self.providers.values():
            if model_name.lower() in cfg.model.lower():
                return cfg
        return None

    def select_provider(
        self,
        task_type: str = "general",
        complexity: str = "low",
        preferred_model: str = "",
    ) -> ProviderConfig:
        """Select the best provider for a given task."""
        if preferred_model:
            cfg = self.get_provider(preferred_model)
            if cfg and cfg.enabled:
                return cfg

        # Task-based selection - OWL Alpha primary, auto-failover on rate limit/error
        task_preferences: dict[str, list[str]] = {
            "coding": ["qwen-coder", "nemotron", "laguna-m1"],
            "research": ["owl-alpha", "nemotron", "laguna-m1"],
            "architecture": ["owl-alpha", "nemotron", "laguna-m1"],
            "repair": ["qwen-coder", "nemotron", "laguna-m1"],
            "debugging": ["qwen-coder", "nemotron", "laguna-m1"],
            "orchestration": ["owl-alpha", "nemotron", "laguna-m1"],
            "visualization": ["qwen-coder", "nemotron", "laguna-m1"],
            "automation": ["qwen-coder", "nemotron", "laguna-m1"],
            "system_analysis": ["owl-alpha", "nemotron", "laguna-m1"],
            "general": ["owl-alpha", "nemotron", "laguna-m1"],
        }

        preferences = task_preferences.get(task_type, ["deepseek-chat"])
        for name in preferences:
            cfg = self.providers.get(name)
            if cfg and cfg.enabled:
                return cfg

        # Fallback to first enabled provider
        for cfg in sorted(self.providers.values(), key=lambda c: c.priority):
            if cfg.enabled:
                return cfg

        raise RuntimeError("No enabled providers available")

    def build_request(
        self,
        provider: ProviderConfig,
        messages: list[dict[str, str]],
        context: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Build a standardized request payload."""
        # Inject context into system message if provided
        if context and messages and messages[0].get("role") == "system":
            context_str = self._format_context(context)
            messages[0]["content"] = messages[0]["content"] + "\n\n" + context_str

        return {
            "model": provider.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dict into a compact string for injection."""
        parts = []
        if "objective" in context:
            obj = context["objective"]
            parts.append(f"## Objective\n{obj.get('description', '')}")
        if "constraints" in context:
            c = context["constraints"]
            parts.append(f"## Constraints\n- Max turns: {c.get('max_turns', 'N/A')}\n- Tools: {', '.join(c.get('allowed_tools', []))}")
        if "environment" in context:
            parts.append(f"## Environment\n{context['environment']}")
        return "\n\n".join(parts)

    def record_request(self, provider_name: str, tokens: int):
        """Record a request for rate limiting."""
        now = time.time()
        self._request_counts[provider_name] = self._request_counts.get(provider_name, 0) + 1
        self._last_request_time[provider_name] = now

    def check_rate_limit(self, provider_name: str, max_rpm: int = 60) -> bool:
        """Check if a provider is rate limited. Returns True if allowed."""
        count = self._request_counts.get(provider_name, 0)
        last_time = self._last_request_time.get(provider_name, 0)
        # Reset counter if more than 60 seconds have passed
        if time.time() - last_time > 60:
            self._request_counts[provider_name] = 0
            return True
        return count < max_rpm

    def get_stats(self) -> dict[str, Any]:
        """Get gateway statistics."""
        return {
            "providers": {
                name: {
                    "model": cfg.model,
                    "enabled": cfg.enabled,
                    "requests": self._request_counts.get(name, 0),
                }
                for name, cfg in self.providers.items()
            },
            "total_requests": sum(self._request_counts.values()),
        }

    async def complete(self, prompt: str, max_tokens: int = 2000, model: str = "openrouter/owl-alpha") -> str:
        """
        Send a completion request to OpenRouter with auto-failover.
        
        Tries providers in priority order on rate limit or error.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            model: Model to use (defaults to OWL Alpha)
            
        Returns:
            Response text from the model
        """
        import httpx
        import os
        
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        
        # Get initial provider or use task-based selection
        provider = self.get_provider(model) or self.select_provider(task_type="research")
        
        # Try providers in priority order (failover)
        providers_to_try = sorted(
            [p for p in self.providers.values() if p.enabled],
            key=lambda p: p.priority
        )
        
        last_error = None
        for prov in providers_to_try:
            try:
                messages = [{"role": "user", "content": prompt}]
                request = self.build_request(prov, messages, max_tokens=max_tokens)
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://larger-lab.local",
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{prov.base_url}/chat/completions",
                        json=request,
                        headers=headers,
                        timeout=120.0,
                    )
                    
                    # Check for rate limit (429) or server errors (5xx)
                    if response.status_code == 429:
                        logger.warning(f"Rate limited on {prov.name}, trying next provider")
                        last_error = f"Rate limit on {prov.name}"
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                self.record_request(prov.name, data.get("usage", {}).get("total_tokens", 0))
                logger.info(f"LLM request succeeded with {prov.name}")
                return data["choices"][0]["message"]["content"]
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {prov.name} failed: {e}")
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
