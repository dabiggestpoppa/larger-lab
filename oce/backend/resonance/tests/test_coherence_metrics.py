"""
Tests for CoherenceEngine and CoherenceSnapshot.
Tests stability of coherence measurement under perturbation.
"""

import pytest
import math
from oce.backend.resonance.signal_packet import SignalPacket, SignalField
from oce.backend.resonance.coherence_metrics import CoherenceEngine, CoherenceSnapshot


class TestCoherenceSnapshot:
    """Tests for coherence snapshot data class."""

    def test_overall_coherence_perfect(self):
        snap = CoherenceSnapshot(
            timestamp=0, phase_alignment=1.0, entropy_gradient=0.0,
            resonance_density=1.0, field_tension=0.0,
            manifold_drift=0.0, attractor_stability=1.0,
        )
        assert snap.overall_coherence == pytest.approx(1.0, abs=0.01)

    def test_overall_coherence_worst(self):
        snap = CoherenceSnapshot(
            timestamp=0, phase_alignment=0.0, entropy_gradient=1.0,
            resonance_density=0.0, field_tension=1.0,
            manifold_drift=1.0, attractor_stability=0.0,
        )
        assert snap.overall_coherence == 0.0

    def test_overall_coherence_mixed(self):
        snap = CoherenceSnapshot(
            timestamp=0, phase_alignment=0.8, entropy_gradient=0.3,
            resonance_density=0.7, field_tension=0.2,
            manifold_drift=0.1, attractor_stability=0.9,
        )
        assert 0.0 < snap.overall_coherence < 1.0

    def test_is_stable(self):
        snap = CoherenceSnapshot(
            timestamp=0, phase_alignment=0.8, entropy_gradient=0.1,
            resonance_density=0.8, field_tension=0.1,
            manifold_drift=0.1, attractor_stability=0.8,
        )
        assert snap.is_stable is True

    def test_is_critical(self):
        snap = CoherenceSnapshot(
            timestamp=0, phase_alignment=0.1, entropy_gradient=0.9,
            resonance_density=0.1, field_tension=0.8,
            manifold_drift=0.9, attractor_stability=0.1,
        )
        assert snap.is_critical is True

    def test_to_dict(self):
        snap = CoherenceSnapshot(
            timestamp=1.0, phase_alignment=0.5, entropy_gradient=0.5,
            resonance_density=0.5, field_tension=0.5,
            manifold_drift=0.5, attractor_stability=0.5,
        )
        d = snap.to_dict()
        assert "overall_coherence" in d
        assert "is_stable" in d
        assert "is_critical" in d


class TestCoherenceEngine:
    """Tests for the coherence measurement engine."""

    def test_empty_engine(self):
        engine = CoherenceEngine()
        assert engine.observer_count == 0
        assert engine.latest is None

    def test_update_observer(self):
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.8)
        assert engine.observer_count == 1

    def test_remove_observer(self):
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.8)
        engine.remove_observer("obs1")
        assert engine.observer_count == 0

    def test_measure_empty_field(self):
        engine = CoherenceEngine()
        field = SignalField()
        snap = engine.measure(field)
        assert snap.resonance_density == 1.0  # No signals = perfect density

    def test_measure_with_signals(self):
        engine = CoherenceEngine()
        field = SignalField()
        field.inject(SignalPacket(source="s1", amplitude=0.8, coherence=0.9))
        field.inject(SignalPacket(source="s2", amplitude=0.2, coherence=0.3))
        snap = engine.measure(field)
        assert 0.0 <= snap.resonance_density <= 1.0

    def test_phase_alignment_single_observer(self):
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.8)
        field = SignalField()
        snap = engine.measure(field)
        assert snap.phase_alignment == 1.0  # Single observer = perfect alignment

    def test_phase_alignment_multiple_observers(self):
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.8)
        engine.update_observer("obs2", phase=0.1, coherence=0.8)
        engine.update_observer("obs3", phase=6.0, coherence=0.2)  # Opposite phase
        field = SignalField()
        snap = engine.measure(field)
        assert 0.0 <= snap.phase_alignment <= 1.0

    def test_entropy_gradient(self):
        engine = CoherenceEngine()
        field = SignalField()
        for i in range(10):
            field.inject(SignalPacket(source=f"s{i}", entropy_delta=0.8))
        snap = engine.measure(field)
        assert snap.entropy_gradient > 0.5

    def test_history_tracking(self):
        engine = CoherenceEngine()
        field = SignalField()
        for i in range(5):
            field.inject(SignalPacket(source=f"s{i}", coherence=0.5))
            engine.measure(field)
        assert len(engine.history) == 5

    def test_history_size_limit(self):
        engine = CoherenceEngine(history_size=5)
        field = SignalField()
        for i in range(10):
            engine.measure(field)
        assert len(engine.history) == 5

    def test_get_trend(self):
        engine = CoherenceEngine()
        field = SignalField()
        # Increasing coherence
        for i in range(10):
            field.inject(SignalPacket(source=f"s{i}", coherence=0.1 * (i + 1)))
            engine.measure(field)
        trend = engine.get_trend("resonance_density")
        assert isinstance(trend, float)

    def test_drift_alerts(self):
        engine = CoherenceEngine()
        field = SignalField()
        # Create high entropy situation
        for i in range(20):
            field.inject(SignalPacket(source=f"s{i}", entropy_delta=0.9, coherence=0.1))
        engine.measure(field)
        alerts = engine.get_drift_alerts()
        assert isinstance(alerts, list)

    def test_baseline_coherence(self):
        engine = CoherenceEngine()
        field = SignalField()
        field.inject(SignalPacket(source="s1", coherence=0.8))
        engine.measure(field)
        assert engine._baseline_coherence is not None

    # Stability tests

    def test_drift_injection(self):
        """Inject corrupted observer state — engine should still produce valid metrics."""
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.9)
        engine.update_observer("obs2", phase=math.pi, coherence=0.1)  # Opposite
        field = SignalField()
        for i in range(50):
            field.inject(SignalPacket(
                source=f"s{i}",
                amplitude=0.5,
                coherence=0.1 if i % 2 == 0 else 0.9,
                phase=math.pi * (i % 4),
            ))
        snap = engine.measure(field)
        assert 0.0 <= snap.overall_coherence <= 1.0
        assert isinstance(snap.is_stable, bool)

    def test_observer_death_recovery(self):
        """Remove all observers — engine should handle gracefully."""
        engine = CoherenceEngine()
        engine.update_observer("obs1", phase=0.0, coherence=0.8)
        engine.update_observer("obs2", phase=1.0, coherence=0.7)
        field = SignalField()
        snap1 = engine.measure(field)
        
        engine.remove_observer("obs1")
        engine.remove_observer("obs2")
        snap2 = engine.measure(field)
        
        assert snap2.phase_alignment == 1.0  # No observers = perfect alignment
