"""
🦉 RL — V3 Phase 1 Integration Tests
Tests for RL's integration bridge with CC's core resonance modules.
"""

import math
import pytest

from oce.backend.resonance.signal_packet import SignalPacket, SignalField
from oce.backend.resonance.coherence_metrics import CoherenceEngine, CoherenceSnapshot
from oce.backend.resonance.resonance_engine import ResonanceEngine, Constraint
from oce.backend.resonance.field_state import FieldStateManager, FieldState
from oce.backend.resonance.boundary_mapper import BoundaryMapper, Boundary
from oce.backend.resonance.pressure_tracker import PressureTracker
from oce.backend.resonance.rlp_integration import (
    IntegratedResonanceOptimizer,
    IntegratedSignalRouter,
    cc_snapshot_to_rl_metrics,
    rl_metrics_to_cc_snapshot,
    cc_signal_to_rl_packet,
)


# ─── Type Adapter Tests ──────────────────────────────────────────────────

class TestTypeAdapters:
    def test_cc_snapshot_to_rl_metrics(self):
        snap = CoherenceSnapshot(
            timestamp=1.0,
            phase_alignment=0.8,
            entropy_gradient=0.2,
            resonance_density=0.6,
            field_tension=0.3,
            manifold_drift=0.1,
            attractor_stability=0.9,
        )
        rl = cc_snapshot_to_rl_metrics(snap)
        assert rl.phase_alignment == 0.8
        assert rl.entropy_gradient == 0.2
        assert rl.resonance_density == 0.6
        assert rl.field_tension == 0.3
        assert rl.manifold_drift == 0.1
        assert rl.attractor_stability == 0.9

    def test_rl_metrics_to_cc_snapshot(self):
        from oce.backend.dspy_resonance import CoherenceMetrics as RLMetrics
        rl = RLMetrics(0.8, 0.2, 0.6, 0.3, 0.1, 0.9)
        snap = rl_metrics_to_cc_snapshot(rl, timestamp=42.0)
        assert snap.timestamp == 42.0
        assert snap.phase_alignment == 0.8
        assert snap.overall_coherence == pytest.approx(0.8 - 0.2, abs=0.1)

    def test_cc_signal_to_rl_packet(self):
        cc_sig = SignalPacket(
            source="test",
            amplitude=0.8,
            coherence=0.9,
            phase=0.5,  # < π/2 → EMERGENCE
            entropy_delta=0.1,
            boundary_tags=["edge"],
            resonance_targets=["field-a"],
        )
        rl = cc_signal_to_rl_packet(cc_sig)
        assert rl.amplitude == 0.8
        assert rl.coherence == 0.9
        assert "edge" in rl.boundary_tags

    def test_cc_signal_phase_mapping(self):
        """Test that CC's continuous phase maps to RL's discrete phases."""
        from oce.backend.dspy_resonance import SignalPhase
        test_cases = [
            (0.0, SignalPhase.EMERGENCE),
            (math.pi / 4, SignalPhase.EMERGENCE),
            (math.pi / 2, SignalPhase.AMPLIFICATION),
            (math.pi, SignalPhase.COHERENCE),
            (3 * math.pi / 2, SignalPhase.DISSIPATION),
            (2 * math.pi * 0.95, SignalPhase.COLLAPSE),
        ]
        for phase_val, expected_phase in test_cases:
            cc_sig = SignalPacket(
                source="test", amplitude=0.5, coherence=0.5,
                phase=phase_val, entropy_delta=0.1,
            )
            rl = cc_signal_to_rl_packet(cc_sig)
            assert rl.phase == expected_phase, f"phase {phase_val} → {rl.phase} (expected {expected_phase})"


# ─── Integrated Optimizer Tests ──────────────────────────────────────────

class TestIntegratedResonanceOptimizer:
    def test_create(self):
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        assert opt.cc_engine is not None
        assert opt.rl_optimizer is not None

    def test_score_with_cc(self):
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        sig = SignalPacket(source="test", amplitude=0.8, coherence=0.9,
                           phase=0.5, entropy_delta=0.1)
        result = opt.score_with_cc(sig, "obs-1", 0.8, 0.5)
        assert result.signal_id == sig.signal_id
        assert result.observer_id == "obs-1"
        assert 0.0 <= result.score <= 1.0

    def test_score_with_rl(self):
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        sig = SignalPacket(source="test", amplitude=0.8, coherence=0.9,
                           phase=0.5, entropy_delta=0.1)
        snap = CoherenceSnapshot(
            timestamp=1.0, phase_alignment=0.8, entropy_gradient=0.2,
            resonance_density=0.6, field_tension=0.3,
            manifold_drift=0.1, attractor_stability=0.9,
        )
        score = opt.score_with_rl(sig, snap)
        assert 0.0 <= score <= 1.0

    def test_hybrid_score(self):
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        sig = SignalPacket(source="test", amplitude=0.8, coherence=0.9,
                           phase=0.5, entropy_delta=0.1)
        snap = CoherenceSnapshot(
            timestamp=1.0, phase_alignment=0.8, entropy_gradient=0.2,
            resonance_density=0.6, field_tension=0.3,
            manifold_drift=0.1, attractor_stability=0.9,
        )
        result = opt.hybrid_score(sig, "obs-1", 0.8, 0.5, snap)
        assert 'combined_score' in result
        assert 'cc_score' in result
        assert 'rl_score' in result
        assert 0.0 <= result['combined_score'] <= 1.0

    def test_hybrid_score_weighted_toward_cc(self):
        """With cc_weight=1.0, combined should equal CC score."""
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        sig = SignalPacket(source="test", amplitude=0.8, coherence=0.9,
                           phase=0.5, entropy_delta=0.1)
        snap = CoherenceSnapshot(
            timestamp=1.0, phase_alignment=0.8, entropy_gradient=0.2,
            resonance_density=0.6, field_tension=0.3,
            manifold_drift=0.1, attractor_stability=0.9,
        )
        result = opt.hybrid_score(sig, "obs-1", 0.8, 0.5, snap, cc_weight=1.0)
        assert result['combined_score'] == result['cc_score']

    def test_optimize_field(self):
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        fm = FieldStateManager()
        bm = BoundaryMapper()
        pt = PressureTracker()

        # Add some signals
        for i in range(5):
            fm.inject_signal(SignalPacket(
                source=f"src-{i}", amplitude=0.5 + i * 0.1,
                coherence=0.6 + i * 0.05, phase=i * 0.5,
                entropy_delta=0.1,
            ))

        result = opt.optimize_field(fm, bm, pt)
        assert 'field_health' in result
        assert 'coherence' in result
        assert 'rl_recommendation' in result
        assert 'rl_actions' in result


# ─── Integrated Router Tests ─────────────────────────────────────────────

class TestIntegratedSignalRouter:
    def test_create(self):
        router = IntegratedSignalRouter()
        assert router.optimizer is not None

    def test_route(self):
        router = IntegratedSignalRouter()
        fm = FieldStateManager()
        sig = SignalPacket(source="test", amplitude=0.8, coherence=0.9,
                           phase=0.5, entropy_delta=0.1)

        targets = router.route(sig, fm, {"obs-1": (0.0, 0.5)})
        assert isinstance(targets, list)

    def test_route_weak_signal(self):
        router = IntegratedSignalRouter()
        fm = FieldStateManager()
        sig = SignalPacket(source="test", amplitude=0.01, coherence=0.01,
                           phase=0.0, entropy_delta=0.0)

        targets = router.route(sig, fm, {"obs-1": (0.0, 0.5)})
        # Weak signal should get minimal or no routing
        assert isinstance(targets, list)


# ─── Cross-Module Integration Tests ──────────────────────────────────────

class TestCrossModuleIntegration:
    def test_full_pipeline(self):
        """Test: SignalPacket → CoherenceEngine → ResonanceEngine → RL optimizer."""
        # Create field with signals
        fm = FieldStateManager()
        for i in range(10):
            fm.inject_signal(SignalPacket(
                source=f"src-{i}",
                amplitude=0.4 + i * 0.06,
                coherence=0.5 + i * 0.04,
                phase=i * 0.6,
                entropy_delta=0.05 + i * 0.02,
            ))

        # Measure coherence
        coherence = fm.measure_coherence()
        assert isinstance(coherence, CoherenceSnapshot)

        # Score with integrated optimizer
        opt = IntegratedResonanceOptimizer(use_dspy=False)
        signals = fm.signal_field.signals
        for sig in signals[:3]:
            result = opt.hybrid_score(sig, "obs-1", 0.7, 1.0, coherence)
            assert 0.0 <= result['combined_score'] <= 1.0

    def test_boundary_to_pressure_flow(self):
        """Test: BoundaryMapper → PressureTracker → RL optimizer."""
        bm = BoundaryMapper()
        pt = PressureTracker()

        # Create boundary
        b = Boundary(
            boundary_id="b-1",
            boundary_type="coherence",
            position=0.5,
            strength=0.8,
        )
        b.add_pressure(0.3)
        bm.boundaries[b.boundary_id] = b

        # Scan pressure (needs field + mapper)
        from oce.backend.resonance.signal_packet import SignalField
        field = SignalField()
        alerts = pt.scan(field, bm)
        assert isinstance(alerts, list)

    def test_cc_resonance_engine_with_constraints(self):
        """Test: CC's ResonanceEngine with Constraint harmonization."""
        engine = ResonanceEngine()

        c1 = Constraint("c-1", "goal", weight=0.8, phase=0.5, coherence=0.9)
        c2 = Constraint("c-2", "system", weight=0.6, phase=0.6, coherence=0.8)

        resonance = c1.resonance_with(c2)
        assert 0.0 <= resonance <= 1.0

        # Add to engine
        engine.add_constraint(c1)
        engine.add_constraint(c2)

        path = engine.get_action_path()
        assert isinstance(path, list)

    def test_field_state_entropy_budget(self):
        """Test: FieldState entropy budget consumption."""
        fm = FieldStateManager()

        # Inject entropic signal
        fm.inject_signal(SignalPacket(
            source="entropy-source",
            amplitude=0.9,
            coherence=0.2,
            phase=0.0,
            entropy_delta=0.8,
        ))

        state = fm.current_state
        assert state.entropy_budget < 1.0  # Budget consumed

    def test_signal_field_operations(self):
        """Test: SignalField with CC's SignalPacket."""
        field = SignalField(max_size=100)

        for i in range(10):
            field.inject(SignalPacket(
                source=f"src-{i}",
                amplitude=0.5,
                coherence=0.6,
                phase=i * 0.5,
                entropy_delta=0.1,
            ))

        assert field.stats['total_signals'] == 10

        resonant = field.get_resonant_signals()
        assert isinstance(resonant, list)

        entropic = field.get_entropic_signals()
        assert isinstance(entropic, list)
