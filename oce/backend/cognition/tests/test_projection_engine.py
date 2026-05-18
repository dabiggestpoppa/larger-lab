"""Tests for Projection Engine."""

import pytest
from oce.backend.cognition.projection_engine import ProjectionEngine, FieldVector
from oce.backend.resonance import SignalPacket


class TestFieldVector:
    def test_creation(self):
        v = FieldVector(vector_id="v1", source_event="test")
        assert v.vector_id == "v1"
        assert v.amplitude == 0.5

    def test_intensity(self):
        v = FieldVector(vector_id="v1", source_event="test", amplitude=0.8, coherence=0.9)
        assert v.intensity == pytest.approx(0.72, abs=0.01)

    def test_interference(self):
        v1 = FieldVector(vector_id="v1", source_event="a", amplitude=0.8, phase=0.0)
        v2 = FieldVector(vector_id="v2", source_event="b", amplitude=0.8, phase=0.0)
        # Same phase = constructive interference
        assert v1.interfere(v2) > 0


class TestProjectionEngine:
    def test_project_event(self):
        engine = ProjectionEngine()
        vec = engine.project_event("test", "source", amplitude=0.8)
        assert vec.amplitude == 0.8

    def test_project_signal(self):
        engine = ProjectionEngine()
        signal = SignalPacket(source="test", amplitude=0.7, coherence=0.9, phase=1.0)
        vec = engine.project_signal(signal)
        assert vec.amplitude == 0.7
        assert vec.coherence == 0.9

    def test_field_state(self):
        engine = ProjectionEngine()
        engine.project_event("test", "source")
        state = engine.get_field_state()
        assert state["total_vectors"] == 1

    def test_decay(self):
        engine = ProjectionEngine()
        engine.project_event("test", "source", amplitude=0.5)
        engine.decay(factor=0.5)
        assert engine._vectors[0].amplitude == pytest.approx(0.25, abs=0.01)

    def test_stats(self):
        engine = ProjectionEngine()
        engine.project_event("test", "source")
        stats = engine.stats
        assert stats["total_vectors"] == 1
