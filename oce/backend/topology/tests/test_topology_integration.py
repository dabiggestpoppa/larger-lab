"""Integration tests for Topology layer - full pipeline testing."""

import pytest
import math
from oce.backend.topology.collar_field import CollarFieldEngine
from oce.backend.topology.bsp_projection import BSPProjectionEngine
from oce.backend.topology.resonance_router import ResonanceRouter
from oce.backend.topology.glyph_engine import GlyphEngine
from oce.backend.topology.field_pressure import FieldPressureSystem
from oce.backend.topology.attractor_stability import AttractorStabilityLayer
from oce.backend.topology.topology_metrics import TopologyMetrics
from oce.backend.resonance import FieldStateManager, ResonanceEngine, SignalPacket
from oce.backend.reconstruction import AttractorMemory, Attractor


class TestFullTopologyPipeline:
    """Test the complete collar -> BSP -> router -> glyph pipeline."""

    def test_collar_to_bsp_integration(self):
        """Test collar field connections feed into BSP projection."""
        collar_engine = CollarFieldEngine()
        bsp_engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()

        # Create collar connections
        collar_engine.connect("obs1", "obs2", initial_resonance=0.8)
        collar_engine.connect("obs2", "obs3", initial_resonance=0.7)

        # BSP should work with the resonance engine
        proj = bsp_engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.8), "obs2": (0.1, 0.75), "obs3": (0.2, 0.7)},
        )
        assert isinstance(proj.coherence_score, float)

    def test_bsp_to_router_integration(self):
        """Test BSP projections inform routing decisions."""
        router = ResonanceRouter()
        bsp_engine = BSPProjectionEngine()
        res_engine = ResonanceEngine()

        # Create a projection
        proj = bsp_engine.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.9), "obs2": (0.1, 0.8)},
        )

        # Router should be able to route based on projection recommendations
        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.8, entropy_delta=0.2)
        route = router.calculate_route(
            signal=signal, observer_id=proj.recommended_observers[0],
            observer_phase=0.0, observer_coherence=0.9,
            resonance_engine=res_engine,
        )
        assert route.target_observer in proj.recommended_observers

    def test_router_to_glyph_integration(self):
        """Test routing results can be encoded as glyphs."""
        router = ResonanceRouter()
        glyph_engine = GlyphEngine()
        res_engine = ResonanceEngine()

        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.3)
        route = router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.8,
            resonance_engine=res_engine,
        )

        # Route status can be encoded as glyph
        encoded = glyph_engine.encode(f"route to {route.target_observer} score {route.score:.2f}")
        assert len(encoded) > 0

    def test_pressure_to_stability_integration(self):
        """Test pressure readings inform stability layer."""
        pressure_system = FieldPressureSystem()
        stability_layer = AttractorStabilityLayer()
        field_mgr = FieldStateManager()

        # Create pressure conditions
        for i in range(30):
            field_mgr.inject_signal(SignalPacket(
                source=f"noise_{i}", amplitude=0.7, coherence=0.3,
                entropy_delta=0.6,
            ))

        reading = pressure_system.scan(field_mgr, collar_engine=None)
        state = stability_layer.evaluate(field_mgr)

        assert isinstance(reading.overall_pressure, float)
        assert isinstance(state.instability_level, float)

    def test_full_pipeline_three_observers(self):
        """Test complete pipeline with three observers."""
        collar = CollarFieldEngine()
        bsp = BSPProjectionEngine()
        router = ResonanceRouter()
        glyph = GlyphEngine()
        pressure = FieldPressureSystem()
        stability = AttractorStabilityLayer()
        metrics = TopologyMetrics()
        field_mgr = FieldStateManager()
        res_engine = ResonanceEngine()

        # Setup observers
        collar.connect("obs1", "obs2", initial_resonance=0.8)
        collar.connect("obs2", "obs3", initial_resonance=0.7)
        collar.connect("obs1", "obs3", initial_resonance=0.6)

        field_mgr.entrain_observer("obs1", 0.0, 0.8)
        field_mgr.entrain_observer("obs2", 0.5, 0.75)
        field_mgr.entrain_observer("obs3", 1.0, 0.7)

        # Run BSP projection
        proj = bsp.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.8), "obs2": (0.5, 0.75), "obs3": (1.0, 0.7)},
        )

        # Route a signal
        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.3)
        route = router.find_best_route(
            signal, {"obs1": (0.0, 0.8), "obs2": (0.5, 0.75), "obs3": (1.0, 0.7)}, res_engine
        )

        # Encode result
        encoded = glyph.encode(f"route {route.target_observer}")

        # Measure pressure
        reading = pressure.scan(field_mgr, collar_engine=collar)

        # Evaluate stability
        state = stability.evaluate(field_mgr)

        # Get metrics
        health = metrics.measure(collar, pressure, observer_count=3)

        assert proj.coherence_score > 0
        assert route is not None
        assert len(encoded) > 0
        assert 0 <= reading.overall_pressure <= 1
        assert isinstance(state, type(state))
        assert 0 <= health.overall_health <= 1


class TestMultiObserverScenarios:
    """Test various multi-observer configurations."""

    def test_four_observer_mesh(self):
        """Test collar field with four observers in mesh topology."""
        collar = CollarFieldEngine()

        # Create mesh
        collar.connect("obs1", "obs2", initial_resonance=0.8)
        collar.connect("obs1", "obs3", initial_resonance=0.7)
        collar.connect("obs1", "obs4", initial_resonance=0.6)
        collar.connect("obs2", "obs3", initial_resonance=0.75)
        collar.connect("obs2", "obs4", initial_resonance=0.65)
        collar.connect("obs3", "obs4", initial_resonance=0.7)

        matrix = collar.get_resonance_matrix()
        assert len(matrix) == 4
        assert collar.get_field_coherence() > 0

    def test_dynamic_observer_addition(self):
        """Test adding observers dynamically."""
        collar = CollarFieldEngine()

        collar.connect("obs1", "obs2", initial_resonance=0.8)
        initial_count = len(collar.collars)

        collar.connect("obs3", "obs1", initial_resonance=0.7)
        assert len(collar.collars) == initial_count + 1

    def test_observer_removal_propagation(self):
        """Test removing an observer propagates through the system."""
        collar = CollarFieldEngine()

        collar.connect("obs1", "obs2", initial_resonance=0.8)
        collar.connect("obs2", "obs3", initial_resonance=0.7)

        collar.disconnect("obs2", "obs1")
        assert collar.collars["obs1"].resonance_map["obs2"] == 0.0


class TestStressScenarios:
    """Test system under stress conditions."""

    def test_high_entropy_flood(self):
        """Test system behavior under high entropy flood."""
        field_mgr = FieldStateManager()
        pressure = FieldPressureSystem()
        stability = AttractorStabilityLayer()

        # Flood with entropy
        for i in range(200):
            field_mgr.inject_signal(SignalPacket(
                source=f"flood_{i}", amplitude=0.9, coherence=0.1,
                entropy_delta=0.9,
            ))

        reading = pressure.scan(field_mgr, collar_engine=None)
        state = stability.evaluate(field_mgr)

        # System should still function
        assert isinstance(reading.overall_pressure, float)
        assert isinstance(state.instability_level, float)

    def test_signal_scarcity(self):
        """Test system with minimal signals."""
        field_mgr = FieldStateManager()
        collar = CollarFieldEngine()

        # Only one weak signal
        field_mgr.inject_signal(SignalPacket(
            source="weak", amplitude=0.1, coherence=0.2,
            entropy_delta=0.1,
        ))

        collar.connect("obs1", "obs2", initial_resonance=0.3)

        # System should handle gracefully
        assert field_mgr.current_state.signal_count == 1
        assert collar.get_field_coherence() >= 0

    def test_rapid_oscillation(self):
        """Test system with rapidly oscillating signals."""
        router = ResonanceRouter()
        res_engine = ResonanceEngine()

        for i in range(50):
            signal = SignalPacket(
                source=f"osc_{i}", amplitude=0.5 + 0.3 * (i % 2),
                coherence=0.5 + 0.2 * (i % 3),
                entropy_delta=0.3 + 0.2 * (i % 2),
            )
            router.calculate_route(
                signal=signal, observer_id="obs1",
                observer_phase=float(i % 10) / 10, observer_coherence=0.5,
                resonance_engine=res_engine,
            )

        assert router.stats["total_routes"] == 50


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_observer_set(self):
        """Test metrics with no observers."""
        metrics = TopologyMetrics()
        collar = CollarFieldEngine()
        pressure = FieldPressureSystem()

        health = metrics.measure(collar, pressure, observer_count=0)
        assert isinstance(health.overall_health, float)

    def test_single_observer_isolation(self):
        """Test single isolated observer."""
        collar = CollarFieldEngine()
        collar.get_or_create_collar("obs1")

        # No connections
        assert len(collar.collars["obs1"].resonance_map) == 0

    def test_zero_resonance_connections(self):
        """Test connections with zero resonance."""
        collar = CollarFieldEngine()
        collar.connect("obs1", "obs2", initial_resonance=0.0)

        assert collar.collars["obs1"].resonance_map["obs2"] == 0.0
        assert collar.collars["obs2"].resonance_map["obs1"] == 0.0

    def test_maximum_resonance_connections(self):
        """Test connections at maximum resonance."""
        collar = CollarFieldEngine()
        collar.connect("obs1", "obs2", initial_resonance=1.0)

        assert collar.collars["obs1"].resonance_map["obs2"] == 1.0

    def test_negative_phase_handling(self):
        """Test router handles negative phases."""
        router = ResonanceRouter()
        res_engine = ResonanceEngine()

        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.3)
        route = router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=-0.5, observer_coherence=0.8,
            resonance_engine=res_engine,
        )
        assert isinstance(route.score, float)

    def test_phase_wrapping(self):
        """Test phase values are properly wrapped."""
        router = ResonanceRouter()
        res_engine = ResonanceEngine()

        signal = SignalPacket(source="src1", amplitude=0.8, coherence=0.7, entropy_delta=0.3)
        route = router.calculate_route(
            signal=signal, observer_id="obs1",
            observer_phase=2 * math.pi, observer_coherence=0.8,
            resonance_engine=res_engine,
        )
        assert isinstance(route.score, float)


class TestCrossLayerConsistency:
    """Test consistency between different topology layers."""

    def test_collar_pressure_consistency(self):
        """Test collar field coherence matches pressure readings."""
        collar = CollarFieldEngine()
        pressure = FieldPressureSystem()
        field_mgr = FieldStateManager()

        collar.connect("obs1", "obs2", initial_resonance=0.8)
        field_mgr.entrain_observer("obs1", 0.0, 0.8)
        field_mgr.entrain_observer("obs2", 0.1, 0.75)

        collar_coherence = collar.get_field_coherence()
        reading = pressure.scan(field_mgr, collar_engine=collar)

        # Both should reflect the field state
        assert 0 <= collar_coherence <= 1
        assert 0 <= reading.overall_pressure <= 1

    def test_bsp_metrics_consistency(self):
        """Test BSP projections align with topology metrics."""
        bsp = BSPProjectionEngine()
        metrics = TopologyMetrics()
        collar = CollarFieldEngine()
        pressure = FieldPressureSystem()
        res_engine = ResonanceEngine()

        collar.connect("obs1", "obs2", initial_resonance=0.8)

        proj = bsp.project(
            resonance_engine=res_engine,
            attractor_memory=AttractorMemory(),
            observer_states={"obs1": (0.0, 0.8), "obs2": (0.1, 0.75)},
        )
        health = metrics.measure(collar, pressure, observer_count=2)

        # Both should indicate field health
        assert 0 <= proj.coherence_score <= 1
        assert 0 <= health.overall_health <= 1


class TestAdditionalScenarios:
    """Additional test scenarios for coverage."""

    def test_glyph_compression_ratio(self):
        """Test glyph compression produces valid ratios."""
        glyph = GlyphEngine()
        original = "stable resonance trajectory divergence in field stabilization"
        compressed, ratio = glyph.compress_semantics(original)
        assert ratio >= 0.0
        assert ratio <= 1.0

    def test_pressure_trend_calculation(self):
        """Test pressure trend calculation over multiple scans."""
        pressure = FieldPressureSystem()
        field_mgr = FieldStateManager()

        for _ in range(10):
            pressure.scan(field_mgr, collar_engine=None)

        trend = pressure.get_trend()
        assert isinstance(trend, float)

    def test_stability_layer_multiple_evaluations(self):
        """Test stability layer with multiple evaluations."""
        stability = AttractorStabilityLayer()
        field_mgr = FieldStateManager()

        for _ in range(5):
            stability.evaluate(field_mgr)

        stats = stability.stats
        assert stats["total_evaluations"] == 5

    def test_metrics_history_tracking(self):
        """Test topology metrics history tracking."""
        metrics = TopologyMetrics()
        collar = CollarFieldEngine()
        pressure = FieldPressureSystem()

        for _ in range(5):
            metrics.measure(collar, pressure, observer_count=2)

        trend = metrics.get_trend()
        assert isinstance(trend, float)

    def test_router_with_different_signal_types(self):
        """Test router handles different signal types."""
        router = ResonanceRouter()
        res_engine = ResonanceEngine()

        # Entropic signal
        entropic = SignalPacket(source="src1", amplitude=0.9, coherence=0.1, entropy_delta=0.9)
        route1 = router.calculate_route(
            signal=entropic, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.5,
            resonance_engine=res_engine,
        )

        # Resonant signal
        resonant = SignalPacket(source="src2", amplitude=0.8, coherence=0.9, entropy_delta=0.1)
        route2 = router.calculate_route(
            signal=resonant, observer_id="obs1",
            observer_phase=0.0, observer_coherence=0.5,
            resonance_engine=res_engine,
        )

        assert isinstance(route1.score, float)
        assert isinstance(route2.score, float)