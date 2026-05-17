"""Tests for BSPProjectionEngine."""

import pytest
import math
from oce.backend.topology.bsp_projection import BSPProjectionEngine, TrajectoryProjection
from oce.backend.resonance import ResonanceEngine, FieldStateManager
from oce.backend.reconstruction import AttractorMemory, Attractor
from oce.backend.resonance.signal_packet import SignalPacket


class TestTrajectoryProjection:
    def test_stable(self):
        proj = TrajectoryProjection(
            projection_id="p1", state_cluster="test",
            trajectory_type="stable", coherence_score=0.8,
            entropy_pressure=0.2, repair_risk=0.1,
        )
        assert proj.is_stable is True
        assert proj.needs_repair is False

    def test_needs_repair(self):
        proj = TrajectoryProjection(
            projection_id="p1", state_cluster="test",
            trajectory_type="chaotic", coherence_score=0.2,
            entropy_pressure=0.8, repair_risk=0.7,
        )
        assert proj.needs_repair is True


class TestBSPProjectionEngine:
    def test_project_stable(self):
        engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()
        res_engine.field_manager.entrain_observer("obs1", 0.0, 0.9)
        res_engine.field_manager.entrain_observer("obs2", 0.1, 0.85)

        proj = engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.9), "obs2": (0.1, 0.85)},
        )
        assert proj.is_stable
        assert proj.coherence_score > 0.5

    def test_project_chaotic(self):
        engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()
        res_engine.field_manager.entrain_observer("obs1", 0.0, 0.2)
        res_engine.field_manager.entrain_observer("obs2", math.pi, 0.1)
        # Inject entropy to create chaotic conditions
        for i in range(50):
            res_engine.field_manager.inject_signal(SignalPacket(
                source=f"noise_{i}", amplitude=0.8, coherence=0.1,
                entropy_delta=0.8,
            ))

        proj = engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.2), "obs2": (math.pi, 0.1)},
        )
        assert proj.trajectory_type in ["chaotic", "divergent"]

    def test_recommended_observers(self):
        engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()
        proj = engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={
                "obs1": (0.0, 0.9),
                "obs2": (0.1, 0.5),
                "obs3": (0.2, 0.3),
            },
        )
        assert len(proj.recommended_observers) >= 1
        # Highest coherence observer should be first
        assert proj.recommended_observers[0] == "obs1"

    def test_pressure_vectors(self):
        engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()
        proj = engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.8)},
        )
        assert "obs1" in proj.pressure_vectors
