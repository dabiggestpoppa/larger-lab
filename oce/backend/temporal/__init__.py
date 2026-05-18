"""
V3 Phase 5 — Long-Horizon Continuity & Temporal Compression Layer
"""

from .temporal_trajectory import TemporalTrajectoryEngine, Trajectory
from .temporal_compression import TemporalCompressionEngine, CompressionResult
from .identity_engine import IdentityEngine, IdentityAttractor
from .temporal_bsp import TemporalBSPProjection, TemporalProjection
from .continuity_collar import ContinuityCollarManager, ContinuityCollar
from .glyph_evolution import GlyphEvolutionEngine, EvolvedGlyph
from .strategic_memory import StrategicMemoryEngine, StrategicInsight
from .temporal_entropy import TemporalEntropyGovernance, EntropyAssessment

__all__ = [
    "TemporalTrajectoryEngine", "Trajectory",
    "TemporalCompressionEngine", "CompressionResult",
    "IdentityEngine", "IdentityAttractor",
    "TemporalBSPProjection", "TemporalProjection",
    "ContinuityCollarManager", "ContinuityCollar",
    "GlyphEvolutionEngine", "EvolvedGlyph",
    "StrategicMemoryEngine", "StrategicInsight",
    "TemporalEntropyGovernance", "EntropyAssessment",
]
