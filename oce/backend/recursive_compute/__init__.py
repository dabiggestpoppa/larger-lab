"""
V3 Phase 10 — Recursive Field Computation
Transform from continuity preservation into recursive field-based computation.

Core shift: continuity preservation → recursive field-based computation
"""

from .recursive_compute_graph import RecursiveComputeGraph, ComputeNode, ComputeResult
from .positional_reference_system import PositionalReferenceSystem, ReferenceFrame, Position
from .resonance_propagation_engine import ResonancePropagationEngine, PropagationWave
from .dynamic_constraint_topology import DynamicConstraintTopology, Constraint, TopologyState
from .attractor_compute_engine import AttractorComputeEngine, ComputeAttractor, ConvergenceResult

__all__ = [
    "RecursiveComputeGraph", "ComputeNode", "ComputeResult",
    "PositionalReferenceSystem", "ReferenceFrame", "Position",
    "ResonancePropagationEngine", "PropagationWave",
    "DynamicConstraintTopology", "Constraint", "TopologyState",
    "AttractorComputeEngine", "ComputeAttractor", "ConvergenceResult",
]
