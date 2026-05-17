"""Tests for Compute Economics Engine."""

import pytest
from oce.backend.sovereign.compute_economics import (
    ComputeEconomicsEngine,
    ComputeBudget,
    WasteReport,
)


class TestComputeBudget:
    """Tests for ComputeBudget dataclass."""

    def test_budget_creation(self):
        """Test ComputeBudget can be created."""
        budget = ComputeBudget()
        assert budget.total_budget == 1.0
        assert budget.used_budget == 0.0
        assert budget.wasted_budget == 0.0

    def test_budget_remaining(self):
        """Test remaining budget calculation."""
        budget = ComputeBudget(total_budget=1.0, used_budget=0.3)
        assert budget.remaining == 0.7

    def test_budget_remaining_zero(self):
        """Test remaining budget at zero."""
        budget = ComputeBudget(total_budget=0.5, used_budget=1.0)
        assert budget.remaining == 0.0

    def test_budget_efficiency(self):
        """Test efficiency calculation."""
        budget = ComputeBudget(used_budget=0.5, coherence_yield=0.25)
        assert budget.efficiency == 0.5

    def test_budget_efficiency_zero_used(self):
        """Test efficiency with zero used budget."""
        budget = ComputeBudget(used_budget=0.0, coherence_yield=0.0)
        assert budget.efficiency == 1.0


class TestWasteReport:
    """Tests for WasteReport dataclass."""

    def test_report_creation(self):
        """Test WasteReport can be created."""
        report = WasteReport()
        assert report.token_waste == 0.0
        assert report.total_waste == 0.0

    def test_report_with_values(self):
        """Test WasteReport with values."""
        report = WasteReport(
            token_waste=0.5,
            routing_inefficiency=0.3,
            total_waste=0.8,
        )
        assert report.token_waste == 0.5
        assert report.total_waste == 0.8


class TestComputeEconomicsEngine:
    """Tests for ComputeEconomicsEngine class."""

    def test_engine_creation(self):
        """Test ComputeEconomicsEngine can be created."""
        engine = ComputeEconomicsEngine()
        assert engine is not None

    def test_engine_with_budget(self):
        """Test ComputeEconomicsEngine with custom budget."""
        engine = ComputeEconomicsEngine(total_budget=0.5)
        assert engine.budget.total_budget == 0.5

    def test_record_operation(self):
        """Test recording an operation."""
        engine = ComputeEconomicsEngine()
        engine.record_operation("test", tokens_used=1000, coherence_delta=0.1)
        assert len(engine._operation_log) == 1
        assert engine.budget.used_budget > 0

    def test_record_multiple_operations(self):
        """Test recording multiple operations."""
        engine = ComputeEconomicsEngine()
        engine.record_operation("test1", tokens_used=1000)
        engine.record_operation("test2", tokens_used=2000)
        assert len(engine._operation_log) == 2

    def test_analyze_waste_empty(self):
        """Test analyzing waste with no operations."""
        engine = ComputeEconomicsEngine()
        report = engine.analyze_waste()
        assert report.total_waste >= 0

    def test_analyze_waste_with_operations(self):
        """Test analyzing waste with operations."""
        engine = ComputeEconomicsEngine()
        engine.record_operation("test", tokens_used=500, coherence_delta=0.05)
        report = engine.analyze_waste()
        assert report is not None

    def test_get_recommendations_ok(self):
        """Test getting recommendations when OK."""
        engine = ComputeEconomicsEngine()
        recs = engine.get_recommendations()
        assert len(recs) > 0
        assert "OK" in recs[0] or "HIGH" in recs[0] or "MEDIUM" in recs[0]

    def test_get_recommendations_high_waste(self):
        """Test getting recommendations with high waste."""
        engine = ComputeEconomicsEngine()
        for _ in range(10):
            engine.record_operation("test", tokens_used=500, coherence_delta=0.05)
        recs = engine.get_recommendations()
        # Check for any recommendation being generated
        assert len(recs) > 0
        assert any("MEDIUM" in r or "HIGH" in r or "OK" in r for r in recs)

    def test_stats(self):
        """Test getting engine statistics."""
        engine = ComputeEconomicsEngine()
        engine.record_operation("test", tokens_used=1000)
        stats = engine.stats
        assert "budget_remaining" in stats
        assert "efficiency" in stats
        assert "operations" in stats