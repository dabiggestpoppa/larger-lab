"""Tests for TopologyMetrics."""

import pytest
from oce.backend.topology.topology_metrics import TopologyMetrics, TopologyHealth
from oce.backend.topology.collar_field import CollarFieldEngine
from oce.backend.topology.field_pressure import FieldPressureSystem


class TestTopologyHealth:
    def test_healthy(self):
        health = TopologyHealth(
            timestamp=0, coupling_efficiency=0.8, resonance_stability=0.8,
            observer_drift=0.1, topology_coherence=0.8, overlap_bandwidth_efficiency=0.7,
            overall_health=0.8,
        )
        assert health.is_healthy is True
        assert health.needs_attention is False

    def test_needs_attention(self):
        health = TopologyHealth(
            timestamp=0, coupling_efficiency=0.2, resonance_stability=0.2,
            observer_drift=0.8, topology_coherence=0.2, overlap_bandwidth_efficiency=0.1,
            overall_health=0.2,
        )
        assert health.needs_attention is True


class TestTopologyMetrics:
    def test_measure(self):
        metrics = TopologyMetrics()
        collar_engine = CollarFieldEngine()
        pressure_system = FieldPressureSystem()
        collar_engine.connect("obs1", "obs2", initial_resonance=0.8)
        health = metrics.measure(collar_engine, pressure_system, observer_count=2)
        assert isinstance(health, TopologyHealth)
        assert 0.0 <= health.overall_health <= 1.0

    def test_measure_healthy_field(self):
        metrics = TopologyMetrics()
        collar_engine = CollarFieldEngine()
        pressure_system = FieldPressureSystem()
        # Create strong connections
        collar_engine.connect("obs1", "obs2", initial_resonance=0.9)
        collar_engine.connect("obs2", "obs3", initial_resonance=0.85)
        collar_engine.connect("obs1", "obs3", initial_resonance=0.8)
        health = metrics.measure(collar_engine, pressure_system, observer_count=3)
        assert health.is_healthy

    def test_trend(self):
        metrics = TopologyMetrics()
        collar_engine = CollarFieldEngine()
        pressure_system = FieldPressureSystem()
        for _ in range(5):
            metrics.measure(collar_engine, pressure_system, observer_count=2)
        trend = metrics.get_trend()
        assert isinstance(trend, float)

    def test_stats(self):
        metrics = TopologyMetrics()
        collar_engine = CollarFieldEngine()
        pressure_system = FieldPressureSystem()
        metrics.measure(collar_engine, pressure_system, observer_count=2)
        stats = metrics.stats
        assert stats["total_measurements"] == 1
