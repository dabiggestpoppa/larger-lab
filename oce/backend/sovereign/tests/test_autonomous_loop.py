"""Tests for Autonomous Operation Loop."""

import pytest
from oce.backend.sovereign.autonomous_loop import (
    AutonomousOperationLoop,
    LoopCycle,
    LoopPhase,
)


class TestLoopCycle:
    """Tests for LoopCycle dataclass."""

    def test_cycle_creation(self):
        """Test LoopCycle can be created."""
        cycle = LoopCycle(cycle_id=1, phase=LoopPhase.OBSERVE)
        assert cycle.cycle_id == 1
        assert cycle.phase == LoopPhase.OBSERVE

    def test_cycle_to_dict(self):
        """Test LoopCycle serialization."""
        cycle = LoopCycle(
            cycle_id=1,
            phase=LoopPhase.OBSERVE,
            actions_taken=["action1"],
            issues_found=["issue1"],
            improvements_made=["improvement1"],
        )
        d = cycle.to_dict()
        assert d["cycle_id"] == 1
        assert d["phase"] == "observe"
        assert d["actions"] == 1


class TestAutonomousOperationLoop:
    """Tests for AutonomousOperationLoop class."""

    def test_loop_creation(self):
        """Test AutonomousOperationLoop can be created."""
        loop = AutonomousOperationLoop()
        assert loop is not None

    def test_run_cycle_basic(self):
        """Test running a basic cycle."""
        loop = AutonomousOperationLoop()
        cycle = loop.run_cycle(field_health=0.9, entropy_pressure=0.2)
        assert cycle.cycle_id == 1
        assert cycle.phase == LoopPhase.OBSERVE

    def test_run_multiple_cycles(self):
        """Test running multiple cycles."""
        loop = AutonomousOperationLoop()
        loop.run_cycle(field_health=0.9)
        loop.run_cycle(field_health=0.8)
        assert loop._cycle_count == 2

    def test_cycle_with_low_health(self):
        """Test cycle with low field health."""
        loop = AutonomousOperationLoop()
        cycle = loop.run_cycle(field_health=0.3, entropy_pressure=0.8)
        assert "low_field_health" in cycle.issues_found

    def test_cycle_with_high_entropy(self):
        """Test cycle with high entropy pressure."""
        loop = AutonomousOperationLoop()
        cycle = loop.run_cycle(field_health=0.9, entropy_pressure=0.9)
        assert "high_entropy_pressure" in cycle.issues_found

    def test_cycle_with_drift(self):
        """Test cycle with drift alerts."""
        loop = AutonomousOperationLoop()
        cycle = loop.run_cycle(field_health=0.9, drift_alerts=["drift1", "drift2", "drift3", "drift4"])
        assert "excessive_drift" in cycle.issues_found

    def test_cycle_with_waste(self):
        """Test cycle with high compute waste."""
        loop = AutonomousOperationLoop()
        cycle = loop.run_cycle(field_health=0.9, waste_report={"total_waste": 1.0})
        assert "high_compute_waste" in cycle.issues_found

    def test_register_callback(self):
        """Test registering a callback."""
        loop = AutonomousOperationLoop()
        called = []

        def callback(cycle):
            called.append(cycle)

        loop.register_callback(LoopPhase.OBSERVE, callback)
        loop.run_cycle()
        assert len(called) == 1

    def test_stats_empty(self):
        """Test stats with no cycles."""
        loop = AutonomousOperationLoop()
        stats = loop.stats
        assert stats["total_cycles"] == 0

    def test_stats_with_cycles(self):
        """Test stats with cycles."""
        loop = AutonomousOperationLoop()
        loop.run_cycle()
        loop.run_cycle()
        stats = loop.stats
        assert stats["total_cycles"] == 2
        assert stats["avg_duration_ms"] >= 0

    def test_observe(self):
        """Test observe method."""
        loop = AutonomousOperationLoop()
        obs = loop._observe(0.9, 0.2, [])
        assert obs["field_health"] == 0.9
        assert obs["entropy_pressure"] == 0.2

    def test_analyze(self):
        """Test analyze method."""
        loop = AutonomousOperationLoop()
        issues = loop._analyze({"field_health": 0.3, "entropy_pressure": 0.5, "drift_count": 0}, {})
        assert "low_field_health" in issues

    def test_bsp_project(self):
        """Test BSP project method."""
        loop = AutonomousOperationLoop()
        projections = loop._bsp_project(["low_field_health"])
        assert "repair_field_coherence" in projections

    def test_prioritize(self):
        """Test prioritize method."""
        loop = AutonomousOperationLoop()
        priorities = loop._prioritize(["low_field_health"], ["repair_field_coherence"])
        assert "repair_field_coherence" in priorities

    def test_execute(self):
        """Test execute method."""
        loop = AutonomousOperationLoop()
        actions = loop._execute(["repair_field_coherence"])
        assert len(actions) == 1

    def test_reflect(self):
        """Test reflect method."""
        loop = AutonomousOperationLoop()
        improvements = loop._reflect(["executed:repair"], ["low_health"])
        assert len(improvements) > 0