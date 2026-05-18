"""
Phase 10: Recursive Field Computation

Transform from continuity preservation into recursive field-based computation.
Computation through field resonance, not instruction execution.
"""

from .rcg import RecursiveComputeGraph, ComputeNode, StabilizationResult
from .prs import PositionalReferenceSystem, Position, ReferenceFrame
from .rpe import ResonancePropagationEngine, PropagationResult
from .dct import DynamicConstraintTopology, ConstraintEdge, TopologyChange
from .ace import AttractorComputeEngine, AttractorSolution

__all__ = [
    # RCG
    "RecursiveComputeGraph",
    "ComputeNode",
    "StabilizationResult",
    # PRS
    "PositionalReferenceSystem",
    "Position",
    "ReferenceFrame",
    # RPE
    "ResonancePropagationEngine",
    "PropagationResult",
    # DCT
    "DynamicConstraintTopology",
    "ConstraintEdge",
    "TopologyChange",
    # ACE
    "AttractorComputeEngine",
    "AttractorSolution",
]