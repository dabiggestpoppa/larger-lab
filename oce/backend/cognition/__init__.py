"""
V3 Phase 6 — Resonant Cognition / BSP Emergence Layer
The system becomes a self-observing adaptive resonance system.
"""

from .boundary_engine import BoundaryEngine, Boundary
from .projection_engine import ProjectionEngine, FieldVector
from .resonance_mapper import ResonanceMapper, ResonanceSnapshot
from .attractor_engine import AttractorEngine, CognitiveAttractor
from .self_model import SelfModelEngine, SelfObservation

__all__ = [
    "BoundaryEngine", "Boundary",
    "ProjectionEngine", "FieldVector",
    "ResonanceMapper", "ResonanceSnapshot",
    "AttractorEngine", "CognitiveAttractor",
    "SelfModelEngine", "SelfObservation",
]
