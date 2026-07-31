"""
Phase 1.6 — Autonomous Cognitive Orchestration

The executive nervous system of OCE.
Coordinates all cognition subsystems (ingestion, synthesis, retrieval, etc.)
into one unified, self-routing, task-aware system.

Subphases:
- 1.6.1: Orchestration Core (controller, task dispatcher, execution state)
- 1.6.2: Agent Runtime (persistent cognitive workers, registry, state tracking)
- 1.6.3: Planner Engine (task decomposition, execution sequencing)
- 1.6.4: Workflow Topology (DAG-based execution graphs)
- 1.6.5: Memory-Aware Execution (context injection, continuity tracking)
- 1.6.6: Reflection Loops (self-correction, verification, retry)
- 1.6.7: Recursive Scheduling (autonomous recurring cognition)
- 1.6.8: Execution Governance (safety, recursion limits, permissions)
"""

from .controller import OrchestrationController, TaskPriority, TaskState
from .planner import PlannerEngine
from .workflow import WorkflowEngine, WorkflowNode, WorkflowEdge
from .scheduler import SchedulerEngine, ScheduleFrequency
from .governance import GovernanceEngine
from .agents import AgentRuntime, AgentSpec, AgentState
from .memory import ContextInjector
from .reflection import ReflectionEngine

__all__ = [
    "OrchestrationController",
    "TaskPriority",
    "TaskState",
    "PlannerEngine",
    "WorkflowEngine",
    "WorkflowNode",
    "WorkflowEdge",
    "SchedulerEngine",
    "ScheduleFrequency",
    "GovernanceEngine",
    "AgentRuntime",
    "AgentSpec",
    "AgentState",
    "ContextInjector",
    "ReflectionEngine",
]
