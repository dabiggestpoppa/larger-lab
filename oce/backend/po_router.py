"""
PO Multi-Model Router — selects the best LLM provider for a given request.

Supports routing across:
- PO (OCE cognitive field) — primary
- OpenAI-compatible endpoints
- Ollama (local)
- Fallback chain (OpenRouter → Ollama → error)

Used by the streaming thought layer and directly by the PO Provider adapter.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_router")


@dataclass
class ModelInfo:
    """Information about an available model."""

    id: str
    name: str
    provider: str
    capabilities: List[str] = field(default_factory=list)
    context_window: int = 4096
    max_output: int = 2048
    supports_streaming: bool = True
    status: str = "available"  # available, degraded, unavailable


@dataclass
class RouteDecision:
    """The router's decision for a given request."""

    model_id: str
    provider: str
    confidence: float = 1.0
    reason: str = ""
    fallback_chain: List[str] = field(default_factory=list)


class ModelRouter:
    """Routes chat requests to the appropriate LLM model/provider."""

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._routing_rules: List[Dict[str, Any]] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register default models and routing rules."""
        # PO is always the primary model
        self.register_model(ModelInfo(
            id="po",
            name="PO Cognitive Field",
            provider="oce",
            capabilities=["chat", "streaming", "tools", "memory"],
            context_window=16384,
            max_output=8192,
            supports_streaming=True,
        ))

        # OpenAI-compatible models
        self.register_model(ModelInfo(
            id="openai/gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["chat", "streaming", "tools"],
        ))
        self.register_model(ModelInfo(
            id="openai/gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            capabilities=["chat", "streaming"],
        ))

        # Ollama local models
        self.register_model(ModelInfo(
            id="ollama/llama3.1",
            name="Llama 3.1 (Ollama)",
            provider="ollama",
            capabilities=["chat", "streaming"],
        ))

        # Default routing rules (ordered by priority)
        self._routing_rules = [
            {
                "name": "po_priority",
                "condition": lambda req: True,  # Always try PO first
                "model": "po",
                "provider": "oce",
            },
        ]

    def register_model(self, model: ModelInfo):
        """Register a new model."""
        self._models[model.id] = model

    def deregister_model(self, model_id: str):
        """Remove a model from the registry."""
        self._models.pop(model_id, None)

    def get_model(self, model_id: str) -> ModelInfo | None:
        """Get model info by ID."""
        return self._models.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        """List all registered models."""
        return list(self._models.values())

    def list_available_models(self) -> List[ModelInfo]:
        """List only available models."""
        return [m for m in self._models.values() if m.status == "available"]

    def route(self, query: str, preferred_model: str | None = None) -> RouteDecision:
        """
        Determine the best model for a given query.

        Args:
            query: The user's query or last message
            preferred_model: Override to use a specific model

        Returns:
            RouteDecision with the selected model and fallback chain
        """
        # If a specific model is requested, use it
        if preferred_model and preferred_model in self._models:
            model = self._models[preferred_model]
            if model.status == "available":
                return RouteDecision(
                    model_id=preferred_model,
                    provider=model.provider,
                    reason=f"Explicitly requested: {preferred_model}",
                    fallback_chain=self._build_fallback_chain(preferred_model),
                )

        # Apply routing rules
        for rule in self._routing_rules:
            try:
                if rule["condition"](query):
                    model_id = rule["model"]
                    if model_id in self._models and self._models[model_id].status == "available":
                        return RouteDecision(
                            model_id=model_id,
                            provider=self._models[model_id].provider,
                            reason=rule.get("name", "routing_rule"),
                            fallback_chain=self._build_fallback_chain(model_id),
                        )
            except Exception:
                continue

        # Fallback: any available model
        for model in self._models.values():
            if model.status == "available":
                return RouteDecision(
                    model_id=model.id,
                    provider=model.provider,
                    reason="first_available",
                    fallback_chain=self._build_fallback_chain(model.id),
                )

        return RouteDecision(
            model_id="",
            provider="",
            confidence=0.0,
            reason="no_available_models",
        )

    def _build_fallback_chain(self, primary_model_id: str) -> List[str]:
        """Build ordered fallback chain for a given primary model."""
        chain = []
        # PO primary → OpenAI → Ollama
        if primary_model_id == "po":
            chain = ["openai/gpt-4o", "openai/gpt-4o-mini", "ollama/llama3.1"]
        elif primary_model_id.startswith("openai"):
            chain = ["po", "ollama/llama3.1"]
        elif primary_model_id.startswith("ollama"):
            chain = ["po", "openai/gpt-4o"]
        else:
            chain = ["po", "openai/gpt-4o", "ollama/llama3.1"]

        # Filter to only available models
        return [m for m in chain if m in self._models and self._models[m].status == "available"]

    def set_model_status(self, model_id: str, status: str):
        """Update model availability status."""
        if model_id in self._models:
            self._models[model_id].status = status

    def health_check(self) -> Dict[str, Any]:
        """Check health of all registered models."""
        return {
            model_id: {
                "status": model.status,
                "provider": model.provider,
                "supports_streaming": model.supports_streaming,
            }
            for model_id, model in self._models.items()
        }

    def route_with_context(
        self,
        query: str,
        estimated_tokens: int = 0,
        preferred_model: str | None = None,
        require_streaming: bool = False,
    ) -> RouteDecision:
        """
        Context-aware routing that considers token count and capabilities.

        Args:
            query: The user's query
            estimated_tokens: Estimated token count for the request
            preferred_model: Override to use a specific model
            require_streaming: If True, only route to streaming-capable models

        Returns:
            RouteDecision with the best model for the request
        """
        # Filter models by requirements
        candidates = []
        for mid, model in self._models.items():
            if model.status != "available":
                continue
            if require_streaming and not model.supports_streaming:
                continue
            if estimated_tokens > 0 and estimated_tokens > model.context_window:
                continue
            candidates.append(model)

        if not candidates:
            # Relax constraints — just find any available model
            candidates = [m for m in self._models.values() if m.status == "available"]

        if not candidates:
            return RouteDecision(
                model_id="",
                provider="",
                confidence=0.0,
                reason="no_available_models",
            )

        # If preferred model is in candidates, use it
        if preferred_model:
            for m in candidates:
                if m.id == preferred_model:
                    return RouteDecision(
                        model_id=m.id,
                        provider=m.provider,
                        reason=f"preferred:{preferred_model}",
                        fallback_chain=self._build_fallback_chain(m.id),
                    )

        # Default: PO first, then by capability match
        for m in candidates:
            if m.id == "po":
                return RouteDecision(
                    model_id="po",
                    provider="oce",
                    reason="po_primary",
                    confidence=1.0,
                    fallback_chain=self._build_fallback_chain("po"),
                )

        # First available candidate
        m = candidates[0]
        return RouteDecision(
            model_id=m.id,
            provider=m.provider,
            reason="first_available",
            fallback_chain=self._build_fallback_chain(m.id),
        )

    def get_routing_stats(self) -> Dict[str, Any]:
        """Return routing statistics."""
        return {
            "total_models": len(self._models),
            "available_models": len([m for m in self._models.values() if m.status == "available"]),
            "routing_rules": len(self._routing_rules),
            "model_ids": list(self._models.keys()),
        }