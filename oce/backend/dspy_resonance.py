"""
🦉 RL — DSPy Resonance Optimizer for V3 Phase 1
Resonant Signal Substrate (RSS) — DSPy integration layer

Optimizes signal resonance scoring, field coherence prediction,
and signal routing using DSPy pipelines with heuristic fallbacks.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ─── Signal Model ────────────────────────────────────────────────────────

class SignalPhase(Enum):
    """Signal phase in the resonance cycle."""
    EMERGENCE = "emergence"
    AMPLIFICATION = "amplification"
    COHERENCE = "coherence"
    DISSIPATION = "dissipation"
    COLLAPSE = "collapse"


@dataclass
class SignalPacket:
    """V3 Signal Packet — matches CC's planned signal_packet.py schema."""
    signal_id: str
    source: str
    amplitude: float  # 0.0 – 1.0
    coherence: float  # 0.0 – 1.0
    phase: SignalPhase
    entropy_delta: float  # change in entropy
    boundary_tags: list[str] = field(default_factory=list)
    resonance_targets: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def resonance_score(self) -> float:
        """Base resonance score from amplitude × coherence."""
        return self.amplitude * self.coherence

    @property
    def is_viable(self) -> bool:
        """Signal is viable if coherence > 0.1 and not collapsed."""
        return self.coherence > 0.1 and self.phase != SignalPhase.COLLAPSE


# ─── Coherence Metrics ───────────────────────────────────────────────────

@dataclass
class CoherenceMetrics:
    """V3 coherence metrics — matches CC's planned coherence_metrics.py."""
    phase_alignment: float  # 0.0 – 1.0: how aligned signals are in phase
    entropy_gradient: float  # -1.0 – 1.0: direction of entropy change
    resonance_density: float  # 0.0 – 1.0: active signals / field capacity
    field_tension: float  # 0.0 – 1.0: gradient between coherence regions
    manifold_drift: float  # 0.0 – 1.0: rate of topology change
    attractor_stability: float  # 0.0 – 1.0: resistance to perturbation

    @property
    def overall_coherence(self) -> float:
        """Weighted composite coherence score."""
        weights = {
            'phase_alignment': 0.25,
            'entropy_gradient': 0.10,  # lower is better, inverted
            'resonance_density': 0.15,
            'field_tension': 0.10,  # lower is better, inverted
            'manifold_drift': 0.15,  # lower is better, inverted
            'attractor_stability': 0.25,
        }
        score = (
            weights['phase_alignment'] * self.phase_alignment +
            weights['entropy_gradient'] * (1.0 - abs(self.entropy_gradient)) +
            weights['resonance_density'] * self.resonance_density +
            weights['field_tension'] * (1.0 - self.field_tension) +
            weights['manifold_drift'] * (1.0 - self.manifold_drift) +
            weights['attractor_stability'] * self.attractor_stability
        )
        return max(0.0, min(1.0, score))

    @property
    def performance_index(self) -> float:
        """V3 performance = coherence × stability × bandwidth."""
        coherence = self.overall_coherence  # already clamped to [0, 1]
        stability = max(0.0, min(1.0, self.attractor_stability))
        bandwidth = max(0.0, min(1.0, self.resonance_density * (1.0 - self.field_tension)))
        return max(0.0, min(1.0, coherence * stability * max(bandwidth, 0.01)))


# ─── DSPy Resonance Optimizer (with heuristic fallback) ─────────────────

class ResonanceOptimizer:
    """
    DSPy-based resonance optimizer with heuristic fallback.
    When DSPy is unavailable, uses mathematical heuristics.
    """

    def __init__(self, use_dspy: bool = False):
        self.use_dspy = use_dspy
        self._dspy_available = False
        if use_dspy:
            self._try_load_dspy()

    def _try_load_dspy(self) -> None:
        """Attempt to import and configure DSPy."""
        try:
            import dspy
            self._dspy_available = True
            self._lm = dspy.LM('openai/gpt-4o-mini')
            dspy.configure(lm=self._lm)
        except (ImportError, Exception):
            self._dspy_available = False

    def score_resonance(self, signal: SignalPacket,
                        field_metrics: CoherenceMetrics) -> float:
        """Score a signal's resonance within the field."""
        if self._dspy_available:
            return self._dspy_score(signal, field_metrics)
        return self._heuristic_score(signal, field_metrics)

    def _heuristic_score(self, signal: SignalPacket,
                         metrics: CoherenceMetrics) -> float:
        """Heuristic resonance scoring."""
        base = signal.resonance_score
        alignment_bonus = metrics.phase_alignment * 0.2
        stability_bonus = metrics.attractor_stability * 0.15
        entropy_penalty = abs(metrics.entropy_gradient) * 0.1
        drift_penalty = metrics.manifold_drift * 0.1
        score = base + alignment_bonus + stability_bonus - entropy_penalty - drift_penalty
        return max(0.0, min(1.0, score))

    def _dspy_score(self, signal: SignalPacket,
                    metrics: CoherenceMetrics) -> float:
        """DSPy-based resonance scoring (fallback to heuristic on error)."""
        try:
            import dspy

            class ResonanceSignature(dspy.Signature):
                """Score signal resonance in a cognitive field."""
                signal_amplitude = dspy.InputField(desc="Signal amplitude 0-1")
                signal_coherence = dspy.InputField(desc="Signal coherence 0-1")
                phase_alignment = dspy.InputField(desc="Field phase alignment 0-1")
                attractor_stability = dspy.InputField(desc="Field attractor stability 0-1")
                entropy_gradient = dspy.InputField(desc="Field entropy gradient -1 to 1")
                resonance_score = dspy.OutputField(desc="Resonance score 0-1, high precision decimal")

            predictor = dspy.Predict(ResonanceSignature)
            result = predictor(
                signal_amplitude=str(signal.amplitude),
                signal_coherence=str(signal.coherence),
                phase_alignment=str(metrics.phase_alignment),
                attractor_stability=str(metrics.attractor_stability),
                entropy_gradient=str(metrics.entropy_gradient),
            )
            return max(0.0, min(1.0, float(result.resonance_score)))
        except Exception:
            return self._heuristic_score(signal, metrics)

    def optimize_field(self, signals: list[SignalPacket],
                       metrics: CoherenceMetrics) -> dict[str, Any]:
        """Optimize field configuration for maximum coherence."""
        viable = [s for s in signals if s.is_viable]
        if not viable:
            return {
                'recommendation': 'no_viable_signals',
                'performance_index': 0.0,
                'suggested_actions': ['reset_field', 'reduce_entropy']
            }

        scores = [(s.signal_id, self.score_resonance(s, metrics)) for s in viable]
        scores.sort(key=lambda x: x[1], reverse=True)

        avg_score = sum(s[1] for s in scores) / len(scores)
        performance = metrics.performance_index

        actions = []
        if metrics.entropy_gradient > 0.5:
            actions.append('reduce_entropy')
        if metrics.manifold_drift > 0.6:
            actions.append('stabilize_topology')
        if metrics.field_tension > 0.7:
            actions.append('relieve_tension')
        if metrics.attractor_stability < 0.3:
            actions.append('strengthen_attractors')
        if not actions and performance < 0.5:
            actions.append('general_optimization')

        return {
            'recommendation': 'optimize',
            'performance_index': performance,
            'avg_resonance_score': avg_score,
            'top_signals': scores[:5],
            'viable_count': len(viable),
            'total_count': len(signals),
            'suggested_actions': actions,
        }


# ─── Signal Router ───────────────────────────────────────────────────────

class SignalRouter:
    """
    Routes signals through the resonance field based on coherence scoring.
    Implements locality principle: no observer needs full global state.
    """

    def __init__(self, optimizer: Optional[ResonanceOptimizer] = None):
        self.optimizer = optimizer or ResonanceOptimizer()
        self._routing_table: dict[str, list[str]] = {}

    def register_route(self, source: str, targets: list[str]) -> None:
        """Register a signal route from source to targets."""
        self._routing_table[source] = targets

    def route_signal(self, signal: SignalPacket,
                     field_metrics: CoherenceMetrics) -> list[str]:
        """Determine optimal routing targets for a signal."""
        if not signal.is_viable:
            return []

        score = self.optimizer.score_resonance(signal, field_metrics)
        if score < 0.2:
            return []  # Too weak to route

        # Direct targets from routing table
        direct = self._routing_table.get(signal.signal_id, [])

        # Resonance-based targets (from signal's own targets)
        resonance_targets = [
            t for t in signal.resonance_targets
            if self._target_coherence(t, field_metrics) > score * 0.5
        ]

        # Deduplicate while preserving order
        seen = set()
        result = []
        for t in direct + resonance_targets:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result

    def _target_coherence(self, target: str,
                          metrics: CoherenceMetrics) -> float:
        """Estimate coherence of a target (hash-based deterministic)."""
        h = hashlib.md5(target.encode()).hexdigest()
        return int(h[:4], 16) / 0xFFFF


# ─── Field State Manager ─────────────────────────────────────────────────

class FieldStateManager:
    """
    Manages the state of a resonance field.
    Tracks signals, computes metrics, and provides locality views.
    """

    def __init__(self, field_id: str, capacity: int = 1000):
        self.field_id = field_id
        self.capacity = capacity
        self.signals: dict[str, SignalPacket] = {}
        self._metrics_history: list[tuple[float, CoherenceMetrics]] = []

    def add_signal(self, signal: SignalPacket) -> bool:
        """Add a signal to the field. Returns False if at capacity."""
        if len(self.signals) >= self.capacity and signal.signal_id not in self.signals:
            return False
        self.signals[signal.signal_id] = signal
        return True

    def remove_signal(self, signal_id: str) -> Optional[SignalPacket]:
        """Remove and return a signal from the field."""
        return self.signals.pop(signal_id, None)

    def compute_metrics(self) -> CoherenceMetrics:
        """Compute current coherence metrics for the field."""
        signals = [s for s in self.signals.values() if s.is_viable]
        n = len(signals)

        if n == 0:
            return CoherenceMetrics(0, 0, 0, 0, 0, 0)

        # Phase alignment: concentration of signals in dominant phase
        phase_counts: dict[str, int] = {}
        for s in signals:
            p = s.phase.value
            phase_counts[p] = phase_counts.get(p, 0) + 1
        dominant_phase_ratio = max(phase_counts.values()) / n
        phase_alignment = dominant_phase_ratio

        # Entropy gradient: average entropy delta
        avg_entropy = sum(s.entropy_delta for s in signals) / n
        entropy_gradient = max(-1.0, min(1.0, avg_entropy))

        # Resonance density: active signals / capacity
        resonance_density = n / self.capacity

        # Field tension: variance in coherence
        if n > 1:
            mean_coh = sum(s.coherence for s in signals) / n
            variance = sum((s.coherence - mean_coh) ** 2 for s in signals) / n
            field_tension = min(1.0, math.sqrt(variance))
        else:
            field_tension = 0.0

        # Manifold drift: rate of signal turnover (simplified)
        recent = [s for s in signals if time.time() - s.timestamp < 60]
        older = [s for s in signals if time.time() - s.timestamp >= 60]
        if n > 0:
            manifold_drift = len(recent) / n  # Higher = more recent activity
        else:
            manifold_drift = 0.0

        # Attractor stability: inverse of entropy gradient + drift
        attractor_stability = max(0.0, 1.0 - (abs(entropy_gradient) + manifold_drift) / 2)

        metrics = CoherenceMetrics(
            phase_alignment=phase_alignment,
            entropy_gradient=entropy_gradient,
            resonance_density=resonance_density,
            field_tension=field_tension,
            manifold_drift=manifold_drift,
            attractor_stability=attractor_stability,
        )
        self._metrics_history.append((time.time(), metrics))
        return metrics

    def get_local_view(self, observer_id: str,
                       radius: int = 10) -> list[SignalPacket]:
        """
        Get a local view of the field for an observer.
        Locality principle: no observer needs full global state.
        """
        signals = sorted(
            self.signals.values(),
            key=lambda s: s.resonance_score,
            reverse=True
        )
        return signals[:radius]

    def prune_collapsed(self) -> int:
        """Remove collapsed signals. Returns count removed."""
        collapsed = [
            sid for sid, s in self.signals.items()
            if s.phase == SignalPhase.COLLAPSE or s.coherence <= 0.05
        ]
        for sid in collapsed:
            del self.signals[sid]
        return len(collapsed)
