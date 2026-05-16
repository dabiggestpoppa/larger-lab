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
]