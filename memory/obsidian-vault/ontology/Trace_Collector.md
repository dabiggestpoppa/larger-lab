# Trace Collector

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
""" O-4-B1: TraceCollector ========================= Capture all operational orchestration traces. Records task execution, routing decisions, agent spawns, topology changes, and system health for field learning and debugging. """

from __future__ import annotations
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.learning.trace_collector")

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
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    output_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class TraceCollector:
    """Captures and stores operational traces for O-4 Field Learning."""
    
    def __init__(self):
        self._traces: List[ExecutionTrace] = []
        self._storage_path: Optional[str] = None
    
    def set_storage_path(self, path: str) -> None:
        """Set persistent storage path for traces."""
        self._storage_path = path
    
    def record_trace(self, trace: ExecutionTrace) -> None:
        """Record an execution trace."""
        self._traces.append(trace)
        logger.info(f"Trace recorded: {trace.trace_id} ({trace.task_type}, {trace.status})")
    
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
        agent_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> List[ExecutionTrace]:
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
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Aggregate routing metrics from all traces."""
        # This would aggregate data for routing learning
        return {
            "total_traces": len(self._traces),
            "by_task_type": {},
            "by_model": {},
            "by_status": {},
        }
    
    def get_recent_traces(self, limit: int = 100) -> List[ExecutionTrace]:
        """Get the most recent traces."""
        return sorted(self._traces, key=lambda t: t.timestamp, reverse=True)[:limit]
```

LINKS:
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
