"""
O-4: Operational Trace + Field Learning
========================================
Learning layer that extracts stable patterns from operational traces,
improves routing decisions, and maintains long-horizon workflow memory.
"""

from core.learning.trace_collector import TraceCollector, ExecutionTrace
from core.learning.operational_replay import OperationalReplay, ReplayEvent
from core.learning.workflow_distiller import WorkflowDistiller, WorkflowPattern, TraceEntry
from core.learning.routing_learning import RoutingLearning, RoutingPattern
from core.learning.failure_analyzer import FailureAnalyzer, FailurePattern, FailureReport
from core.learning.topology_learning import TopologyLearning, TopologySnapshot, TopologyCorrelation
from core.learning.observer_evolution import ObserverEvolution, EvolutionRecord
from core.learning.pattern_memory import PatternMemory, StoredPattern
from core.learning.workflow_memory import WorkflowMemory, WorkflowEntry
from core.learning.operational_scoring import OperationalScoring, ScoreEntry
from core.learning.adaptation_engine import AdaptationEngine, AdaptationAction

__all__ = [
    "TraceCollector",
    "ExecutionTrace",
    "OperationalReplay",
    "ReplayEvent",
    "WorkflowDistiller",
    "WorkflowPattern",
    "TraceEntry",
    "RoutingLearning",
    "RoutingPattern",
    "FailureAnalyzer",
    "FailurePattern",
    "FailureReport",
    "TopologyLearning",
    "TopologySnapshot",
    "TopologyCorrelation",
    "ObserverEvolution",
    "EvolutionRecord",
    "PatternMemory",
    "StoredPattern",
    "WorkflowMemory",
    "WorkflowEntry",
    "OperationalScoring",
    "ScoreEntry",
    "AdaptationEngine",
    "AdaptationAction",
]
