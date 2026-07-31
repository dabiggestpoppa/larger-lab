"""
🦉 RL — V3 Phase 1 Integration Bridge
Connects RL's dspy_resonance module with CC's core resonance modules.

CC modules (core):
  signal_packet.py     → SignalPacket, SignalField
  coherence_metrics.py  → CoherenceEngine, CoherenceSnapshot
  resonance_engine.py   → ResonanceEngine, ResonanceScore, Constraint
  field_state.py        → FieldStateManager, FieldState
  boundary_mapper.py    → BoundaryMapper, Boundary, PressureZone
  pressure_tracker.py   → PressureTracker, PressureAlert

RL modules (optimization):
  dspy_resonance.py     → ResonanceOptimizer, SignalRouter, FieldStateManager

This bridge lets RL's DSPy optimizer and router operate on CC's core types.
"""

from __future__ import annotations
import math
import time
from typing import Any, Optional

# CC's core types
from .signal_packet import SignalPacket, SignalField
from .coherence_metrics import CoherenceEngine, CoherenceSnapshot
from .resonance_engine import ResonanceEngine, ResonanceScore, Constraint
from .field_state import FieldStateManager, FieldState
from .boundary_mapper import BoundaryMapper, Boundary, PressureZone
from .pressure_tracker import PressureTracker, PressureAlert

# RL's optimization types
from ..dspy_resonance import (
    CoherenceMetrics as RLCoherenceMetrics,
    ResonanceOptimizer,
    SignalRouter,
)


# ─── Type Adapters ───────────────────────────────────────────────────────

def cc_snapshot_to_rl_metrics(snapshot: CoherenceSnapshot) -> RLCoherenceMetrics:
    """Convert CC's CoherenceSnapshot to RL's CoherenceMetrics."""
    return RLCoherenceMetrics(
        phase_alignment=snapshot.phase_alignment,
        entropy_gradient=snapshot.entropy_gradient,
        resonance_density=snapshot.resonance_density,
        field_tension=snapshot.field_tension,
        manifold_drift=snapshot.manifold_drift,
        attractor_stability=snapshot.attractor_stability,
    )


def rl_metrics_to_cc_snapshot(metrics: RLCoherenceMetrics,
                               timestamp: float = 0.0) -> CoherenceSnapshot:
    """Convert RL's CoherenceMetrics to CC's CoherenceSnapshot."""
    return CoherenceSnapshot(
        timestamp=timestamp or time.time(),
        phase_alignment=metrics.phase_alignment,
        entropy_gradient=metrics.entropy_gradient,
        resonance_density=metrics.resonance_density,
        field_tension=metrics.field_tension,
        manifold_drift=metrics.manifold_drift,
        attractor_stability=metrics.attractor_stability,
    )


def cc_signal_to_rl_packet(signal: SignalPacket):
    """Convert CC's SignalPacket to RL's SignalPacket for optimization."""
    from ..dspy_resonance import SignalPacket as RLSignalPacket, SignalPhase
    phase_val = signal.phase
    if phase_val < math.pi / 2:
        rl_phase = SignalPhase.EMERGENCE
    elif phase_val < math.pi:
        rl_phase = SignalPhase.AMPLIFICATION
    elif phase_val < 3 * math.pi / 2:
        rl_phase = SignalPhase.COHERENCE
    elif phase_val < 2 * math.pi * 0.9:
        rl_phase = SignalPhase.DISSIPATION
    else:
        rl_phase = SignalPhase.COLLAPSE

    return RLSignalPacket(
        signal_id=signal.signal_id,
        source=signal.source,
        amplitude=signal.amplitude,
        coherence=signal.coherence,
        phase=rl_phase,
        entropy_delta=signal.entropy_delta,
        boundary_tags=list(signal.boundary_tags),
        resonance_targets=list(signal.resonance_targets),
        timestamp=signal.timestamp,
    )


# ─── Integrated Resonance Optimizer ──────────────────────────────────────

class IntegratedResonanceOptimizer:
    """
    Combines CC's ResonanceEngine with RL's DSPy ResonanceOptimizer.
    Uses CC's core scoring, enhanced by RL's optimization layer.
    """

    def __init__(self, use_dspy: bool = False):
        self.cc_engine = ResonanceEngine()
        self.rl_optimizer = ResonanceOptimizer(use_dspy=use_dspy)
        self.rl_router = SignalRouter(self.rl_optimizer)

    def score_with_cc(self, signal: SignalPacket, observer_id: str,
                      observer_phase: float,
                      observer_coherence: float) -> ResonanceScore:
        """Score resonance using CC's native engine."""
        return self.cc_engine.score_resonance(
            observer_id, observer_phase, observer_coherence, signal
        )

    def score_with_rl(self, signal: SignalPacket,
                      snapshot: CoherenceSnapshot) -> float:
        """Score resonance using RL's optimizer."""
        rl_packet = cc_signal_to_rl_packet(signal)
        rl_metrics = cc_snapshot_to_rl_metrics(snapshot)
        return self.rl_optimizer.score_resonance(rl_packet, rl_metrics)

    def hybrid_score(self, signal: SignalPacket, observer_id: str,
                     observer_phase: float, observer_coherence: float,
                     snapshot: CoherenceSnapshot,
                     cc_weight: float = 0.6) -> dict[str, Any]:
        """
        Hybrid scoring: weighted combination of CC and RL scores.
        Default: 60% CC (core engine) + 40% RL (optimization layer).
        """
        cc_result = self.score_with_cc(
            signal, observer_id, observer_phase, observer_coherence
        )
        rl_score = self.score_with_rl(signal, snapshot)

        combined = cc_weight * cc_result.score + (1 - cc_weight) * rl_score

        return {
            'combined_score': round(combined, 4),
            'cc_score': round(cc_result.score, 4),
            'rl_score': round(rl_score, 4),
            'cc_viable': cc_result.is_viable,
            'signal_id': signal.signal_id,
            'observer_id': observer_id,
        }

    def optimize_field(self, field_manager: FieldStateManager,
                       boundary_mapper: BoundaryMapper,
                       pressure_tracker: PressureTracker) -> dict[str, Any]:
        """
        Full field optimization using all three layers.
        """
        field_state = field_manager.current_state
        coherence = field_manager.measure_coherence()
        boundaries = boundary_mapper.get_critical_boundaries()
        new_alerts = pressure_tracker.scan(field_manager.signal_field, boundary_mapper)

        rl_metrics = cc_snapshot_to_rl_metrics(coherence)
        signals = field_manager.signal_field.signals
        rl_signals = [cc_signal_to_rl_packet(s) for s in signals]
        rl_result = self.rl_optimizer.optimize_field(rl_signals, rl_metrics)

        return {
            'field_health': round(field_state.health, 4),
            'field_stable': field_state.is_stable,
            'coherence': round(coherence.overall_coherence, 4),
            'critical_boundaries': len(boundaries),
            'active_alerts': len(new_alerts),
            'rl_recommendation': rl_result['recommendation'],
            'rl_performance_index': round(rl_result['performance_index'], 4),
            'rl_actions': rl_result['suggested_actions'],
            'viable_signals': rl_result['viable_count'],
            'total_signals': rl_result['total_count'],
        }


# ─── Integrated Signal Router ────────────────────────────────────────────

class IntegratedSignalRouter:
    """
    Combines CC's resonance-based routing with RL's locality-based routing.
    """

    def __init__(self, optimizer: Optional[IntegratedResonanceOptimizer] = None):
        self.optimizer = optimizer or IntegratedResonanceOptimizer()
        self.rl_router = SignalRouter(self.optimizer.rl_optimizer)

    def route(self, signal: SignalPacket, field_manager: FieldStateManager,
              observers: dict[str, tuple[float, float]]) -> list[str]:
        """
        Route a signal through the field using both CC and RL routing.
        observers: dict of observer_id -> (phase, coherence)
        """
        coherence = field_manager.measure_coherence()

        best_observer = self.optimizer.cc_engine.find_best_observer(
            signal, observers
        )

        rl_packet = cc_signal_to_rl_packet(signal)
        rl_metrics = cc_snapshot_to_rl_metrics(coherence)
        rl_targets = self.rl_router.route_signal(rl_packet, rl_metrics)

        targets = []
        if best_observer:
            targets.append(best_observer)
        targets.extend(rl_targets)

        seen = set()
        result = []
        for t in targets:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result
