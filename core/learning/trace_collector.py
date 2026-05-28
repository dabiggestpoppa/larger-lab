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