# Capability Matcher

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B7: CapabilityMatcher
=========================
Determine required capabilities for a task.

Matches task requirements against available observer capabilities.
"""

from __future__ import annotations

from typing import Any


# Observer capabilities registry
OBSERVER_CAPABILITIES: dict[str, list[str]] = {
    "planner": [
        "task_decomposition", "goal_setting", "strategy",
        "prioritization", "dependency_analysis", "planning",
    ],
    "execution": [
        "code_generation", "file_operations", "command_execution",
        "testing", "deployment", "automation",
    ],
    "memory": [
        "context_retrieval", "pattern_recognition", "knowledge_storage",
        "continuity_tracking", "history_analysis",
    ],
    "repair": [
        "error_detection", "self_healing", "consistency_checking",
        "rollback", "recovery", "diagnostics",
    ],
}

# Task type -> required capabilities mapping
TASK_CAPABILITIES: dict[str, list[str]] = {
    "coding": ["code_generation", "file_operations", "testing", "planning"],
    "research": ["context_retrieval", "pattern_recognition", "knowledge_storage"],
    "architecture": ["planning", "strategy", "dependency_analysis", "goal_setting"],
    "repair": ["error_detection", "self_healing", "diagnostics", "recovery"],
    "debugging": ["error_detection", "diagnostics", "context_retrieval"],
    "orchestration": ["task_decomposition", "prioritization", "planning", "automation"],
    "visualization": ["code_generation", "file_operations"],
    "automation": ["command_execution", "deployment", "automation", "planning"],
    "system_analysis": ["context_retrieval", "pattern_recognition", "continuity_tracking"],
    "general": ["planning"],
}


class CapabilityMatcher:
    """
    Matches task requirements against available observer capabilities.
    """

    def match(
        self,
        task_type: str,
        complexity: str,
        routing_path: list[str],
        available_observers: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """
        Determine required capabilities and match against observers.

        Returns:
            {
                "required": list[str],
                "available": list[str],
                "gaps": list[str],
                "coverage": float,  # 0.0-1.0
                "requires_multi_agent": bool,
                "observer_assignments": dict[str, list[str]],
            }
        """
        if available_observers is None:
            available_observers = OBSERVER_CAPABILITIES

        required = TASK_CAPABILITIES.get(task_type, ["planning"])

        # Gather all available capabilities
        all_available: set[str] = set()
        for caps in available_observers.values():
            all_available.update(caps)

        # Find gaps
        gaps = [cap for cap in required if cap not in all_available]
        covered = [cap for cap in required if cap in all_available]

        coverage = len(covered) / len(required) if required else 1.0

        # Assign capabilities to observers
        assignments: dict[str, list[str]] = {}
        for observer_id in routing_path:
            obs_caps = available_observers.get(observer_id, [])
            matched = [c for c in required if c in obs_caps]
            if matched:
                assignments[observer_id] = matched

        # Multi-agent if coverage < 1.0 or complexity is high
        requires_multi = len(gaps) > 0 or complexity in ("critical", "high")

        return {
            "required": required,
            "available": list(all_available),
            "gaps": gaps,
            "coverage": round(coverage, 2),
            "requires_multi_agent": requires_multi,
            "observer_assignments": assignments,
        }

```

LINKS:
[[Architecture]]
[[Debugging]]
[[Testing]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Composition]]
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
