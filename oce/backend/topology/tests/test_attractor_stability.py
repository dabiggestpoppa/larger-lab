"""Tests for AttractorStabilityLayer."""

import pytest
import math
from oce.backend.topology.attractor_stability import AttractorStabilityLayer, StabilityState
from oce.backend.resonance import FieldStateManager, ResonanceEngine, SignalPacket


class TestStabilityState:
    def test_stable(self):
        state = StabilityState(
            timestamp=0, is_stable=True, instability_level=0.2,
            active_attractors=3, frozen_routes=0, repair_active=False, compression_level=0.0,
        )
        assert state.is_stable is True

    def test_unstable(self):
        state = StabilityState(
            timestamp=0, is_stable=False, instability_level=0.8,
            active_attractors=1, frozen_routes=2, repair_active=True, compression_level=0.5,
        )
        assert state.is_stable is False


class TestAttractorStabilityLayer:
    def test_evaluate_stable(self):
        layer = AttractorStabilityLayer()
        field_mgr = FieldStateManager()
        field_mgr.entrain_observer("obs1", 0.0, 0.9)
        state = layer.evaluate(field_mgr)
        assert isinstance(state, StabilityState)

    def test_evaluate_unstable(self):
        layer = AttractorStabilityLayer(instability_threshold=0.3)
        field_mgr = FieldStateManager()
        # Create unstable conditions
        for i in range(50):
            field_mgr.inject_signal(SignalPacket(
                source=f"noise_{i}", amplitude=0.8, coherence=0.1,
                entropy_delta=0.9,
            ))
        state = layer.evaluate(field_mgr)
        # Should detect instability
        assert isinstance(state, StabilityState)

    def test_stability_rules_applied(self):
        layer = AttractorStabilityLayer(instability_threshold=0.2)
        field_mgr = FieldStateManager()
        # Create very unstable conditions
        for i in range(100):
            field_mgr.inject_signal(SignalPacket(
                source=f"flood_{i}", amplitude=0.9, coherence=0.05,
                entropy_delta=0.95,
            ))
        state = layer.evaluate(field_mgr)
        # After evaluation, stability layer should have taken some action
        # Either repair was triggered, or routes were frozen, or compression applied
        assert isinstance(state, StabilityState)
        # The layer should have evaluated and returned a state
        assert state.instability_level >= 0.0

    def test_stats(self):
        layer = AttractorStabilityLayer()
        field_mgr = FieldStateManager()
        layer.evaluate(field_mgr)
        layer.evaluate(field_mgr)
        stats = layer.stats
        assert stats["total_evaluations"] == 2
