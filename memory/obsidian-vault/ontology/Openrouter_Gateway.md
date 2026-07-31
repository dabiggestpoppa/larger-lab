# Openrouter Gateway

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
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

    # Default provider configurations
    DEFAULT_PROVIDERS: list[dict[str, Any]] = [
        {
            "name": "qwen-coder",
            "model": "qwen/qwen-2.5-coder-32b-instruct",
            "max_context": 131072,
            "cost_per_1k_tokens": 0.002,
            "priority": 1,
        },
        {
            "name": "deepseek-chat",
            "model": "deepseek/deepseek-chat",
            "max_context": 65536,
            "cost_per_1k_tokens": 0.001,
            "priority": 2,
        },
        {
            "name": "deepseek-reasoner",
            "model": "deepseek/deepseek-reasoner",
            "max_context": 65536,
            "cost_per_1k_tokens": 0.002,
            "priority": 3,
        },
        {
            "name": "qwen-plus",
            "model": "qwen/qwen-plus",
            "max_context": 131072,
            "cost_per_1k_tokens": 0.004,
            "priority": 4,
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

        # Task-based selection
        task_preferences: dict[str, list[str]] = {
            "coding": ["qwen-coder", "deepseek-chat"],
            "research": ["deepseek-chat", "qwen-plus"],
            "architecture": ["deepseek-reasoner", "deepseek-chat"],
            "repair": ["qwen-coder", "deepseek-chat"],
            "debugging": ["qwen-coder", "deepseek-chat"],
            "orchestration": ["deepseek-chat", "qwen-plus"],
            "visualization": ["qwen-coder", "deepseek-chat"],
            "automation": ["qwen-coder", "deepseek-chat"],
            "system_analysis": ["deepseek-reasoner", "deepseek-chat"],
            "general": ["deepseek-chat", "qwen-plus"],
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

```

LINKS:
[[Architecture]]
[[Debugging]]
[[Tools]]
[[Oc2 Gateway Failures]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Configuration]]
[[Description]]
[[Formatting]]
[[Standard]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
