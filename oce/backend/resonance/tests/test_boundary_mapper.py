"""
Tests for BoundaryMapper, Boundary, and PressureZone.
"""

import pytest
import math
from oce.backend.resonance.boundary_mapper import BoundaryMapper, Boundary, PressureZone
from oce.backend.resonance.signal_packet import SignalPacket, SignalField


class TestBoundary:
    def test_basic_creation(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence")
        assert b.boundary_id == "b1"
        assert b.pressure == 0.0

    def test_is_critical(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence", pressure=0.8)
        assert b.is_critical is True

    def test_is_weakening(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence", strength=0.1)
        assert b.is_weakening is True

    def test_add_pressure(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence")
        b.add_pressure(0.5)
        assert b.pressure == pytest.approx(0.5, abs=0.01)
        b.add_pressure(0.3)
        assert b.pressure == pytest.approx(0.8, abs=0.01)

    def test_pressure_clamped(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence")
        b.add_pressure(2.0)
        assert b.pressure == 1.0

    def test_decay(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence", pressure=0.8, strength=0.8)
        b.decay(factor=0.5)
        assert b.pressure == pytest.approx(0.4, abs=0.01)
        assert b.strength == pytest.approx(0.4, abs=0.01)

    def test_to_dict(self):
        b = Boundary(boundary_id="b1", boundary_type="coherence", pressure=0.5)
        d = b.to_dict()
        assert d["boundary_id"] == "b1"
        assert d["is_critical"] is False


class TestPressureZone:
    def test_basic_creation(self):
        z = PressureZone(zone_id="z1")
        assert z.zone_id == "z1"
        assert z.intensity == 0.0

    def test_is_critical(self):
        z = PressureZone(zone_id="z1", intensity=0.9)
        assert z.is_critical is True

    def test_is_resolved(self):
        z = PressureZone(zone_id="z1", intensity=0.05)
        assert z.is_resolved is True


class TestBoundaryMapper:
    def test_empty_field(self):
        mapper = BoundaryMapper()
        field = SignalField()
        boundaries = mapper.detect_boundaries(field)
        assert len(boundaries) == 0

    def test_detect_coherence_boundary(self):
        mapper = BoundaryMapper()
        field = SignalField()
        field.inject(SignalPacket(source="s1", coherence=0.9, phase=0.0))
        field.inject(SignalPacket(source="s2", coherence=0.2, phase=0.1))
        boundaries = mapper.detect_boundaries(field)
        assert len(boundaries) >= 1

    def test_detect_phase_boundary(self):
        mapper = BoundaryMapper()
        field = SignalField()
        field.inject(SignalPacket(source="s1", coherence=0.5, phase=0.0))
        field.inject(SignalPacket(source="s2", coherence=0.5, phase=math.pi))
        boundaries = mapper.detect_boundaries(field)
        assert len(boundaries) >= 1

    def test_no_boundary_similar_signals(self):
        mapper = BoundaryMapper()
        field = SignalField()
        field.inject(SignalPacket(source="s1", coherence=0.8, phase=0.5))
        field.inject(SignalPacket(source="s2", coherence=0.8, phase=0.6))
        boundaries = mapper.detect_boundaries(field)
        assert len(boundaries) == 0

    def test_map_pressure_zones(self):
        mapper = BoundaryMapper()
        field = SignalField()
        for i in range(10):
            field.inject(SignalPacket(
                source=f"s{i}", coherence=0.1, phase=0.1 * i,
                entropy_delta=0.8, amplitude=0.8,
            ))
        mapper.detect_boundaries(field)
        zones = mapper.map_pressure_zones()
        assert isinstance(zones, list)

    def test_get_critical_boundaries(self):
        mapper = BoundaryMapper()
        field = SignalField()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", coherence=0.1,
                entropy_delta=0.9, amplitude=0.9,
            ))
        mapper.detect_boundaries(field)
        critical = mapper.get_critical_boundaries()
        assert isinstance(critical, list)

    def test_decay(self):
        mapper = BoundaryMapper()
        b = Boundary(boundary_id="b1", boundary_type="coherence", pressure=0.8, strength=0.8)
        mapper.boundaries["b1"] = b
        mapper.decay(factor=0.5)
        assert mapper.boundaries["b1"].pressure < 0.8

    def test_decay_removes_weak(self):
        mapper = BoundaryMapper()
        b = Boundary(boundary_id="b1", boundary_type="coherence", pressure=0.001, strength=0.001)
        mapper.boundaries["b1"] = b
        mapper.decay(factor=0.5)
        assert "b1" not in mapper.boundaries

    def test_get_repair_targets(self):
        mapper = BoundaryMapper()
        field = SignalField()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", coherence=0.1,
                entropy_delta=0.9, amplitude=0.9,
            ))
        mapper.detect_boundaries(field)
        targets = mapper.get_repair_targets()
        assert isinstance(targets, list)

    def test_stats(self):
        mapper = BoundaryMapper()
        stats = mapper.stats
        assert "total_boundaries" in stats
        assert "critical_boundaries" in stats
