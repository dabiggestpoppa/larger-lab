"""
Tests for FieldStateManager and FieldState.
"""

import pytest
from oce.backend.resonance.field_state import FieldStateManager, FieldState
from oce.backend.resonance.signal_packet import SignalPacket


class TestFieldState:
    def test_basic_creation(self):
        s = FieldState()
        assert s.resonance_level == 0.5
        assert s.stability_index == 0.5
        assert s.entropy_budget == 1.0

    def test_is_stable(self):
        s = FieldState(resonance_level=0.8, stability_index=0.8, entropy_budget=0.5)
        assert s.is_stable is True

    def test_not_stable_low_entropy(self):
        s = FieldState(resonance_level=0.8, stability_index=0.8, entropy_budget=0.05)
        assert s.is_stable is False

    def test_is_saturated(self):
        s = FieldState(entropy_budget=0.05)
        assert s.is_saturated is True

    def test_health(self):
        s = FieldState(resonance_level=0.8, stability_index=0.8, entropy_budget=0.8)
        assert s.health == pytest.approx(0.512, abs=0.01)

    def test_to_dict(self):
        s = FieldState()
        d = s.to_dict()
        assert "health" in d
        assert "is_stable" in d


class TestFieldStateManager:
    def test_inject_signal(self):
        mgr = FieldStateManager()
        mgr.inject_signal(SignalPacket(source="s1", amplitude=0.8, coherence=0.9))
        assert len(mgr.signal_field) == 1

    def test_inject_entropic_consumes_budget(self):
        mgr = FieldStateManager()
        initial_budget = mgr.current_state.entropy_budget
        mgr.inject_signal(SignalPacket(source="s1", entropy_delta=0.5))
        assert mgr.current_state.entropy_budget < initial_budget

    def test_entrain_observer(self):
        mgr = FieldStateManager()
        mgr.entrain_observer("obs1", phase=0.0, coherence=0.8)
        assert mgr.current_state.observer_count == 1

    def test_remove_observer(self):
        mgr = FieldStateManager()
        mgr.entrain_observer("obs1", phase=0.0, coherence=0.8)
        mgr.remove_observer("obs1")
        assert mgr.current_state.observer_count == 0

    def test_measure_coherence(self):
        mgr = FieldStateManager()
        mgr.inject_signal(SignalPacket(source="s1", coherence=0.8))
        snap = mgr.measure_coherence()
        assert snap is not None
        assert 0.0 <= snap.overall_coherence <= 1.0

    def test_decay_step(self):
        mgr = FieldStateManager()
        mgr.inject_signal(SignalPacket(source="s1", amplitude=0.5))
        mgr.decay_step()
        assert mgr.signal_field.signals[0].amplitude < 0.5

    def test_repair(self):
        mgr = FieldStateManager()
        mgr.current_state.stability_index = 0.2
        mgr.current_state.entropy_budget = 0.1
        mgr.repair(amount=0.3)
        assert mgr.current_state.stability_index > 0.2
        assert mgr.current_state.entropy_budget > 0.1

    def test_pressure_map(self):
        mgr = FieldStateManager()
        mgr.inject_signal(SignalPacket(source="s1", amplitude=0.8, coherence=0.2, entropy_delta=0.5, boundary_tags=["b1"]))
        pressure = mgr.get_pressure_map()
        assert "b1" in pressure

    def test_stats(self):
        mgr = FieldStateManager()
        mgr.inject_signal(SignalPacket(source="s1"))
        stats = mgr.stats
        assert "state" in stats
        assert "signals" in stats
        assert "coherence" in stats

    def test_entropy_flood_recovery(self):
        """Flood with entropic signals, then repair — field should recover."""
        mgr = FieldStateManager()
        for i in range(50):
            mgr.inject_signal(SignalPacket(source=f"s{i}", entropy_delta=0.5, coherence=0.2))
        assert mgr.current_state.entropy_budget < 0.5
        mgr.repair(amount=0.5)
        assert mgr.current_state.stability_index > 0.3
