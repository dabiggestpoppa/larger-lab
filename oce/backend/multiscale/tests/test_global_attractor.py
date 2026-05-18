"""Tests for Global Attractor Layer."""

import pytest
from oce.backend.multiscale.global_attractor import GlobalAttractorLayer, GlobalAttractor, AttractorState


class TestGlobalAttractor:
    def test_creation(self):
        a = GlobalAttractor(attractor_id="a1")
        assert a.attractor_id == "a1"
        assert a.state == AttractorState.STABLE

    def test_set_direction(self):
        a = GlobalAttractor(attractor_id="a1")
        a.set_direction({"goal": "build_v3"})
        assert a.strategic_direction == {"goal": "build_v3"}

    def test_get_direction(self):
        a = GlobalAttractor(attractor_id="a1")
        a.set_direction({"goal": "test"})
        assert a.get_direction() == {"goal": "test"}

    def test_record_local_operation(self):
        a = GlobalAttractor(attractor_id="a1", update_frequency=5)
        for _ in range(5):
            a.record_local_operation()
        assert a.should_update() is True

    def test_calculate_influence(self):
        a = GlobalAttractor(attractor_id="a1")
        assert a.calculate_influence("local") == 0.1
        assert a.calculate_influence("global") == 1.0


class TestGlobalAttractorLayer:
    def test_update_direction(self):
        layer = GlobalAttractorLayer()
        layer.update_direction({"goal": "build_v3"})
        assert layer.get_current_direction() == {"goal": "build_v3"}

    def test_get_direction_history(self):
        layer = GlobalAttractorLayer()
        layer.update_direction({"goal": "test1"})
        layer.update_direction({"goal": "test2"})
        history = layer.get_direction_history()
        assert len(history) == 2

    def test_process_local_operation(self):
        layer = GlobalAttractorLayer()
        # Process operations up to update frequency
        for _ in range(100):
            result = layer.process_local_operation()
        # After 100 operations, should return direction
        assert result is not None
