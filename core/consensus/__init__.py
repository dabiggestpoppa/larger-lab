"""
Observer Consensus + Task Routing
==================================
O-2 Phase: Observer Consensus components.

Components:
- ObserverConsensus: Coordinate distributed observer decision-making
- TaskClassifier: Determine task type (9 categories)
- RoutingConsensus: Determine best orchestration path
- ComplexityScorer: Estimate operational complexity (4 levels)
- SpawnPlanner: Generate task orchestration blueprint
- ModelSelector: Choose best cognition provider
- CapabilityMatcher: Determine required capabilities
- ConsensusMemory: Store orchestration outcome history
- ObserverSpecialization: Allow observers to specialize
- ConsensusReplay: Replay observer decisions
"""

from .observer_consensus import ObserverConsensus
from .task_classifier import TaskClassifier, TaskType
from .routing_consensus import RoutingConsensus
from .complexity_scorer import ComplexityScorer
from .spawn_planner import SpawnPlanner
from .model_selector import ModelSelector
from .capability_matcher import CapabilityMatcher
from .consensus_memory import ConsensusMemory
from .observer_specialization import ObserverSpecialization
from .consensus_replay import ConsensusReplay

__all__ = [
    "ObserverConsensus",
    "TaskClassifier",
    "TaskType",
    "RoutingConsensus",
    "ComplexityScorer",
    "SpawnPlanner",
    "ModelSelector",
    "CapabilityMatcher",
    "ConsensusMemory",
    "ObserverSpecialization",
    "ConsensusReplay",
]
