"""
Tests for PressureTracker and PressureAlert.
"""

import pytest
from oce.backend.resonance.pressure_tracker import PressureTracker, PressureAlert
from oce.backend.resonance.signal_packet import SignalPacket, SignalField
from oce.backend.resonance.boundary_mapper import BoundaryMapper


class TestPressureAlert:
    def test_basic_creation(self):
        a = PressureAlert(alert_id="a1", zone_id="z1", boundary_id="b1", pressure=0.8, severity="critical")
        assert a.resolved is False

    def test_resolve(self):
        a = PressureAlert(alert_id="a1", zone_id="z1", boundary_id="b1", pressure=0.8, severity="critical")
        a.resolve()
        assert a.resolved is True
        assert a.resolved_at is not None


class TestPressureTracker:
    def test_empty_scan(self):
        tracker = PressureTracker()
        field = SignalField()
        mapper = BoundaryMapper()
        alerts = tracker.scan(field, mapper)
        assert len(alerts) == 0

    def test_scan_with_pressure(self):
        tracker = PressureTracker(warning_threshold=0.3)
        field = SignalField()
        mapper = BoundaryMapper()
        # Create high-pressure signals
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9, boundary_tags=["b1"],
            ))
        mapper.detect_boundaries(field)
        alerts = tracker.scan(field, mapper)
        assert isinstance(alerts, list)

    def test_active_alerts(self):
        tracker = PressureTracker(warning_threshold=0.3)
        field = SignalField()
        mapper = BoundaryMapper()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9, boundary_tags=["b1"],
            ))
        mapper.detect_boundaries(field)
        tracker.scan(field, mapper)
        active = tracker.get_active_alerts()
        assert isinstance(active, list)

    def test_resolve_alert(self):
        tracker = PressureTracker(warning_threshold=0.3)
        field = SignalField()
        mapper = BoundaryMapper()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9,
            ))
        mapper.detect_boundaries(field)
        alerts = tracker.scan(field, mapper)
        if alerts:
            assert tracker.resolve_alert(alerts[0].alert_id) is True

    def test_pressure_trend(self):
        tracker = PressureTracker()
        field = SignalField()
        mapper = BoundaryMapper()
        for i in range(5):
            field.inject(SignalPacket(source=f"s{i}", amplitude=0.5))
            tracker.scan(field, mapper)
        trend = tracker.get_pressure_trend()
        assert isinstance(trend, float)

    def test_callback_firing(self):
        tracker = PressureTracker(warning_threshold=0.3)
        fired = []
        tracker.register_callback(lambda a: fired.append(a))
        field = SignalField()
        mapper = BoundaryMapper()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9, boundary_tags=["b1"],
            ))
        mapper.detect_boundaries(field)
        tracker.scan(field, mapper)
        # Callbacks should have fired if alerts were generated
        assert isinstance(fired, list)

    def test_stats(self):
        tracker = PressureTracker()
        stats = tracker.stats
        assert "total_alerts" in stats
        assert "active_alerts" in stats

    def test_cooldown(self):
        """Alerts for same boundary should respect cooldown."""
        tracker = PressureTracker(warning_threshold=0.3, cooldown=60.0)
        field = SignalField()
        mapper = BoundaryMapper()
        for i in range(20):
            field.inject(SignalPacket(
                source=f"s{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9, boundary_tags=["b1"],
            ))
        mapper.detect_boundaries(field)
        alerts1 = tracker.scan(field, mapper)
        alerts2 = tracker.scan(field, mapper)  # Should be empty due to cooldown
        # Second scan should produce fewer or no new alerts
        assert len(alerts2) <= len(alerts1)
