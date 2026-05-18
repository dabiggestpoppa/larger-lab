"""Tests for Temporal BSP Projection."""

import pytest
from oce.backend.temporal.temporal_bsp import TemporalBSPProjection, TemporalProjection
from oce.backend.temporal.temporal_trajectory import TemporalTrajectoryEngine


class TestTemporalProjection:
    def test_critical(self):
        p = TemporalProjection(
            projection_id="p1", target_trajectory="t1",
            forecast_type="collapse", confidence=0.8,
            time_horizon_hours=24, risk_factors=["low_coherence"],
        )
        assert p.is_critical is True

    def test_not_critical(self):
        p = TemporalProjection(
            projection_id="p1", target_trajectory="t1",
            forecast_type="stability", confidence=0.9,
            time_horizon_hours=24,
        )
        assert p.is_critical is False


class TestTemporalBSPProjection:
    def test_project_stable(self):
        proj = TemporalBSPProjection()
        engine = proj.trajectory_engine
        traj = engine.create_trajectory("project")
        engine.update_coherence(traj.trajectory_id, 0.9)
        result = proj.project_trajectory(traj.trajectory_id)
        assert result.forecast_type in ["stability", "convergence"]

    def test_project_collapse(self):
        proj = TemporalBSPProjection()
        engine = proj.trajectory_engine
        traj = engine.create_trajectory("project")
        engine.update_coherence(traj.trajectory_id, 0.1)
        engine.update_entropy_drift(traj.trajectory_id, 0.9)
        result = proj.project_trajectory(traj.trajectory_id)
        assert result.forecast_type in ["collapse", "drift"]

    def test_project_unknown(self):
        proj = TemporalBSPProjection()
        result = proj.project_trajectory("nonexistent")
        assert result.forecast_type == "unknown"

    def test_get_critical(self):
        proj = TemporalBSPProjection()
        engine = proj.trajectory_engine
        traj = engine.create_trajectory("project")
        engine.update_coherence(traj.trajectory_id, 0.1)
        engine.update_entropy_drift(traj.trajectory_id, 0.9)
        proj.project_trajectory(traj.trajectory_id)
        critical = proj.get_critical_projections()
        assert isinstance(critical, list)

    def test_stats(self):
        proj = TemporalBSPProjection()
        engine = proj.trajectory_engine
        traj = engine.create_trajectory("project")
        proj.project_trajectory(traj.trajectory_id)
        stats = proj.stats
        assert stats["total_projections"] == 1
