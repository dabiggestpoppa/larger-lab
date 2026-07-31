# Trace Feedback

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O3-B8: TraceFeedback
=====================
Feed traces back to field memory.

Captures execution traces from spawned agents and feeds them back
to the field memory system for learning and analysis.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.trace")


@dataclass
class ExecutionTrace:
    """A single execution trace from a spawned agent."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str = ""
    plan_id: str = ""
    task_type: str = ""
    model: str = ""
    status: str = ""  # complete, failed, timeout
    turns_used: int = 0
    tokens_used: int = 0
    duration_seconds: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    output_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class TraceFeedback:
    """
    Captures and feeds execution traces back to field memory.
    
    Records what happened during agent execution: tool calls,
    errors, results, timing. This data feeds into O-4 Field Learning.
    """

    def __init__(self):
        self._traces: list[ExecutionTrace] = []

    def record_trace(self, trace: ExecutionTrace) -> None:
        """Record an execution trace."""
        self._traces.append(trace)
        logger.info(
            f"Trace recorded: {trace.trace_id} ({trace.task_type}, {trace.status})"
        )

    def create_trace(
        self,
        agent_id: str,
        plan_id: str,
        task_type: str,
        model: str,
        status: str,
        **kwargs: Any,
    ) -> ExecutionTrace:
        """Create and record a new trace."""
        trace = ExecutionTrace(
            agent_id=agent_id,
            plan_id=plan_id,
            task_type=task_type,
            model=model,
            status=status,
            **kwargs,
        )
        self.record_trace(trace)
        return trace

    def get_traces(
        self,
        agent_id: str | None = None,
        task_type: str | None = None,
        status: str | None = None,
        plan_id: str | None = None,
    ) -> list[ExecutionTrace]:
        """Query traces with optional filters."""
        results = self._traces
        if agent_id:
            results = [t for t in results if t.agent_id == agent_id]
        if task_type:
            results = [t for t in results if t.task_type == task_type]
        if status:
            results = [t for t in results if t.status == status]
        if plan_id:
            results = [t for t in results if t.plan_id == plan_id]
        return results

    def get_routing_metrics(self) -> dict[str, Any]:
        """Aggregate routing metrics from all traces."""
        if not self._traces:
            return {"total_traces": 0}

        total = len(self._traces)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_model: dict[str, int] = {}
        total_tokens = 0
        total_turns = 0
        total_duration = 0.0

        for t in self._traces:
            by_type[t.task_type] = by_type.get(t.task_type, 0) + 1
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_model[t.model] = by_model.get(t.model, 0) + 1
            total_tokens += t.tokens_used
            total_turns += t.turns_used
            total_duration += t.duration_seconds

        return {
            "total_traces": total,
            "by_type": by_type,
            "by_status": by_status,
            "by_model": by_model,
            "total_tokens": total_tokens,
            "total_turns": total_turns,
            "avg_tokens": round(total_tokens / total, 1) if total else 0,
            "avg_turns": round(total_turns / total, 1) if total else 0,
            "avg_duration": round(total_duration / total, 1) if total else 0,
            "success_rate": round(
                by_status.get("complete", 0) / total * 100, 1
            ) if total else 0,
        }

    def get_failure_analysis(self) -> list[dict[str, Any]]:
        """Analyze failed traces for patterns."""
        failed = [t for t in self._traces if t.status in ("failed", "timeout")]
        analysis = []
        for t in failed:
            analysis.append({
                "trace_id": t.trace_id,
                "task_type": t.task_type,
                "model": t.model,
                "status": t.status,
                "errors": t.errors[:5],
                "turns_used": t.turns_used,
            })
        return analysis

```

LINKS:
[[Agents]]
[[Quality Review Feedback]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Patterns]]
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
