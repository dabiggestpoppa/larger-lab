"""
V3 Phase 3 — Resonant Topology & BSP Emergence Layer
Transforms isolated agents into dynamic resonance structures.
"""

from .collar_field import CollarFieldEngine, CollarField
from .bsp_projection import BSPProjectionEngine, TrajectoryProjection
from .resonance_router import ResonanceRouter, Route
from .glyph_engine import GlyphEngine, GlyphToken, GLYPH_MAP
from .field_pressure import FieldPressureSystem, PressureReading
from .attractor_stability import AttractorStabilityLayer, StabilityState
from .topology_metrics import TopologyMetrics, TopologyHealth

__all__ = [
    "CollarFieldEngine", "CollarField",
    "BSPProjectionEngine", "TrajectoryProjection",
    "ResonanceRouter", "Route",
    "GlyphEngine", "GlyphToken", "GLYPH_MAP",
    "FieldPressureSystem", "PressureReading",
    "AttractorStabilityLayer", "StabilityState",
    "TopologyMetrics", "TopologyHealth",
]
