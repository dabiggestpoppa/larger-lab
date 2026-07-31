"""
Tests for ResonanceEngine, ResonanceScore, and Constraint.
"""

import pytest
import math
from oce.backend.resonance.resonance_engine import ResonanceEngine, ResonanceScore, Constraint
from oce.backend.resonance.signal_packet import SignalPacket, SignalField


class TestResonanceScore:
    def test_basic_creation(self):
        s = ResonanceScore(observer_id="obs1", signal_id="sig1", score=0.8,
                          coherence_alignment=0.9, phase_proximity=0.8,
                          amplitude_factor=0.7, entropy_cost=0.1)
        assert s.score == 0.8
        assert s.is_viable is True

    def test_not_viable_low_score(self):
        s = ResonanceScore(observer_id="obs1", signal_id="sig1", score=0.1,
                          coherence_alignment=0.1, phase_proximity=0.1,
                          amplitude_factor=0.1, entropy_cost=0.1)
        assert s.is_viable is False

    def test_not_viable_high_entropy(self):
        s = ResonanceScore(observer_id="obs1", signal_id="sig1", score=0.8,
                          coherence_alignment=0.9, phase_proximity=0.8,
                          amplitude_factor=0.7, entropy_cost=0.8)
        assert s.is_viable is False


class TestConstraint:
    def test_resonance_with(self):
        c1 = Constraint(constraint_id="c1", constraint_type="goal", weight=0.8, phase=0.0, coherence=0.9)
        c2 = Constraint(constraint_id="c2", constraint_type="system", weight=0.7, phase=0.1, coherence=0.8)
        r = c1.resonance_with(c2)
        assert 0.0 <= r <= 1.0

    def test_resonance_perfect_alignment(self):
        c1 = Constraint(constraint_id="c1", constraint_type="goal", weight=1.0, phase=0.0, coherence=1.0)
        c2 = Constraint(constraint_id="c2", constraint_type="system", weight=1.0, phase=0.0, coherence=1.0)
        assert c1.resonance_with(c2) == pytest.approx(1.0, abs=0.01)

    def test_resonance_opposite(self):
        c1 = Constraint(constraint_id="c1", constraint_type="goal", weight=1.0, phase=0.0, coherence=1.0)
        c2 = Constraint(constraint_id="c2", constraint_type="system", weight=1.0, phase=math.pi, coherence=0.0)
        r = c1.resonance_with(c2)
        assert r < 0.3


class TestResonanceEngine:
    def test_score_resonance(self):
        engine = ResonanceEngine()
        signal = SignalPacket(source="s1", amplitude=0.8, coherence=0.9, phase=0.0)
        score = engine.score_resonance("obs1", observer_phase=0.1, observer_coherence=0.9, signal=signal)
        assert score.is_viable
        assert score.score > 0.5

    def test_score_resonance_misaligned(self):
        engine = ResonanceEngine()
        signal = SignalPacket(source="s1", amplitude=0.2, coherence=0.2, phase=math.pi)
        score = engine.score_resonance("obs1", observer_phase=0.0, observer_coherence=0.9, signal=signal)
        assert score.is_viable is False

    def test_find_best_observer(self):
        engine = ResonanceEngine()
        signal = SignalPacket(source="s1", amplitude=0.8, coherence=0.9, phase=0.0)
        observers = {
            "obs1": (0.1, 0.9),   # Close match
            "obs2": (math.pi, 0.2),  # Far match
        }
        best = engine.find_best_observer(signal, observers)
        assert best == "obs1"

    def test_find_best_observer_none_viable(self):
        engine = ResonanceEngine()
        signal = SignalPacket(source="s1", amplitude=0.1, coherence=0.1)
        observers = {"obs1": (math.pi, 0.1)}
        best = engine.find_best_observer(signal, observers)
        assert best is None

    def test_add_constraint(self):
        engine = ResonanceEngine()
        engine.add_constraint(Constraint(constraint_id="c1", constraint_type="goal"))
        assert len(engine._constraints) == 1

    def test_harmonize_constraints(self):
        engine = ResonanceEngine()
        engine.add_constraint(Constraint(constraint_id="c1", constraint_type="goal", phase=0.0, coherence=0.9, weight=0.8))
        engine.add_constraint(Constraint(constraint_id="c2", constraint_type="system", phase=0.1, coherence=0.8, weight=0.7))
        h = engine.harmonize_constraints()
        assert 0.0 <= h <= 1.0

    def test_harmonize_single_constraint(self):
        engine = ResonanceEngine()
        engine.add_constraint(Constraint(constraint_id="c1", constraint_type="goal"))
        assert engine.harmonize_constraints() == 1.0

    def test_get_action_path(self):
        engine = ResonanceEngine()
        engine.add_constraint(Constraint(constraint_id="c1", constraint_type="goal", phase=0.0, coherence=0.9, weight=0.8))
        engine.add_constraint(Constraint(constraint_id="c2", constraint_type="system", phase=0.1, coherence=0.8, weight=0.7))
        path = engine.get_action_path()
        assert isinstance(path, list)

    def test_inject_and_score(self):
        engine = ResonanceEngine()
        signal = SignalPacket(source="s1", amplitude=0.8, coherence=0.9, phase=0.0)
        result = engine.inject_and_score(signal)
        assert "signal" in result
        assert "coherence" in result
        assert "field_state" in result

    def test_decay_step(self):
        engine = ResonanceEngine()
        engine.inject_and_score(SignalPacket(source="s1", amplitude=0.8))
        engine.decay_step()
        assert len(engine.field_manager.signal_field) >= 0

    def test_repair(self):
        engine = ResonanceEngine()
        engine.field_manager.current_state.stability_index = 0.2
        engine.repair()
        assert engine.field_manager.current_state.stability_index > 0.2

    def test_stats(self):
        engine = ResonanceEngine()
        stats = engine.stats
        assert "field" in stats
        assert "boundaries" in stats
        assert "constraints" in stats

    # Stability tests

    def test_entropy_flood_stability(self):
        """Flood with 100 entropic signals — engine should handle gracefully."""
        engine = ResonanceEngine()
        for i in range(100):
            signal = SignalPacket(
                source=f"s{i}", amplitude=0.5,
                coherence=0.2, entropy_delta=0.8,
            )
            engine.inject_and_score(signal)
        stats = engine.stats
        assert stats["field"]["signals"]["total_signals"] > 0

    def test_observer_death_recovery(self):
        """Remove all observers — engine should still function."""
        engine = ResonanceEngine()
        engine.field_manager.entrain_observer("obs1", 0.0, 0.8)
        engine.field_manager.entrain_observer("obs2", 1.0, 0.7)
        engine.field_manager.remove_observer("obs1")
        engine.field_manager.remove_observer("obs2")
        signal = SignalPacket(source="s1", amplitude=0.8, coherence=0.9)
        result = engine.inject_and_score(signal)
        assert result["coherence"] is not None
