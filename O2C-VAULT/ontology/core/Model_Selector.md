# Model Selector

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B6: ModelSelector
=====================
Choose best cognition provider for a task.

Selects appropriate model based on task type, complexity,
and available providers.
"""

from __future__ import annotations

from typing import Any


# Model capabilities and costs
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "claude-sonnet-4": {
        "strengths": ["coding", "architecture", "complex_reasoning"],
        "max_context": 200000,
        "cost_per_1k": 0.003,
        "speed": "medium",
        "available": True,
    },
    "claude-haiku-4": {
        "strengths": ["quick_tasks", "simple_queries", "classification"],
        "max_context": 200000,
        "cost_per_1k": 0.001,
        "speed": "fast",
        "available": True,
    },
    "gpt-4o": {
        "strengths": ["coding", "reasoning", "multimodal"],
        "max_context": 128000,
        "cost_per_1k": 0.005,
        "speed": "medium",
        "available": False,  # Not configured by default
    },
    "gpt-4o-mini": {
        "strengths": ["quick_tasks", "simple_queries"],
        "max_context": 128000,
        "cost_per_1k": 0.0003,
        "speed": "fast",
        "available": False,
    },
}

# Task type -> preferred model mapping
TASK_MODEL_PREFERENCE: dict[str, list[str]] = {
    "coding": ["claude-sonnet-4", "gpt-4o", "claude-haiku-4"],
    "research": ["claude-sonnet-4", "claude-haiku-4"],
    "architecture": ["claude-sonnet-4", "gpt-4o"],
    "repair": ["claude-sonnet-4", "claude-haiku-4"],
    "debugging": ["claude-sonnet-4", "gpt-4o"],
    "orchestration": ["claude-sonnet-4", "gpt-4o"],
    "visualization": ["claude-haiku-4", "claude-sonnet-4"],
    "automation": ["claude-haiku-4", "claude-sonnet-4"],
    "system_analysis": ["claude-haiku-4", "claude-sonnet-4"],
    "general": ["claude-haiku-4", "claude-sonnet-4"],
}


class ModelSelector:
    """
    Selects the best model for a given task.

    Considers task type, complexity, cost, and availability.
    """

    def select(
        self,
        task_type: str,
        complexity: str,
        required_capabilities: list[str] | None = None,
        prefer_speed: bool = False,
    ) -> dict[str, Any]:
        """
        Select the best model for a task.

        Returns:
            {
                "model": str,
                "reason": str,
                "fallbacks": list[str],
                "estimated_cost": float,
            }
        """
        preferences = TASK_MODEL_PREFERENCE.get(task_type, ["claude-haiku-4"])

        # Filter by availability
        available = [m for m in preferences if MODEL_REGISTRY.get(m, {}).get("available", False)]

        if not available:
            return {
                "model": "claude-haiku-4",
                "reason": "default_fallback",
                "fallbacks": [],
                "estimated_cost": 0.001,
            }

        # For critical/high complexity, prefer stronger models
        if complexity in ("critical", "high") and not prefer_speed:
            for model in available:
                info = MODEL_REGISTRY.get(model, {})
                if "complex_reasoning" in info.get("strengths", []):
                    return {
                        "model": model,
                        "reason": f"complexity_{complexity}",
                        "fallbacks": available,
                        "estimated_cost": info.get("cost_per_1k", 0.003),
                    }

        # Default: first available
        selected = available[0]
        info = MODEL_REGISTRY.get(selected, {})

        return {
            "model": selected,
            "reason": "default_available",
            "fallbacks": available[1:],
            "estimated_cost": info.get("cost_per_1k", 0.001),
        }

    def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models."""
        return [
            {"name": name, **info}
            for name, info in MODEL_REGISTRY.items()
            if info.get("available", False)
        ]

```

LINKS:
[[Architecture]]
[[Cg 2 World Model Activation]]
[[Claude]]
[[Debugging]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
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
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
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
