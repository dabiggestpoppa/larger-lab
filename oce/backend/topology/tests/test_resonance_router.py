"""Tests for ResonanceRouter."""

import pytest
import math
from oce.backend.topology.resonance_router import ResonanceRouter, Route
from oce.backend.topology.collar_field import CollarFieldEngine
from oce.backend.resonance import ResonanceEngine, SignalPacket


class TestRoute:
    def test_viable_route(self):
        r = Route(
            signal_id="sig1", target_observer="obs1", score=0.8,
            coherence_alignment=0.9, entropy_cost=0.2,
            topology_affinity=0.7, resonance_density=0.6,
        )
        assert r.is_viable is True

    def test_non_viable_route(self):
        r = Route(
            signal_id="sig1", target_observer="obs1", score=0.2,
            coherence_alignment=0.3, entropy_cost=0.5,
            topology_affinity=0.1, resonance_density=0.1,
        )
        assert r.is_viable is False

    def test_to_dict(self):
        r = Route(
            signal_id="sig1", target_observer="obs1", score=0.75,
            coherence_alignment=0.8, entropy_cost=0.3,
            topology_affinity=0.6, resonance_density=0.5,
        )
        d = r.to_dict()
        assert d["signal_id"] == "sig1"
        assert d["is_viable"] is True


class TestResonanceRouter:
    def test_calculate_route(self):
        router = ResonanceRouter()
        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.3)
        res_engine = ResonanceEngine()
        
        route = router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=0.5, observer_coherence=0.8,
            resonance_engine=res_engine,
        )
        
        assert isinstance(route, Route)
        assert route.target_observer == "obs1"
        assert 0.0 <= route.score <= 1.0

    def test_route_scoring(self):
        router = ResonanceRouter()
        res_engine = ResonanceEngine()
        
        # High coherence signal should score higher
        high_coherence_signal = SignalPacket(
            source="src1", amplitude=0.9, coherence=0.9, entropy_delta=0.1,
        )
        route1 = router.calculate_route(
            signal=high_coherence_signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.9,
            resonance_engine=res_engine,
        )
        
        # Low coherence signal should score lower
        low_coherence_signal = SignalPacket(
            source="src1", amplitude=0.5, coherence=0.2, entropy_delta=0.8,
        )
        route2 = router.calculate_route(
            signal=low_coherence_signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.9,
            resonance_engine=res_engine,
        )
        
        assert route1.score > route2.score

    def test_route_history(self):
        router = ResonanceRouter()
        signal = SignalPacket(source="src1", amplitude=0.5, coherence=0.5, entropy_delta=0.3)
        res_engine = ResonanceEngine()
        
        router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.5,
            resonance_engine=res_engine,
        )
        
        assert len(router._route_history) == 1

    def test_find_best_route(self):
        router = ResonanceRouter()
        res_engine = ResonanceEngine()
        
        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.2)
        
        # Calculate routes to multiple observers
        route1 = router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.9,
            resonance_engine=res_engine,
        )
        route2 = router.calculate_route(
            signal=signal, observer_id="obs2",
            observer_phase=0.5, observer_coherence=0.5,
            resonance_engine=res_engine,
        )
        
        best = router.find_best_route(signal, {"obs1": (0.0, 0.9), "obs2": (0.5, 0.5)}, res_engine)
        assert best is not None
        assert best.target_observer in ["obs1", "obs2"]

    def test_stats(self):
        router = ResonanceRouter()
        res_engine = ResonanceEngine()
        signal = SignalPacket(source="src1", amplitude=0.5, coherence=0.5, entropy_delta=0.3)
        
        router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.5,
            resonance_engine=res_engine,
        )
        
        stats = router.stats
        assert stats["total_routes"] >= 1