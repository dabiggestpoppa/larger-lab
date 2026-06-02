# Spawn Planner

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B5: SpawnPlanner
====================
Generate task orchestration blueprint.

Creates structured spawn plans for agent execution.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SpawnBlueprint:
    """Formal orchestration schema for spawning agents."""
    blueprint_id: str
    task_type: str
    complexity: str
    timestamp: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    context_injection: dict[str, Any] = field(default_factory=dict)
    execution_boundaries: list[str] = field(default_factory=list)
    fallback_strategy: str = "retry"
    max_retries: int = 3
    timeout_seconds: int = 300


class SpawnPlanner:
    """
    Generates task orchestration blueprints.

    Creates structured plans for agent spawning with context injection,
    execution boundaries, and fallback strategies.
    """

    def create_blueprint(
        self,
        task_type: str,
        complexity: str,
        user_input: str,
        routing_path: list[str],
        capabilities: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> SpawnBlueprint:
        """
        Create a spawn blueprint for a task.

        Args:
            task_type: Classified task type
            complexity: Estimated complexity
            user_input: Original user input
            routing_path: Observer routing path
            capabilities: Capability matching result
            context: Session context

        Returns:
            SpawnBlueprint with execution plan
        """
        blueprint_id = f"bp_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build execution steps
        steps = self._build_steps(task_type, complexity, routing_path, capabilities)

        # Build context injection
        context_injection = self._build_context(task_type, context)

        # Build execution boundaries
        boundaries = self._build_boundaries(task_type, complexity)

        # Determine fallback strategy
        fallback = self._determine_fallback(complexity)

        return SpawnBlueprint(
            blueprint_id=blueprint_id,
            task_type=task_type,
            complexity=complexity,
            timestamp=timestamp,
            steps=steps,
            context_injection=context_injection,
            execution_boundaries=boundaries,
            fallback_strategy=fallback,
            max_retries=3 if complexity in ("critical", "high") else 1,
            timeout_seconds=self._get_timeout(complexity),
        )

    def _build_steps(
        self,
        task_type: str,
        complexity: str,
        routing_path: list[str],
        capabilities: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build execution steps."""
        steps: list[dict[str, Any]] = []

        for i, observer_id in enumerate(routing_path):
            step: dict[str, Any] = {
                "step_id": i + 1,
                "observer": observer_id,
                "action": self._get_observer_action(observer_id, task_type),
                "timeout": self._get_step_timeout(complexity),
                "retry_on_failure": complexity in ("critical", "high"),
            }

            if capabilities and "observer_assignments" in capabilities:
                obs_caps = capabilities["observer_assignments"].get(observer_id, [])
                step["capabilities"] = obs_caps

            steps.append(step)

        return steps

    def _get_observer_action(self, observer_id: str, task_type: str) -> str:
        """Get the action for an observer."""
        actions: dict[str, dict[str, str]] = {
            "planner": {
                "coding": "plan_implementation",
                "research": "plan_research",
                "architecture": "design_architecture",
                "repair": "plan_repair",
                "debugging": "plan_debugging",
                "orchestration": "plan_orchestration",
                "visualization": "plan_visualization",
                "automation": "plan_automation",
                "system_analysis": "plan_analysis",
                "general": "plan_response",
            },
            "execution": {
                "coding": "implement_code",
                "research": "execute_research",
                "architecture": "implement_design",
                "repair": "execute_repair",
                "debugging": "execute_debugging",
                "orchestration": "execute_orchestration",
                "visualization": "implement_ui",
                "automation": "execute_automation",
                "system_analysis": "execute_analysis",
                "general": "execute_task",
            },
            "memory": {
                "coding": "retrieve_context",
                "research": "retrieve_knowledge",
                "architecture": "retrieve_patterns",
                "repair": "retrieve_history",
                "debugging": "retrieve_logs",
                "orchestration": "retrieve_state",
                "visualization": "retrieve_data",
                "automation": "retrieve_config",
                "system_analysis": "retrieve_metrics",
                "general": "retrieve_context",
            },
            "repair": {
                "coding": "fix_errors",
                "research": "validate_findings",
                "architecture": "validate_design",
                "repair": "heal_system",
                "debugging": "diagnose_issue",
                "orchestration": "stabilize",
                "visualization": "fix_rendering",
                "automation": "fix_pipeline",
                "system_analysis": "analyze_health",
                "general": "check_consistency",
            },
        }
        return actions.get(observer_id, {}).get(task_type, "process")

    def _get_step_timeout(self, complexity: str) -> int:
        """Get timeout for a step based on complexity."""
        timeouts = {"critical": 600, "high": 300, "medium": 120, "low": 60}
        return timeouts.get(complexity, 120)

    def _get_timeout(self, complexity: str) -> int:
        """Get total timeout based on complexity."""
        timeouts = {"critical": 1800, "high": 900, "medium": 300, "low": 120}
        return timeouts.get(complexity, 300)

    def _build_context(
        self, task_type: str, session_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build context injection for spawned agents."""
        ctx: dict[str, Any] = {
            "task_type": task_type,
            "injected_at": datetime.now(timezone.utc).isoformat(),
        }
        if session_context:
            ctx["session"] = {
                k: v for k, v in session_context.items()
                if k in ("last_domain", "last_complexity", "active_goals")
            }
        return ctx

    def _build_boundaries(self, task_type: str, complexity: str) -> list[str]:
        """Build execution boundaries."""
        boundaries = ["no_file_deletion", "no_external_api_without_approval"]
        if complexity in ("critical", "high"):
            boundaries.extend([
                "no_database_writes_without_backup",
                "no_production_deployment_without_approval",
            ])
        return boundaries

    def _determine_fallback(self, complexity: str) -> str:
        """Determine fallback strategy."""
        if complexity == "critical":
            return "escalate"
        if complexity == "high":
            return "retry_with_simplification"
        return "retry"

```

LINKS:
[[Architecture]]
[[Agents]]
[[Debugging]]
[[User]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Ontology Core Summary]]
[[Action]]
[[Blueprint]]
[[Cal]]
[[Citation Workflow]]
[[Patterns]]
[[Rendering]]
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
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
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
