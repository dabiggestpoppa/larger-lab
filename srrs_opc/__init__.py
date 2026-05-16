"""
SRRA-OPH: Self-Repairing Recursive Architecture — Observer Patch Harness
=========================================================================
Phases 1-3 implemented. Phases 4-9 planned.
"""

# Phase 1: Foundational Observer Mesh
from .base_patch import BasePatch, CollarState
from .planner_patch import PlannerPatch
from .execution_patch import ExecutionPatch
from .memory_patch import MemoryPatch
from .repair_patch import RepairPatch
from .collar_layer import CollarLayer
from .agent_bridge import AgentBridge

# Phase 2: Reconstruction + Recoverability
from .recovery_anchors import create_anchor, get_anchor, get_top_anchors
from .drift_detector import DriftDetector
from .consistency_validator import ConsistencyValidator
from .reconstruction_synthesizer import ReconstructionSynthesizer
from .contradiction_resolver import ContradictionResolver
from .constraint_propagator import ConstraintPropagator

# Phase 3: Emergent Topology (original + Book 2 updates)
from .dynamic_coupling import DynamicCouplingEngine
from .topological_router import TopologicalRouter
from .distributed_consensus import DistributedConsensus
from .active_collar_fields import ActiveCollarField, CollarFieldManager
from .local_consensus import LocalConsensusEngine

# Phase 4: Workspace Integration (Book 2 updated)
from .capability_fields import CapabilityField, CapabilityFieldRegistry
from .workspace_integration import ToolRole, ToolAdapter
from .overlap_aware_tooling import OverlapAwareTooling, ExecutionRequest
from .reconstruction_safe_exec import ReconstructionSafeExecutor, ExecutionSafety, ExecutionRecord

# Phase 5: Long-Horizon Continuity (Book 2 updated)
from .trajectory_fields import TrajectoryFragment, TrajectoryReconstructionField
from .continuity_collars import ContinuityCollar, ContinuityCollarManager, TemporalOverlap
from .temporal_attractors import TemporalAttractor, AttractorField
from .drift_tracker import LongTermDriftTracker, DriftSignal
from .reinforcement_engine import ReinforcementEngine, ReinforcementRecord

# Phase 6: Recursive Topology Introspection
from .topology_observer import TopologyObserver, TopologySnapshot
from .collar_topology_engine import CollarTopologyEngine, CollarMetrics
from .prediction_contracts import PredictionContractManager, PredictionContract, ContractStatus

# DSPy Integration (optional)
try:
    from .dspy_contracts import DSPyContractManager, DSPyContractGenerator
except ImportError:
    DSPyContractManager = None
    DSPyContractGenerator = None

# Phase 7: Multi-Scale Overlap Ecologies
from .attractor_reasoning import AttractorReasoningEngine, AttractorState
from .structural_memory import StructuralMemoryFields, StructuralMemoryEntry, MemoryLayer

# Phase 8: Sovereign Coevolution
from .operator_patterns import OperatorPatternModel, PatternObservation
from .strategic_preferences import StrategicPreferenceModel, PreferenceVector, PreferenceDriftSignal
from .constraint_alignment import ConstraintAlignmentAdapter, Constraint, AlignmentSuggestion
from .operator_continuity import OperatorContinuityTracker, SessionAnchor, StrategicTrajectory
from .bidirectional_coherence import BidirectionalCoherenceEngine, FeedbackEvent
from .anti_manipulation import AntiManipulationSafeguards, ManipulationRisk

# Phase 9: Entropy Economics
from .coherence_yield_analyzer import CoherenceYieldAnalyzer, YieldRecord
from .entropy_budget_manager import EntropyBudgetManager, EntropyBudget
from .recoverability_economics import RecoverabilityEconomics, RecoveryCostRecord
from .adaptive_compression_engine import AdaptiveCompressionEngine, CompressionRecord
from .sync_cost_optimizer import SyncCostOptimizer, SyncDecision
from .resource_constrained_cognition import ResourceConstrainedCognition, PrioritizedOperation, OperationPriority
from .sustainability_governance import SustainabilityGovernance, OptimizationCandidate, GovernanceDecision

__all__ = [
    # Phase 1
    "BasePatch", "CollarState",
    "PlannerPatch", "ExecutionPatch", "MemoryPatch", "RepairPatch",
    "CollarLayer", "AgentBridge",
    # Phase 2
    "RecoveryAnchorStore", "create_anchor", "get_anchor", "get_top_anchors",
    "DriftDetector", "ConsistencyValidator",
    "ReconstructionSynthesizer", "ContradictionResolver", "ConstraintPropagator",
    # Phase 3
    "DynamicCouplingEngine", "TopologicalRouter", "DistributedConsensus",
    "ActiveCollarField", "CollarFieldManager",
    "LocalConsensusEngine",
    # Phase 4
    "CapabilityField", "CapabilityFieldRegistry",
    "WorkspaceIntegrationLayer", "ToolAdapter", "ToolRole",
    "OverlapAwareTooling", "ExecutionRequest",
    "ReconstructionSafeExecutor", "ExecutionSafety", "ExecutionRecord",
    # Phase 5
    "TrajectoryFragment", "TrajectoryReconstructionField",
    "ContinuityCollar", "ContinuityCollarManager", "TemporalOverlap",
    "TemporalAttractor", "AttractorField",
    "DriftTracker", "DriftSignal",
    "ReinforcementEngine", "ReinforcementRecord",
    # Phase 8
    "OperatorPatternModel", "PatternObservation",
    "StrategicPreferenceModel", "PreferenceVector", "PreferenceDriftSignal",
    "ConstraintAlignmentAdapter", "Constraint", "AlignmentSuggestion",
    "OperatorContinuityTracker", "SessionAnchor", "StrategicTrajectory",
    "BidirectionalCoherenceEngine", "FeedbackEvent",
    "AntiManipulationSafeguards", "ManipulationRisk",
    # DSPy Integration
    "DSPyContractManager", "DSPyContractGenerator",
    # Phase 9
    "CoherenceYieldAnalyzer", "YieldRecord",
    "EntropyBudgetManager", "EntropyBudget",
    "RecoverabilityEconomics", "RecoveryCostRecord",
    "AdaptiveCompressionEngine", "CompressionRecord",
    "SyncCostOptimizer", "SyncDecision",
    "ResourceConstrainedCognition", "PrioritizedOperation", "OperationPriority",
    "SustainabilityGovernance", "OptimizationCandidate", "GovernanceDecision",
]