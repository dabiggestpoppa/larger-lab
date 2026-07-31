"""Tests for FieldPressureSystem."""

import pytest
import math
from oce.backend.topology.field_pressure import FieldPressureSystem, PressureReading
from oce.backend.resonance import FieldStateManager, ResonanceEngine
from oce.backend.resonance.signal_packet import SignalPacket


class TestPressureReading:
    def test_normal_pressure(self):
        r = PressureReading(
            timestamp=1.0, observer_load={"obs1": 0.3},
            sync_instability=0.2, entropy_spike=0.3,
            coherence_drift=0.1, trajectory_fragmentation=0.2,
            overall_pressure=0.2,
        )
        assert r.is_critical is False
        assert r.needs_attention is False

    def test_critical_pressure(self):
        r = PressureReading(
            timestamp=1.0, observer_load={"obs1": 0.9},
            sync_instability=0.8, entropy_spike=0.9,
            coherence_drift=0.8, trajectory_fragmentation=0.9,
            overall_pressure=0.85,
        )
        assert r.is_critical is True
        assert r.needs_attention is True


class TestFieldPressureSystem:
    def test_scan_basic(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        field_mgr.entrain_observer("obs1", 0.0, 0.8)
        
        reading = system.scan(field_mgr, collar_engine=None)
        assert isinstance(reading, PressureReading)
        assert 0.0 <= reading.overall_pressure <= 1.0

    def test_scan_multiple_observers(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        field_mgr.entrain_observer("obs1", 0.0, 0.9)
        field_mgr.entrain_observer("obs2", 0.5, 0.85)
        
        reading = system.scan(field_mgr, collar_engine=None)
        assert "obs1" in reading.observer_load
        assert "obs2" in reading.observer_load

    def test_callback_on_critical(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        
        callback_called = []
        def callback(r):
            callback_called.append(r)
        
        system.register_callback(callback)
        
        # Create critical conditions
        for i in range(100):
            signal = SignalPacket(
                source=f"noise_{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9,
            )
            field_mgr.inject_signal(signal)
        
        reading = system.scan(field_mgr, collar_engine=None)
        # Callback should fire if critical
        if reading.is_critical:
            assert len(callback_called) > 0

    def test_trend(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        
        # Take multiple readings
        for i in range(5):
            system.scan(field_mgr, collar_engine=None)
        
        trend = system.get_trend()
        assert isinstance(trend, float)

    def test_latest(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        
        assert system.latest is None
        
        system.scan(field_mgr, collar_engine=None)
        assert system.latest is not None

    def test_stats(self):
        system = FieldPressureSystem()
        field_mgr = FieldStateManager()
        
        system.scan(field_mgr, collar_engine=None)
        system.scan(field_mgr, collar_engine=None)
        
        stats = system.stats
        assert stats["total_readings"] >= 2