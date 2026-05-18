"""
🦉 RL — V3 Phase 1 Integration Tests
Tests for resonance module interoperability.

These tests verify that RL's dspy_resonance module integrates
correctly with CC's core resonance modules as they're built.
"""

import pytest

from oce.backend.dspy_resonance import (
    CoherenceMetrics,
    FieldStateManager,
    ResonanceOptimizer,
    SignalPacket,
    SignalPhase,
    SignalRouter,
)


class TestResonanceIntegration:
    """End-to-end resonance field tests."""

    def _make_field(self, n_signals: int = 10) -> FieldStateManager:
        """Helper: create a field with n test signals."""
        fm = FieldStateManager("test-field", capacity=100)
        phases = list(SignalPhase)
        for i in range(n_signals):
            s = SignalPacket(
                signal_id=f"sig-{i:04d}",
                source=f"source-{i % 3}",
                amplitude=0.3 + (i * 0.07) % 0.7,
                coherence=0.4 + (i * 0.06) % 0.6,
                phase=phases[i % len(phases)],
                entropy_delta=-0.5 + (i * 0.1) % 1.0,
                boundary_tags=[f"boundary-{i % 5}"],
                resonance_targets=[f"target-{(i + 1) % 7}", f"target-{(i + 2) % 7}"],
            )
            fm.add_signal(s)
        return fm

    def test_full_pipeline(self):
        """Test: create field → compute metrics → optimize → route."""
        fm = self._make_field(20)
        metrics = fm.compute_metrics()
        optimizer = ResonanceOptimizer(use_dspy=False)
        router = SignalRouter(optimizer)

        # Register some routes
        for i in range(5):
            router.register_route(f"sig-{i:04d}", [f"target-{i}"])

        # Optimize field
        result = optimizer.optimize_field(list(fm.signals.values()), metrics)
        assert result['recommendation'] == 'optimize'
        assert result['viable_count'] > 0

        # Route top signal
        top_signal = list(fm.signals.values())[0]
        targets = router.route_signal(top_signal, metrics)
        assert isinstance(targets, list)

    def test_field_pruning_improves_metrics(self):
        """Test: pruning collapsed signals improves field coherence."""
        fm = FieldStateManager("prune-field", capacity=100)
        # Add 15 healthy signals
        for i in range(15):
            fm.add_signal(SignalPacket(
                signal_id=f"healthy-{i}",
                source="src",
                amplitude=0.7,
                coherence=0.8,
                phase=SignalPhase.COHERENCE,
                entropy_delta=0.1,
            ))

        # Add 5 collapsed signals
        for i in range(5):
            fm.add_signal(SignalPacket(
                signal_id=f"collapsed-{i}",
                source="decay",
                amplitude=0.01,
                coherence=0.01,
                phase=SignalPhase.COLLAPSE,
                entropy_delta=0.9,
            ))

        assert len(fm.signals) == 20
        pruned = fm.prune_collapsed()
        assert pruned == 5
        # After pruning, only healthy signals remain
        assert len(fm.signals) == 15

    def test_local_view_respects_locality(self):
        """Test: local view returns limited signals (locality principle)."""
        fm = self._make_field(50)
        view = fm.get_local_view("observer-1", radius=10)
        assert len(view) == 10

    def test_performance_index_bounds(self):
        """Test: performance index is always in [0, 1]."""
        fm = self._make_field(30)
        metrics = fm.compute_metrics()
        assert 0.0 <= metrics.performance_index <= 1.0

    def test_resonance_score_bounds(self):
        """Test: resonance scores are always in [0, 1]."""
        fm = self._make_field(20)
        metrics = fm.compute_metrics()
        optimizer = ResonanceOptimizer(use_dspy=False)

        for signal in fm.signals.values():
            score = optimizer.score_resonance(signal, metrics)
            assert 0.0 <= score <= 1.0

    def test_empty_field_handling(self):
        """Test: empty field doesn't crash any component."""
        fm = FieldStateManager("empty-field")
        metrics = fm.compute_metrics()

        optimizer = ResonanceOptimizer(use_dspy=False)
        result = optimizer.optimize_field([], metrics)
        assert result['recommendation'] == 'no_viable_signals'

        router = SignalRouter(optimizer)
        targets = router.route_signal(
            SignalPacket("s", "src", 0.5, 0.5, SignalPhase.COHERENCE, 0.0),
            metrics,
        )
        assert targets == []

    def test_high_entropy_field(self):
        """Test: high entropy field triggers correct recommendations."""
        fm = FieldStateManager("entropy-field", capacity=100)
        for i in range(20):
            fm.add_signal(SignalPacket(
                f"s{i}", "src", 0.8, 0.8, SignalPhase.COHERENCE,
                entropy_delta=0.9,  # High entropy
            ))

        metrics = fm.compute_metrics()
        optimizer = ResonanceOptimizer(use_dspy=False)
        result = optimizer.optimize_field(list(fm.signals.values()), metrics)

        assert 'reduce_entropy' in result['suggested_actions']

    def test_metrics_history_tracking(self):
        """Test: metrics history grows with each computation."""
        fm = self._make_field(10)
        for _ in range(5):
            fm.compute_metrics()

        assert len(fm._metrics_history) == 5

    def test_signal_lifecycle(self):
        """Test: full signal lifecycle (add → route → prune)."""
        fm = FieldStateManager("lifecycle-field", capacity=50)
        optimizer = ResonanceOptimizer(use_dspy=False)
        router = SignalRouter(optimizer)

        # Add signals
        for i in range(10):
            fm.add_signal(SignalPacket(
                f"sig-{i}", "src", 0.7, 0.8, SignalPhase.COHERENCE, 0.1,
                resonance_targets=["field-b"],
            ))

        # Compute and route
        metrics = fm.compute_metrics()
        for sig in list(fm.signals.values())[:3]:
            router.route_signal(sig, metrics)

        # Collapse some signals
        for i in range(3):
            if f"sig-{i}" in fm.signals:
                fm.signals[f"sig-{i}"].phase = SignalPhase.COLLAPSE
                fm.signals[f"sig-{i}"].coherence = 0.01

        # Prune
        pruned = fm.prune_collapsed()
        assert pruned == 3
        assert len(fm.signals) == 7
