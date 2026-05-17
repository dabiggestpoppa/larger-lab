"""
Tests for OCE Economics Engine — OCE-9.5a
===========================================
15+ tests covering coherence yield, budget allocation,
entropy debt, sustainability forecasting.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_economics(tmp_path):
    """Reset the EconomicsEngine singleton before each test."""
    from economics_engine import EconomicsEngine
    import economics_engine
    original_path = economics_engine.DB_PATH
    test_db = str(tmp_path / "test_economics.db")
    economics_engine.DB_PATH = test_db
    EconomicsEngine._instance = None
    yield
    EconomicsEngine._instance = None
    economics_engine.DB_PATH = original_path


class TestEconomicsEngineInit:
    def test_singleton_identity(self):
        from economics_engine import get_economics_engine
        e1 = get_economics_engine()
        e2 = get_economics_engine()
        assert e1 is e2

    def test_default_budget(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        status = e.get_budget_status()
        assert status["total_budget"] > 0
        assert "allocations" in status


class TestCoherenceYield:
    def test_initial_yield(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        result = e.get_coherence_yield()
        assert "coherence_yield" in result
        assert "coherence" in result
        assert "recoverability" in result
        assert "adaptability" in result
        assert "entropy_debt" in result
        assert "sync_cost" in result
        assert "resource_consumption" in result

    def test_yield_positive(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        result = e.get_coherence_yield()
        assert result["coherence_yield"] > 0

    def test_update_scores(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        e.update_scores(coherence=0.8, recoverability=0.9, adaptability=0.7)
        result = e.get_coherence_yield()
        assert result["coherence"] == 0.8
        assert result["recoverability"] == 0.9
        assert result["adaptability"] == 0.7


class TestBudgetAllocation:
    def test_allocate_budget(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        result = e.allocate_budget("test_task", 500.0, "Test allocation")
        assert "allocations" in result
        assert "test_task" in result["allocations"]

    def test_budget_status_structure(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        status = e.get_budget_status()
        assert "total_budget" in status
        assert "total_allocated" in status
        assert "total_consumed" in status
        assert "remaining" in status
        assert "utilization_pct" in status

    def test_reallocate_budget(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        e.allocate_budget("from_type", 1000.0)
        result = e.reallocate_budget("from_type", "to_type", 500.0, "Test")
        assert "to_type" in result["allocations"]

    def test_reallocate_insufficient(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        with pytest.raises(ValueError):
            e.reallocate_budget("nonexistent", "to", 100.0)


class TestEntropyDebt:
    def test_initial_debt_zero(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        debt = e.get_entropy_debt()
        assert debt["total_debt"] == 0.0

    def test_record_consumption(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        e.allocate_budget("test_task", 100.0)
        e.record_consumption("test_task", 50.0)
        debt = e.get_entropy_debt()
        assert "by_task_type" in debt


class TestSustainabilityForecast:
    def test_forecast_structure(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        forecast = e.forecast_sustainability(24)
        assert "horizon_hours" in forecast
        assert "sustainable" in forecast
        assert "hours_until_depletion" in forecast
        assert "recommendation" in forecast

    def test_forecast_default_horizon(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        forecast = e.forecast_sustainability()
        assert forecast["horizon_hours"] == 24


class TestOptimizeYield:
    def test_optimize_returns_suggestions(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        result = e.optimize_yield()
        assert "current_yield" in result
        assert "suggestions" in result
        assert len(result["suggestions"]) >= 1

    def test_optimize_with_high_debt(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        e.update_scores(coherence=0.5, recoverability=0.5, adaptability=0.5)
        # Simulate high entropy debt
        e._entropy_debt = 500.0
        result = e.optimize_yield()
        assert any(s["priority"] == "high" for s in result["suggestions"])


class TestBudgetHistory:
    def test_history_after_allocation(self):
        from economics_engine import get_economics_engine
        e = get_economics_engine()
        e.allocate_budget("test", 100.0, "Test")
        history = e.get_budget_history()
        assert len(history) >= 1
