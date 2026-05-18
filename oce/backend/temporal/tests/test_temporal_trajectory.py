"""Tests for Temporal Trajectory Engine."""

import pytest
from oce.backend.temporal.temporal_trajectory import TemporalTrajectoryEngine, Trajectory


class TestTrajectory:
    def test_creation(self):
        t = Trajectory(trajectory_id="t1", trajectory_type="project")
        assert t.trajectory_id == "t1"
        assert t.is_stable is False  # Default coherence is 0.5

    def test_stable(self):
        t = Trajectory(trajectory_id="t1", trajectory_type="project", coherence_score=0.8, entropy_drift=0.1)
        assert t.is_stable is True

    def test_add_state(self):
        t = Trajectory(trajectory_id="t1", trajectory_type="project")
        t.add_state("s1")
        assert "s1" in t.historical_states


class TestTemporalTrajectoryEngine:
    def test_create_trajectory(self):
        engine = TemporalTrajectoryEngine()
        traj = engine.create_trajectory("project", "initial_state")
        assert traj.trajectory_id in engine.trajectories

    def test_record_state(self):
        engine = TemporalTrajectoryEngine()
        traj = engine.create_trajectory("project")
        engine.record_state(traj.trajectory_id, "s1")
        assert "s1" in traj.historical_states

    def test_get_stable(self):
        engine = TemporalTrajectoryEngine()
        t1 = engine.create_trajectory("project")
        engine.update_coherence(t1.trajectory_id, 0.9)
        stable = engine.get_stable_trajectories()
        assert len(stable) >= 1

    def test_get_drifting(self):
        engine = TemporalTrajectoryEngine()
        t1 = engine.create_trajectory("project")
        engine.update_entropy_drift(t1.trajectory_id, 0.8)
        drifting = engine.get_drifting_trajectories()
        assert len(drifting) >= 1

    def test_stats(self):
        engine = TemporalTrajectoryEngine()
        engine.create_trajectory("project")
        engine.create_trajectory("behavioral")
        stats = engine.stats
        assert stats["total_trajectories"] == 2
