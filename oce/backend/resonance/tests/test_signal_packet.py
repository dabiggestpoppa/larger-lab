"""
Tests for SignalPacket and SignalField.
Tests stability under perturbation, not just correct outputs.
"""

import pytest
import time
import math
from oce.backend.resonance.signal_packet import SignalPacket, SignalField


class TestSignalPacket:
    """Tests for the core SignalPacket ontology."""

    def test_basic_creation(self):
        s = SignalPacket(source="test", amplitude=0.8, coherence=0.9)
        assert s.source == "test"
        assert s.amplitude == 0.8
        assert s.coherence == 0.9
        assert s.signal_id is not None

    def test_amplitude_clamping(self):
        s = SignalPacket(source="test", amplitude=1.5)
        assert s.amplitude == 1.0
        s2 = SignalPacket(source="test", amplitude=-0.5)
        assert s2.amplitude == 0.0

    def test_coherence_clamping(self):
        s = SignalPacket(source="test", coherence=2.0)
        assert s.coherence == 1.0

    def test_phase_wrapping(self):
        s = SignalPacket(source="test", phase=3 * math.pi)
        assert s.phase == pytest.approx(math.pi, abs=0.01)

    def test_entropy_delta_non_negative(self):
        s = SignalPacket(source="test", entropy_delta=-0.5)
        assert s.entropy_delta == 0.0

    def test_is_resonant(self):
        s = SignalPacket(source="test", amplitude=0.8, coherence=0.9)
        assert s.is_resonant is True

    def test_not_resonant_low_coherence(self):
        s = SignalPacket(source="test", amplitude=0.8, coherence=0.3)
        assert s.is_resonant is False

    def test_not_resonant_low_amplitude(self):
        s = SignalPacket(source="test", amplitude=0.2, coherence=0.9)
        assert s.is_resonant is False

    def test_is_entropic(self):
        s = SignalPacket(source="test", entropy_delta=0.8)
        assert s.is_entropic is True

    def test_not_entropic(self):
        s = SignalPacket(source="test", entropy_delta=0.1)
        assert s.is_entropic is False

    def test_signal_pressure(self):
        s = SignalPacket(source="test", amplitude=0.8, coherence=0.2, entropy_delta=0.5)
        expected = 0.8 * 0.8 * 0.5  # amp * (1-coh) * entropy
        assert s.signal_pressure == pytest.approx(expected, abs=0.01)

    def test_resonance_score(self):
        s = SignalPacket(source="test", amplitude=0.8, coherence=0.9, phase=0.0)
        score = s.resonance_score(observer_coherence=0.9, observer_phase=0.1)
        assert 0.0 <= score <= 1.0

    def test_resonance_score_perfect_alignment(self):
        s = SignalPacket(source="test", amplitude=1.0, coherence=1.0, phase=0.0)
        score = s.resonance_score(observer_coherence=1.0, observer_phase=0.0)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_resonance_score_misaligned(self):
        s = SignalPacket(source="test", amplitude=0.1, coherence=0.1, phase=math.pi)
        score = s.resonance_score(observer_coherence=0.9, observer_phase=0.0)
        assert score < 0.3

    def test_serialization_roundtrip(self):
        s = SignalPacket(
            source="test", amplitude=0.7, coherence=0.8,
            phase=1.5, entropy_delta=0.3,
            boundary_tags=["b1", "b2"], resonance_targets=["obs1"],
        )
        d = s.to_dict()
        s2 = SignalPacket.from_dict(d)
        assert s2.source == s.source
        assert s2.amplitude == s.amplitude
        assert s2.coherence == s.coherence
        assert s2.phase == s.phase
        assert s2.entropy_delta == s.entropy_delta
        assert s2.boundary_tags == s.boundary_tags
        assert s2.resonance_targets == s.resonance_targets

    def test_factory_resonant(self):
        s = SignalPacket.create_resonant("src", "tgt", amplitude=0.9)
        assert s.is_resonant
        assert "tgt" in s.resonance_targets

    def test_factory_entropic(self):
        s = SignalPacket.create_entropic("src", entropy=0.9)
        assert s.is_entropic

    def test_factory_boundary(self):
        s = SignalPacket.create_boundary("src", "boundary_1")
        assert "boundary_1" in s.boundary_tags


class TestSignalField:
    """Tests for the SignalField container."""

    def test_inject(self):
        f = SignalField()
        s = SignalPacket(source="test")
        f.inject(s)
        assert len(f) == 1

    def test_max_size_eviction(self):
        f = SignalField(max_size=5)
        for i in range(10):
            f.inject(SignalPacket(source=f"test_{i}"))
        assert len(f) == 5

    def test_get_resonant_signals(self):
        f = SignalField()
        f.inject(SignalPacket(source="r1", amplitude=0.8, coherence=0.9))
        f.inject(SignalPacket(source="r2", amplitude=0.2, coherence=0.3))
        resonant = f.get_resonant_signals()
        assert len(resonant) == 1
        assert resonant[0].source == "r1"

    def test_get_entropic_signals(self):
        f = SignalField()
        f.inject(SignalPacket(source="e1", entropy_delta=0.8))
        f.inject(SignalPacket(source="e2", entropy_delta=0.1))
        entropic = f.get_entropic_signals()
        assert len(entropic) == 1

    def test_get_signals_by_source(self):
        f = SignalField()
        f.inject(SignalPacket(source="obs1"))
        f.inject(SignalPacket(source="obs1"))
        f.inject(SignalPacket(source="obs2"))
        assert len(f.get_signals_by_source("obs1")) == 2

    def test_get_signals_by_boundary(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", boundary_tags=["b1", "b2"]))
        f.inject(SignalPacket(source="s2", boundary_tags=["b2"]))
        assert len(f.get_signals_by_boundary("b1")) == 1
        assert len(f.get_signals_by_boundary("b2")) == 2

    def test_pressure_map(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", amplitude=0.8, coherence=0.2, entropy_delta=0.5, boundary_tags=["b1"]))
        pressure = f.get_pressure_map()
        assert "b1" in pressure
        assert pressure["b1"] > 0

    def test_decay(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", amplitude=0.5))
        f.decay(factor=0.5)
        assert f.signals[0].amplitude == pytest.approx(0.25, abs=0.01)

    def test_decay_removes_weak(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", amplitude=0.005))
        f.decay(factor=0.5)
        assert len(f) == 0

    def test_field_coherence(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", coherence=0.8))
        f.inject(SignalPacket(source="s2", coherence=0.6))
        assert f.field_coherence == pytest.approx(0.7, abs=0.01)

    def test_field_coherence_empty(self):
        f = SignalField()
        assert f.field_coherence == 1.0

    def test_field_entropy(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", entropy_delta=0.3))
        f.inject(SignalPacket(source="s2", entropy_delta=0.5))
        assert f.field_entropy == pytest.approx(0.8, abs=0.01)

    def test_clear(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1"))
        f.clear()
        assert len(f) == 0

    def test_stats(self):
        f = SignalField()
        f.inject(SignalPacket(source="s1", amplitude=0.8, coherence=0.9))
        stats = f.stats
        assert stats["total_signals"] == 1
        assert stats["injections"] == 1
        assert "field_coherence" in stats

    # Stability under perturbation tests

    def test_entropy_flood_stability(self):
        """Inject 1000 noisy signals — field should handle without crashing."""
        f = SignalField(max_size=500)
        for i in range(1000):
            f.inject(SignalPacket(
                source=f"noise_{i}",
                amplitude=0.1 + (i % 10) * 0.05,
                coherence=0.1,
                entropy_delta=0.8,
            ))
        assert len(f) <= 500
        stats = f.stats
        assert stats["injections"] == 1000

    def test_signal_scarcity(self):
        """With very few signals, field should still report valid coherence."""
        f = SignalField()
        f.inject(SignalPacket(source="only", coherence=0.5))
        assert f.field_coherence == 0.5
