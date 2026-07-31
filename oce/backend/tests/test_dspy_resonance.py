"""
🦉 RL — Tests for DSPy Resonance Optimizer (V3 Phase 1)
"""

import time
import pytest

from oce.backend.dspy_resonance import (
    CoherenceMetrics,
    FieldStateManager,
    ResonanceOptimizer,
    SignalPacket,
    SignalPhase,
    SignalRouter,
)


# ─── SignalPacket Tests ──────────────────────────────────────────────────

class TestSignalPacket:
    def test_basic_creation(self):
        s = SignalPacket(
            signal_id="sig-001",
            source="test",
            amplitude=0.8,
            coherence=0.9,
            phase=SignalPhase.COHERENCE,
            entropy_delta=0.1,
        )
        assert s.signal_id == "sig-001"
        assert s.amplitude == 0.8
        assert s.coherence == 0.9

    def test_resonance_score(self):
        s = SignalPacket("s1", "src", 0.8, 0.5, SignalPhase.COHERENCE, 0.0)
        assert s.resonance_score == pytest.approx(0.4)

    def test_is_viable_high_coherence(self):
        s = SignalPacket("s1", "src", 0.5, 0.9, SignalPhase.COHERENCE, 0.0)
        assert s.is_viable is True

    def test_is_viable_low_coherence(self):
        s = SignalPacket("s1", "src", 0.5, 0.05, SignalPhase.COHERENCE, 0.0)
        assert s.is_viable is False

    def test_is_viable_collapsed(self):
        s = SignalPacket("s1", "src", 0.5, 0.9, SignalPhase.COLLAPSE, 0.0)
        assert s.is_viable is False

    def test_boundary_tags(self):
        s = SignalPacket("s1", "src", 0.5, 0.5, SignalPhase.EMERGENCE, 0.0,
                         boundary_tags=["edge", "boundary"])
        assert "edge" in s.boundary_tags

    def test_resonance_targets(self):
        s = SignalPacket("s1", "src", 0.5, 0.5, SignalPhase.EMERGENCE, 0.0,
                         resonance_targets=["field-a", "field-b"])
        assert len(s.resonance_targets) == 2


# ─── CoherenceMetrics Tests ──────────────────────────────────────────────

class TestCoherenceMetrics:
    def test_perfect_coherence(self):
        m = CoherenceMetrics(1.0, 0.0, 1.0, 0.0, 0.0, 1.0)
        assert m.overall_coherence == pytest.approx(1.0)
        assert m.performance_index == pytest.approx(1.0)

    def test_zero_coherence(self):
        m = CoherenceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        # entropy_gradient=0 contributes 0.1 weight * (1-0) = 0.1
        # attractor_stability=0 contributes 0.25 * 0 = 0
        # Total = 0.1 from entropy_gradient + 0.15*0 from density + 0.1*0 from tension + 0.15*0 from drift = 0.1
        # But phase_alignment=0 contributes 0, so total = 0.1 + 0.25*0 = 0.1
        # Actually: 0.25*0 + 0.1*(1-0) + 0.15*0 + 0.1*(1-0) + 0.15*(1-0) + 0.25*0 = 0+0.1+0+0.1+0.15+0 = 0.35
        assert m.overall_coherence == pytest.approx(0.35)

    def test_performance_index_formula(self):
        m = CoherenceMetrics(0.8, 0.2, 0.6, 0.3, 0.2, 0.9)
        perf = m.performance_index
        assert 0.0 <= perf <= 1.0

    def test_high_entropy_reduces_coherence(self):
        m_low = CoherenceMetrics(0.8, 0.0, 0.8, 0.1, 0.1, 0.8)
        m_high = CoherenceMetrics(0.8, 0.9, 0.8, 0.1, 0.1, 0.8)
        assert m_low.overall_coherence > m_high.overall_coherence

    def test_high_drift_reduces_coherence(self):
        m_low = CoherenceMetrics(0.8, 0.0, 0.8, 0.1, 0.1, 0.8)
        m_high = CoherenceMetrics(0.8, 0.0, 0.8, 0.1, 0.9, 0.8)
        assert m_low.overall_coherence > m_high.overall_coherence

    def test_clamping(self):
        # CoherenceMetrics doesn't clamp inputs — it's a data class
        # But overall_coherence and performance_index clamp their outputs
        m = CoherenceMetrics(2.0, 5.0, 3.0, -1.0, -2.0, 2.0)
        assert 0.0 <= m.overall_coherence <= 1.0
        assert 0.0 <= m.performance_index <= 1.0


# ─── ResonanceOptimizer Tests ────────────────────────────────────────────

class TestResonanceOptimizer:
    def test_heuristic_score_basic(self):
        opt = ResonanceOptimizer(use_dspy=False)
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0)
        m = CoherenceMetrics(0.8, 0.1, 0.5, 0.2, 0.1, 0.9)
        score = opt.score_resonance(s, m)
        assert 0.0 <= score <= 1.0

    def test_heuristic_score_high_quality(self):
        opt = ResonanceOptimizer(use_dspy=False)
        s = SignalPacket("s1", "src", 1.0, 1.0, SignalPhase.COHERENCE, 0.0)
        m = CoherenceMetrics(1.0, 0.0, 0.5, 0.0, 0.0, 1.0)
        score = opt.score_resonance(s, m)
        assert score > 0.9

    def test_heuristic_score_low_quality(self):
        opt = ResonanceOptimizer(use_dspy=False)
        s = SignalPacket("s1", "src", 0.1, 0.1, SignalPhase.COLLAPSE, 0.0)
        m = CoherenceMetrics(0.1, 0.9, 0.1, 0.9, 0.9, 0.1)
        score = opt.score_resonance(s, m)
        assert score < 0.3

    def test_optimize_field_empty(self):
        opt = ResonanceOptimizer(use_dspy=False)
        m = CoherenceMetrics(0, 0, 0, 0, 0, 0)
        result = opt.optimize_field([], m)
        assert result['recommendation'] == 'no_viable_signals'

    def test_optimize_field_with_signals(self):
        opt = ResonanceOptimizer(use_dspy=False)
        signals = [
            SignalPacket(f"s{i}", "src", 0.5 + i * 0.1, 0.6 + i * 0.05,
                         SignalPhase.COHERENCE, 0.05)
            for i in range(5)
        ]
        m = CoherenceMetrics(0.7, 0.2, 0.5, 0.3, 0.2, 0.8)
        result = opt.optimize_field(signals, m)
        assert result['recommendation'] == 'optimize'
        assert result['viable_count'] == 5
        assert 'performance_index' in result

    def test_optimize_field_suggests_entropy_reduction(self):
        opt = ResonanceOptimizer(use_dspy=False)
        signals = [SignalPacket("s1", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.8)]
        m = CoherenceMetrics(0.5, 0.7, 0.5, 0.3, 0.2, 0.5)
        result = opt.optimize_field(signals, m)
        assert 'reduce_entropy' in result['suggested_actions']

    def test_optimize_field_suggests_topology_stabilization(self):
        opt = ResonanceOptimizer(use_dspy=False)
        signals = [SignalPacket("s1", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.1)]
        m = CoherenceMetrics(0.5, 0.2, 0.5, 0.3, 0.8, 0.5)
        result = opt.optimize_field(signals, m)
        assert 'stabilize_topology' in result['suggested_actions']

    def test_optimize_field_suggests_tension_relief(self):
        opt = ResonanceOptimizer(use_dspy=False)
        signals = [SignalPacket("s1", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.1)]
        m = CoherenceMetrics(0.5, 0.2, 0.5, 0.8, 0.2, 0.5)
        result = opt.optimize_field(signals, m)
        assert 'relieve_tension' in result['suggested_actions']

    def test_optimize_field_suggests_attractor_strengthening(self):
        opt = ResonanceOptimizer(use_dspy=False)
        signals = [SignalPacket("s1", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.1)]
        m = CoherenceMetrics(0.5, 0.2, 0.5, 0.3, 0.2, 0.2)
        result = opt.optimize_field(signals, m)
        assert 'strengthen_attractors' in result['suggested_actions']


# ─── SignalRouter Tests ──────────────────────────────────────────────────

class TestSignalRouter:
    def test_route_viable_signal(self):
        router = SignalRouter()
        router.register_route("s1", ["field-a", "field-b"])
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0)
        m = CoherenceMetrics(0.8, 0.1, 0.5, 0.2, 0.1, 0.9)
        targets = router.route_signal(s, m)
        assert "field-a" in targets

    def test_route_weak_signal(self):
        router = SignalRouter()
        s = SignalPacket("s1", "src", 0.05, 0.05, SignalPhase.COHERENCE, 0.0)
        m = CoherenceMetrics(0.1, 0.9, 0.1, 0.9, 0.9, 0.1)
        targets = router.route_signal(s, m)
        assert targets == []

    def test_route_collapsed_signal(self):
        router = SignalRouter()
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COLLAPSE, 0.0)
        m = CoherenceMetrics(0.8, 0.1, 0.5, 0.2, 0.1, 0.9)
        targets = router.route_signal(s, m)
        assert targets == []

    def test_route_deduplication(self):
        router = SignalRouter()
        router.register_route("s1", ["field-a", "field-b"])
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0,
                         resonance_targets=["field-a", "field-c"])
        m = CoherenceMetrics(0.8, 0.1, 0.5, 0.2, 0.1, 0.9)
        targets = router.route_signal(s, m)
        assert targets.count("field-a") == 1  # No duplicates


# ─── FieldStateManager Tests ─────────────────────────────────────────────

class TestFieldStateManager:
    def test_add_signal(self):
        fm = FieldStateManager("field-1")
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0)
        assert fm.add_signal(s) is True
        assert "s1" in fm.signals

    def test_capacity_limit(self):
        fm = FieldStateManager("field-1", capacity=2)
        fm.add_signal(SignalPacket("s1", "src", 0.5, 0.5, SignalPhase.COHERENCE, 0.0))
        fm.add_signal(SignalPacket("s2", "src", 0.5, 0.5, SignalPhase.COHERENCE, 0.0))
        result = fm.add_signal(SignalPacket("s3", "src", 0.5, 0.5, SignalPhase.COHERENCE, 0.0))
        assert result is False

    def test_remove_signal(self):
        fm = FieldStateManager("field-1")
        s = SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0)
        fm.add_signal(s)
        removed = fm.remove_signal("s1")
        assert removed is not None
        assert removed.signal_id == "s1"

    def test_remove_nonexistent(self):
        fm = FieldStateManager("field-1")
        assert fm.remove_signal("nonexistent") is None

    def test_compute_metrics_empty(self):
        fm = FieldStateManager("field-1")
        m = fm.compute_metrics()
        assert m.phase_alignment == 0.0
        assert m.resonance_density == 0.0

    def test_compute_metrics_with_signals(self):
        fm = FieldStateManager("field-1")
        for i in range(10):
            fm.add_signal(SignalPacket(
                f"s{i}", "src", 0.5 + i * 0.05, 0.6 + i * 0.03,
                SignalPhase.COHERENCE, 0.05
            ))
        m = fm.compute_metrics()
        assert m.resonance_density == pytest.approx(0.01)  # 10/1000
        assert 0.0 <= m.phase_alignment <= 1.0

    def test_compute_metrics_phase_alignment(self):
        fm = FieldStateManager("field-1")
        # All same phase → high alignment
        for i in range(10):
            fm.add_signal(SignalPacket(
                f"s{i}", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.05
            ))
        m = fm.compute_metrics()
        assert m.phase_alignment == pytest.approx(1.0)

    def test_get_local_view(self):
        fm = FieldStateManager("field-1")
        for i in range(20):
            fm.add_signal(SignalPacket(
                f"s{i}", "src", 0.1 + i * 0.04, 0.5, SignalPhase.COHERENCE, 0.0
            ))
        view = fm.get_local_view("observer-1", radius=5)
        assert len(view) == 5
        # Highest resonance first
        assert view[0].resonance_score >= view[1].resonance_score

    def test_prune_collapsed(self):
        fm = FieldStateManager("field-1")
        fm.add_signal(SignalPacket("s1", "src", 0.8, 0.9, SignalPhase.COHERENCE, 0.0))
        fm.add_signal(SignalPacket("s2", "src", 0.1, 0.01, SignalPhase.COLLAPSE, 0.0))
        fm.add_signal(SignalPacket("s3", "src", 0.5, 0.03, SignalPhase.DISSIPATION, 0.0))
        removed = fm.prune_collapsed()
        assert removed == 2
        assert len(fm.signals) == 1
        assert "s1" in fm.signals

    def test_metrics_history(self):
        fm = FieldStateManager("field-1")
        fm.add_signal(SignalPacket("s1", "src", 0.8, 0.8, SignalPhase.COHERENCE, 0.0))
        fm.compute_metrics()
        fm.compute_metrics()
        assert len(fm._metrics_history) == 2
