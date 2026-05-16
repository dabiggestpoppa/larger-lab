"""
test_phase9_e2e.py — Phase 9: Entropy Economics Tests

Tests for the entropy economics framework (srrs_opc/entropy_economics.py)
and cloud burst engine (tools/cloud-burst.py).

Success Criteria:
1. Coherence-per-resource optimization
2. Entropy-aware scaling
3. Adaptive compression economics
4. Synchronization efficiency maximization
5. Recoverability preservation under load
6. Sustainability governance
"""

import json
import tempfile
from pathlib import Path

import pytest

from srrs_opc.entropy_economics import (
    EntropyEconomics,
    TaskProfile,
    TaskType,
    TaskComplexity,
    BudgetState,
    GPU_CATALOG,
    quick_decide,
)


# ─── Test 1: Coherence-per-Resource Optimization ─────────────────────────────

class TestCoherencePerResource:
    """Test that the engine maximizes work per dollar spent."""

    def test_local_tasks_have_infinite_coherence(self):
        """CPU-only tasks should have maximum coherence (free)."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("backtest", vram_needed=0, estimated_hours=2)
        decision = eco.decide(task)
        assert decision.action == "local"
        assert decision.estimated_cost == 0.0
        assert decision.coherence_score == 1.0

    def test_burst_tasks_have_positive_coherence(self):
        """GPU tasks should have positive coherence scores."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        decision = eco.decide(task)
        assert decision.action == "burst"
        assert decision.coherence_score > 0

    def test_cheaper_gpu_selected_for_low_entropy(self):
        """Low entropy tasks should get the cheapest available GPU."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("embedding", vram_needed=8, estimated_hours=0.5, complexity="low")
        decision = eco.decide(task)
        assert decision.action == "burst"
        # Should be one of the cheapest options
        assert decision.estimated_cost < 0.10  # Very cheap for low entropy

    def test_coherence_improves_with_efficiency(self):
        """Higher entropy tasks should get better GPUs (higher coherence)."""
        eco = EntropyEconomics(monthly_budget=100.0)

        low_task = TaskProfile("embedding", vram_needed=8, estimated_hours=0.1, complexity="low")
        high_task = TaskProfile("training", vram_needed=24, estimated_hours=8, complexity="high")

        low_decision = eco.decide(low_task)
        high_decision = eco.decide(high_task)

        # Both should be burst
        assert low_decision.action == "burst"
        assert high_decision.action == "burst"
        # High entropy should get more powerful GPU
        assert high_decision.estimated_cost > low_decision.estimated_cost


# ─── Test 2: Entropy-Aware Scaling ────────────────────────────────────────────

class TestEntropyAwareScaling:
    """Test that compute scale matches task complexity."""

    def test_entropy_score_calculation(self):
        """Entropy scores should be between 0 and 1."""
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        assert 0 <= task.entropy_score <= 1

    def test_high_vram_increases_entropy(self):
        """More VRAM needed = higher entropy."""
        low = TaskProfile("embedding", vram_needed=8, estimated_hours=0.1)
        high = TaskProfile("training", vram_needed=40, estimated_hours=12)
        assert high.entropy_score > low.entropy_score

    def test_long_duration_increases_entropy(self):
        """Longer tasks = higher entropy."""
        short = TaskProfile("inference", vram_needed=12, estimated_hours=0.5)
        long = TaskProfile("inference", vram_needed=12, estimated_hours=24)
        assert long.entropy_score > short.entropy_score

    def test_complexity_affects_entropy(self):
        """Higher complexity = higher entropy."""
        low = TaskProfile("inference", vram_needed=12, estimated_hours=1, complexity="low")
        high = TaskProfile("inference", vram_needed=12, estimated_hours=1, complexity="extreme")
        assert high.entropy_score > low.entropy_score

    def test_gpu_selection_scales_with_entropy(self):
        """Higher entropy tasks should get more powerful GPUs."""
        eco = EntropyEconomics(monthly_budget=100.0)

        low = TaskProfile("embedding", vram_needed=8, estimated_hours=0.1, complexity="low")
        high = TaskProfile("training", vram_needed=24, estimated_hours=12, complexity="high")

        low_dec = eco.decide(low)
        high_dec = eco.decide(high)

        # High entropy should get more expensive (powerful) GPU
        assert high_dec.estimated_cost >= low_dec.estimated_cost


# ─── Test 3: Adaptive Compression Economics ──────────────────────────────────

class TestAdaptiveCompressionEconomics:
    """Test that the system adapts to budget constraints."""

    def test_budget_tracking(self):
        """Budget should track spending correctly."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        eco.decide(task)
        assert eco.budget.spent_this_month > 0
        assert eco.budget.sessions_count == 1

    def test_budget_exhaustion_defers_tasks(self):
        """When budget is exhausted, tasks should be deferred."""
        eco = EntropyEconomics(monthly_budget=0.01)  # Tiny budget
        task = TaskProfile("training", vram_needed=24, estimated_hours=8)
        decision = eco.decide(task)
        assert decision.action in ("defer", "reject")

    def test_downgrade_to_fit_budget(self):
        """System should downgrade GPU to fit remaining budget."""
        eco = EntropyEconomics(monthly_budget=0.50)  # Small budget
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        decision = eco.decide(task)
        # Should either find a cheap option or defer
        assert decision.estimated_cost <= 0.50 or decision.action == "defer"

    def test_budget_persistence(self):
        """Budget state should persist to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            budget_file = f.name

        try:
            eco1 = EntropyEconomics(monthly_budget=100.0, budget_file=budget_file)
            task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
            eco1.decide(task)

            # Load budget in new instance
            eco2 = EntropyEconomics(monthly_budget=100.0, budget_file=budget_file)
            assert eco2.budget.sessions_count == 1
            assert eco2.budget.spent_this_month > 0
        finally:
            Path(budget_file).unlink(missing_ok=True)

    def test_multiple_tasks_accumulate_cost(self):
        """Multiple tasks should accumulate costs."""
        eco = EntropyEconomics(monthly_budget=100.0)
        for _ in range(5):
            task = TaskProfile("inference", vram_needed=12, estimated_hours=1)
            eco.decide(task)
        assert eco.budget.sessions_count == 5
        assert eco.budget.spent_this_month > 0


# ─── Test 4: Synchronization Efficiency ───────────────────────────────────────

class TestSynchronizationEfficiency:
    """Test that sync overhead is minimized."""

    def test_decision_is_fast(self):
        """Resource decisions should be near-instantaneous."""
        import time
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)

        start = time.time()
        for _ in range(100):
            eco.decide(task)
        elapsed = time.time() - start

        # 100 decisions should take < 1 second
        assert elapsed < 1.0, f"100 decisions took {elapsed:.2f}s (should be <1s)"

    def test_gpu_catalog_is_complete(self):
        """GPU catalog should have entries for all major providers."""
        providers = set(g["provider"] for g in GPU_CATALOG)
        assert "octaspace" in providers
        assert "runpod" in providers
        assert "hetzner" in providers

    def test_all_gpus_have_required_fields(self):
        """All GPU entries should have required fields."""
        for gpu in GPU_CATALOG:
            assert "provider" in gpu
            assert "gpu" in gpu
            assert "vram" in gpu
            assert "hourly" in gpu
            assert gpu["hourly"] > 0

    def test_quick_decide_convenience(self):
        """quick_decide should work as a one-liner."""
        result = quick_decide("inference", vram=12, hours=4)
        assert "action" in result
        assert "cost" in result
        assert "coherence" in result


# ─── Test 5: Recoverability Preservation ──────────────────────────────────────

class TestRecoverabilityPreservation:
    """Test that the system preserves recoverability under load."""

    def test_task_profiles_are_serializable(self):
        """Task profiles should be serializable for checkpointing."""
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4, complexity="medium")
        data = {
            "task_type": task.task_type,
            "vram_needed": task.vram_needed,
            "estimated_hours": task.estimated_hours,
            "complexity": task.complexity,
            "entropy_score": task.entropy_score,
        }
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0

    def test_decisions_are_logged(self):
        """All decisions should be logged for audit trail."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        eco.decide(task)
        assert len(eco.decisions) == 1
        assert eco.decisions[0].timestamp != ""

    def test_budget_state_is_recoverable(self):
        """Budget state should be recoverable from file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            budget_file = f.name

        try:
            eco = EntropyEconomics(monthly_budget=100.0, budget_file=budget_file)
            task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
            eco.decide(task)

            # File should exist and be valid JSON
            with open(budget_file) as f:
                data = json.load(f)
            assert data["sessions_count"] == 1
            assert data["spent_this_month"] > 0
        finally:
            Path(budget_file).unlink(missing_ok=True)

    def test_report_generation(self):
        """Economics report should be generatable."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        eco.decide(task)
        report = eco.get_economics_report()
        assert "Entropy Economics" in report
        assert "Budget Status" in report


# ─── Test 6: Sustainability Governance ────────────────────────────────────────

class TestSustainabilityGovernance:
    """Test that the system enforces sustainability constraints."""

    def test_budget_never_exceeded(self):
        """Total spending should never exceed budget (tasks deferred instead)."""
        eco = EntropyEconomics(monthly_budget=1.0)
        for _ in range(100):
            task = TaskProfile("training", vram_needed=24, estimated_hours=8)
            eco.decide(task)
        assert eco.budget.spent_this_month <= 1.0

    def test_utilization_calculation(self):
        """Utilization should be calculated correctly."""
        budget = BudgetState(monthly_budget=100.0, spent_this_month=35.0)
        assert budget.utilization == 0.35

    def test_remaining_budget_calculation(self):
        """Remaining budget should be correct."""
        budget = BudgetState(monthly_budget=100.0, spent_this_month=35.0)
        assert budget.remaining == 65.0

    def test_can_afford_check(self):
        """can_afford should return False when budget is exhausted."""
        budget = BudgetState(monthly_budget=100.0, spent_this_month=100.0)
        assert not budget.can_afford

    def test_budget_status_report(self):
        """Budget status should include all key metrics."""
        eco = EntropyEconomics(monthly_budget=100.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        eco.decide(task)
        status = eco.get_budget_status()
        assert "monthly_budget" in status
        assert "spent" in status
        assert "remaining" in status
        assert "utilization" in status
        assert "sessions" in status
        assert "total_hours" in status
        assert "avg_cost_per_hour" in status

    def test_zero_budget_defers_all_gpu_tasks(self):
        """With zero budget, all GPU tasks should be deferred."""
        eco = EntropyEconomics(monthly_budget=0.0)
        task = TaskProfile("inference", vram_needed=12, estimated_hours=4)
        decision = eco.decide(task)
        assert decision.action in ("defer", "reject")


# ─── Integration: Cloud Burst Engine ──────────────────────────────────────────

class TestCloudBurstIntegration:
    """Test integration with tools/cloud-burst.py"""

    def test_estimate_cost_function(self):
        """Cost estimation should return sorted results."""
        from tools.cloud_burst import estimate_cost
        results = estimate_cost(hours=4, vram_min=12)
        assert len(results) > 0
        # Should be sorted by total cost
        costs = [r["total_cost"] for r in results]
        assert costs == sorted(costs)

    def test_recommend_function(self):
        """Recommendation should return a valid GPU."""
        from tools.cloud_burst import recommend_instance
        rec = recommend_instance("inference", vram_needed=12)
        assert rec is not None
        assert "provider" in rec
        assert "gpu" in rec
        assert "hourly" in rec

    def test_recommend_respects_budget(self):
        """Recommendation should respect budget constraint."""
        from tools.cloud_burst import recommend_instance
        rec = recommend_instance("inference", vram_needed=12, max_budget=0.05)
        if rec:
            assert rec["hourly"] <= 0.05

    def test_recommend_different_tasks(self):
        """Different task types should get different recommendations."""
        from tools.cloud_burst import recommend_instance
        recs = {}
        for task_type in ["inference", "training", "backtest", "image_gen"]:
            rec = recommend_instance(task_type, vram_needed=12)
            if rec:
                recs[task_type] = rec["gpu"]
        # Should have recommendations for all task types
        assert len(recs) >= 3
