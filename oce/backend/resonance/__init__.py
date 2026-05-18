"""
V3 Phase 1 — Resonant Signal Substrate (RSS)
Foundation layer beneath OCE/SRRA-OPH.

Transforms event->handler into signal field->resonance->observer entrainment->execution emergence.
"""

from .signal_packet import SignalPacket, SignalField
from .coherence_metrics import CoherenceEngine, CoherenceSnapshot
from .field_state import FieldStateManager, FieldState
from .boundary_mapper import BoundaryMapper, Boundary, PressureZone
from .resonance_engine import ResonanceEngine, ResonanceScore, Constraint
from .pressure_tracker import PressureTracker, PressureAlert

__all__ = [
    "SignalPacket", "SignalField",
    "CoherenceEngine", "CoherenceSnapshot",
    "FieldStateManager", "FieldState",
    "BoundaryMapper", "Boundary", "PressureZone",
    "ResonanceEngine", "ResonanceScore", "Constraint",
    "PressureTracker", "PressureAlert",
]
