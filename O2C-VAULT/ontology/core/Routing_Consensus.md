# Routing Consensus

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B3: RoutingConsensus
========================
Determine best orchestration path through the observer field.

Decides which observers should handle a task and in what order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Observer routing map: which observers handle which task types
OBSERVER_ROUTING: dict[str, list[str]] = {
    "coding": ["planner", "execution", "repair"],
    "research": ["planner", "memory"],
    "architecture": ["planner", "memory", "execution"],
    "repair": ["repair", "planner", "execution"],
    "debugging": ["repair", "planner", "memory"],
    "orchestration": ["planner", "execution", "memory", "repair"],
    "visualization": ["planner", "execution"],
    "automation": ["execution", "planner"],
    "system_analysis": ["planner", "memory", "repair"],
    "general": ["planner"],
}

# Complexity-based routing adjustments
COMPLEXITY_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "critical": {
        "coding": ["planner", "repair", "execution", "memory"],
        "orchestration": ["planner", "repair", "execution", "memory"],
    },
    "high": {
        "coding": ["planner", "repair", "execution"],
        "architecture": ["planner", "memory", "repair", "execution"],
    },
}


@dataclass
class RoutingDecision:
    """Routing decision for a task."""
    path: list[str]
    primary_observer: str
    fallback_observers: list[str]
    strategy: str  # "direct", "cascade", "parallel", "consensus"
    estimated_steps: int


class RoutingConsensus:
    """
    Determines the best orchestration path for a task.

    Uses task type, complexity, and current observer availability
    to route tasks through the observer field.
    """

    def __init__(self):
        self._routing_history: list[dict[str, Any]] = []

    def determine_path(
        self,
        task_type: str,
        complexity: str,
        signals: list[dict[str, Any]] | None = None,
        observer_availability: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """
        Determine the best routing path for a task.

        Returns:
            {
                "path": list[str],
                "primary": str,
                "fallbacks": list[str],
                "strategy": str,
                "estimated_steps": int,
            }
        """
        # Get base routing
        base_path = OBSERVER_ROUTING.get(task_type, ["planner"])

        # Apply complexity overrides
        if complexity in COMPLEXITY_OVERRIDES:
            overrides = COMPLEXITY_OVERRIDES[complexity]
            if task_type in overrides:
                base_path = overrides[task_type]

        # Filter by availability
        if observer_availability:
            available_path = [
                obs for obs in base_path
                if observer_availability.get(obs, True)
            ]
            if available_path:
                base_path = available_path

        # Determine strategy
        strategy = self._determine_strategy(task_type, complexity, base_path)

        # Build result
        result = {
            "path": base_path,
            "primary": base_path[0] if base_path else "planner",
            "fallbacks": base_path[1:] if len(base_path) > 1 else [],
            "strategy": strategy,
            "estimated_steps": len(base_path),
        }

        self._routing_history.append({
            "task_type": task_type,
            "complexity": complexity,
            "result": result,
        })

        return result

    def _determine_strategy(
        self, task_type: str, complexity: str, path: list[str]
    ) -> str:
        """Determine routing strategy."""
        if len(path) == 1:
            return "direct"
        if complexity in ("critical", "high"):
            return "cascade"
        if task_type in ("orchestration", "automation"):
            return "parallel"
        if len(path) >= 3:
            return "consensus"
        return "cascade"

    def get_routing_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent routing history."""
        return self._routing_history[-limit:]

```

LINKS:
[[Architecture]]
[[Debugging]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Server]]
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
[[Memory]]
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
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
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
