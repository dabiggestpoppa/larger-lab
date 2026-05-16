"""
Phase 9 End-to-End Integration Test
====================================
Tests Entropy Economics: Coherence-Per-Resource Optimization.

Components tested:
1. CoherenceYieldAnalyzer  — Quantify coherence-per-resource efficiency
2. EntropyBudgetManager    — Explicit entropy budgeting (hierarchical)
3. RecoverabilityEconomics — Track and optimize recovery cost across scales
4. AdaptiveCompressionEngine — Compress redundant state, preserve recoverability
5. SyncCostOptimizer       — Sync only when coherence gain > entropy cost
6. ResourceConstrainedCognition — Maintain coherence under resource pressure
7. SustainabilityGovernance — Validate optimizations against constraints
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.coherence_yield_analyzer import YieldRecord, CoherenceYieldAnalyzer
from srrs_opc.entropy_budget_manager import EntropyBudget, EntropyBudgetManager
from srrs_opc.recoverability_economics import RecoveryCostRecord, RecoverabilityEconomics
from srrs_opc.adaptive_compression_engine import CompressionRecord, AdaptiveCompressionEngine
from srrs_opc.sync_cost_optimizer import SyncDecision, SyncCostOptimizer
from srrs_opc.resource_constrained_cognition import (
    OperationPriority, PrioritizedOperation, ResourceConstrainedCognition
)
from srrs_opc.sustainability_governance import (
    OptimizationCandidate, GovernanceDecision, SustainabilityGovernance
)


# ─── Test 1: Coherence Yield Analysis ────────────────────────────────────────

def test_1_coherence_yield_basic():
    """Test 1: Coherence yield = coherence_delta / (entropy_cost + resource_cost)."""
    print("\n=== Test 1: Coherence Yield Basic ===")
    analyzer = CoherenceYieldAnalyzer()

    # Zero cost → infinite yield
    r1 = analyzer.measure_yield("sync", coherence_delta=0.5, entropy_cost=0.0, resource_cost=0.0)
    assert r1.yield_value == float('inf'), f"Expected inf, got {r1.yield_value}"

    # Normal case
    r2 = analyzer.measure_yield("repair", coherence_delta=0.8, entropy_cost=0.2, resource_cost=0.1)
    expected = 0.8 / (0.2 + 0.1)
    assert abs(r2.yield_value - expected) < 0.01, f"Expected ~{expected}, got {r2.yield_value}"

    # Zero coherence → zero yield
    r3 = analyzer.measure_yield("noop", coherence_delta=0.0, entropy_cost=0.5, resource_cost=0.5)
    assert r3.yield_value == 0.0

    print(f"  ✅ Zero cost → inf yield")
    print(f"  ✅ Normal: 0.8/(0.2+0.1) = {r2.yield_value:.3f}")
    print(f"  ✅ Zero coherence → 0 yield")


def test_2_coherence_yield_ranking():
    """Test 2: Operations ranked by average coherence yield."""
    print("\n=== Test 2: Coherence Yield Ranking ===")
    analyzer = CoherenceYieldAnalyzer()

    # Operation A: high yield
    for _ in range(5):
        analyzer.measure_yield("efficient_op", coherence_delta=0.9, entropy_cost=0.05, resource_cost=0.05)

    # Operation B: low yield
    for _ in range(5):
        analyzer.measure_yield("wasteful_op", coherence_delta=0.1, entropy_cost=0.5, resource_cost=0.5)

    ranked = analyzer.rank_operations()
    assert len(ranked) == 2
    assert ranked[0]["operation"] == "efficient_op"
    assert ranked[0]["avg_yield"] > ranked[1]["avg_yield"]

    print(f"  ✅ Ranked: {ranked[0]['operation']} (yield={ranked[0]['avg_yield']:.1f}) > "
          f"{ranked[1]['operation']} (yield={ranked[1]['avg_yield']:.1f})")


def test_3_entropy_budget_consumption():
    """Test 3: Entropy budget tracks consumption and replenishment."""
    print("\n=== Test 3: Entropy Budget Consumption ===")
    budget = EntropyBudget("observer_1", initial_budget=100.0, min_budget=10.0)

    # Consume some budget
    within, remaining = budget.consume(30.0)
    assert within is True
    assert remaining == 70.0
    assert budget.consumed == 30.0

    # Consume more
    within, remaining = budget.consume(50.0)
    assert within is True
    assert remaining == 20.0

    # Try to consume beyond min_budget
    within, remaining = budget.consume(15.0)
    assert remaining == 10.0  # Clamped to min_budget

    # Replenish
    budget.replenish(0.5)
    assert budget.budget > 10.0

    print(f"  ✅ Consumed 30+50, remaining={budget.budget:.1f}")
    print(f"  ✅ Min budget enforced at {budget.min_budget}")
    print(f"  ✅ Replenish works: budget={budget.budget:.1f}")


def test_4_entropy_budget_critical():
    """Test 4: Budget correctly identifies critical state."""
    print("\n=== Test 4: Entropy Budget Critical State ===")
    budget = EntropyBudget("observer_2", initial_budget=100.0, min_budget=10.0)

    assert budget.is_critical() is False

    # Consume 75% of usable budget (75 out of 90 usable = 83%)
    budget.consume(75.0)
    # 83% > 80% threshold → critical
    assert budget.is_critical(threshold=0.8) is True

    # Fresh budget: consume only 50%
    budget2 = EntropyBudget("observer_3", initial_budget=100.0, min_budget=10.0)
    budget2.consume(50.0)
    # 50 out of 90 usable = 55% < 80% → not critical
    assert budget2.is_critical(threshold=0.8) is False

    util = budget.utilization()
    print(f"  ✅ Utilization: {util:.2f}")
    print(f"  ✅ Critical at >80%: {budget.is_critical(threshold=0.8)}")
    print(f"  ✅ Not critical at 55%: {budget2.is_critical(threshold=0.8)}")


def test_5_entropy_budget_manager_hierarchical():
    """Test 5: Hierarchical budget management (global → observer)."""
    print("\n=== Test 5: Hierarchical Budget Manager ===")
    manager = EntropyBudgetManager(global_budget=500.0)

    # Consume from observer (auto-creates observer budget)
    result = manager.consume(40.0, observer_id="planner")
    assert result["approved"] is True
    assert result["observer"]["within_budget"] is True

    # Consume from another observer
    result2 = manager.consume(30.0, observer_id="executor")
    assert result2["approved"] is True

    # Check stats
    stats = manager.get_stats()
    assert stats["global"]["max_budget"] == 500.0
    assert stats["total_observer_budgets"] >= 2
    state = manager.get_budget_state("planner")
    assert state is not None

    # Check budget state
    state = manager.get_budget_state("planner")
    assert state is not None

    # Critical budgets
    manager.consume(200.0, observer_id="planner")  # Heavy consumption
    critical = manager.get_critical_budgets(threshold=0.5)
    print(f"  ✅ Global budget: {stats['global']['max_budget']}")
    print(f"  ✅ Observer count: {stats['total_observer_budgets']}")
    print(f"  ✅ Budget state for planner: {state}")
    print(f"  ✅ Critical budgets: {len(critical)}")


def test_6_recoverability_economics():
    """Test 6: Recovery efficiency tracking across scales."""
    print("\n=== Test 6: Recoverability Economics ===")
    tracker = RecoverabilityEconomics()

    # Local recovery: fast, cheap
    local = tracker.record_recovery(
        scope="local", repair_complexity=0.2,
        reconstruction_speed=0.9, continuity_restored=0.95, sync_cost=0.05
    )
    assert local.scope == "local"
    assert local.efficiency > 0.5  # Efficient local recovery

    # Global recovery: slow, expensive
    global_rec = tracker.record_recovery(
        scope="global", repair_complexity=0.8,
        reconstruction_speed=0.3, continuity_restored=0.6, sync_cost=0.7
    )
    assert global_rec.efficiency < local.efficiency  # Less efficient

    # Scope efficiency returns a dict
    local_eff = tracker.scope_efficiency("local")
    assert isinstance(local_eff, dict)
    assert local_eff["avg_efficiency"] > 0

    # Recoverability score
    score = tracker.recoverability_score()
    assert 0 < score <= 1.0

    # Stats
    stats = tracker.get_stats()
    assert stats["total_recoveries"] == 2

    print(f"  ✅ Local efficiency: {local.efficiency:.3f}")
    print(f"  ✅ Global efficiency: {global_rec.efficiency:.3f}")
    print(f"  ✅ Recoverability score: {score:.3f}")
    print(f"  ✅ Total recoveries: {stats['total_recoveries']}")


def test_7_adaptive_compression():
    """Test 7: Compression preserves recoverability."""
    print("\n=== Test 7: Adaptive Compression ===")
    engine = AdaptiveCompressionEngine()

    # Compress a context-layer target (compressible)
    record = engine.compress(target="stable_sync_routes",
                             original_size=100.0, layer="context")
    assert record.original_size == 100.0
    assert record.compressed_size < record.original_size
    # Context layer has lower recoverability preservation (0.75)
    assert record.recoverability_preserved > 0

    # Compress event layer
    record2 = engine.compress(target="event_logs",
                              original_size=200.0, layer="event")
    assert record2.compressed_size < record2.original_size

    # Compression stats
    stats = engine.get_stats()
    assert stats["total_compressions"] == 2

    # Compression ratio
    ratio = engine.compression_ratio()
    assert ratio > 0

    print(f"  ✅ Compression ratio: {record.ratio:.1f}x")
    print(f"  ✅ Recoverability preserved: {record.recoverability_preserved:.2f}")
    print(f"  ✅ Total compressions: {stats['total_compressions']}")
    print(f"  ✅ Overall compression ratio: {ratio:.2f}")


def test_8_sync_cost_optimizer():
    """Test 8: Sync only when coherence gain exceeds entropy cost."""
    print("\n=== Test 8: Sync Cost Optimizer ===")
    optimizer = SyncCostOptimizer()

    # Positive yield: coherence gain > entropy cost
    decision = optimizer.should_sync("obs_a", "obs_b",
                                     coherence_gain=0.8, entropy_cost=0.2)
    assert decision.approved is True
    assert decision.yield_value == 0.8 / 0.2

    # Negative yield: coherence gain < entropy cost
    decision2 = optimizer.should_sync("obs_c", "obs_d",
                                      coherence_gain=0.1, entropy_cost=0.9)
    assert decision2.approved is False

    # Optimal frequency (cluster only, no interaction_density param)
    freq = optimizer.optimal_sync_frequency(["a", "b", "c"])
    assert 0 < freq <= 1.0

    # Sync efficiency
    eff = optimizer.sync_efficiency()
    assert 0 <= eff <= 1.0

    print(f"  ✅ Positive yield sync approved: {decision.approved}")
    print(f"  ✅ Negative yield sync rejected: {decision2.approved}")
    print(f"  ✅ Optimal frequency: {freq:.3f}")
    print(f"  ✅ Sync efficiency: {eff:.3f}")


def test_9_resource_constrained_cognition():
    """Test 9: Under resource pressure, critical operations preserved."""
    print("\n=== Test 9: Resource-Constrained Cognition ===")
    rcc = ResourceConstrainedCognition()

    # Register operations first
    rcc.register_operation("continuity_check", OperationPriority.CRITICAL, 0.1, 0.9)
    rcc.register_operation("local_repair", OperationPriority.HIGH, 0.2, 0.7)
    rcc.register_operation("full_sync", OperationPriority.MEDIUM, 0.5, 0.4)
    rcc.register_operation("strategic_review", OperationPriority.LOW, 0.3, 0.3)
    rcc.register_operation("redundant_scan", OperationPriority.DEFER, 0.4, 0.1,
                           is_redundant=True)

    # Plenty of resources: all ops pass (redundant included when resources abundant)
    result = rcc.prioritize(available_resources=2.0)
    result_ids = [op.operation_id for op in result]
    assert "continuity_check" in result_ids  # Critical always included
    assert "local_repair" in result_ids  # High priority included

    # Severe constraint: only critical + high
    result_constrained = rcc.prioritize(available_resources=0.25)
    result_ids = [op.operation_id for op in result_constrained]
    # With only 0.25 resources, expensive ops get deferred
    assert "continuity_check" in result_ids  # Critical always preserved
    # Redundant scan should be excluded under constraints
    assert "redundant_scan" not in result_ids

    # Resource utilization
    util = rcc.resource_utilization()
    assert 0 <= util <= 1.0

    # Is overloaded
    overloaded = rcc.is_overloaded()
    assert isinstance(overloaded, bool)

    print(f"  ✅ Full resources: {len(result)} ops approved")
    print(f"  ✅ Constrained: {len(result_constrained)} ops approved")
    print(f"  ✅ Redundant ops correctly excluded")
    print(f"  ✅ Resource utilization: {util:.2f}")


def test_10_sustainability_governance():
    """Test 10: Governance blocks unsafe optimizations."""
    print("\n=== Test 10: Sustainability Governance ===")
    gov = SustainabilityGovernance()

    # Safe optimization
    safe = OptimizationCandidate(
        optimization_id="safe_1", target="sync_interval",
        expected_coherence_gain=0.5, expected_entropy_reduction=0.3,
        expected_recovery_cost=0.1, rollback_feasibility=0.9,
        description="Increase sync interval to reduce overhead"
    )
    decision = gov.validate_optimization(safe)
    assert decision.approved is True

    # Unsafe: destroys recoverability
    unsafe = OptimizationCandidate(
        optimization_id="unsafe_1", target="anchor_store",
        expected_coherence_gain=0.1, expected_entropy_reduction=0.05,
        expected_recovery_cost=0.8, rollback_feasibility=0.2,
        description="Delete all anchors to save memory"
    )
    decision2 = gov.validate_optimization(unsafe)
    assert decision2.approved is False

    # Governance stats
    stats = gov.get_stats()
    assert stats["total_validations"] == 2
    assert stats["approved"] == 1
    assert stats["rejected"] == 1

    # Approval rate
    rate = gov.approval_rate()
    assert rate == 0.5

    print(f"  ✅ Safe optimization approved")
    print(f"  ✅ Unsafe optimization rejected: {decision2.reason[:50]}...")
    print(f"  ✅ Governance stats: {stats['approved']} approved, {stats['rejected']} rejected")
    print(f"  ✅ Approval rate: {rate:.0%}")


# ─── Integration: All 7 Components Working Together ──────────────────────────

def test_11_full_integration():
    """Test 11: All 7 Phase 9 components work together in a coherent pipeline."""
    print("\n=== Test 11: Full Integration Pipeline ===")

    # 1. Set up entropy budgets
    budget_mgr = EntropyBudgetManager(global_budget=1000.0)
    r1 = budget_mgr.consume(15.0, observer_id="planner")
    r2 = budget_mgr.consume(10.0, observer_id="executor")
    assert r1["approved"] and r2["approved"]

    # 2. Analyze coherence yield (need >= min_observations per op)
    analyzer = CoherenceYieldAnalyzer(min_observations=1)
    analyzer.measure_yield("sync", 0.7, 0.1, 0.05)
    analyzer.measure_yield("repair", 0.9, 0.2, 0.1)
    ranked = analyzer.rank_operations()
    assert len(ranked) > 0

    # 3. Record recovery from a local failure
    rec_tracker = RecoverabilityEconomics()
    rec_tracker.record_recovery("local", 0.3, 0.8, 0.9, 0.05)
    rec_tracker.record_recovery("global", 0.7, 0.4, 0.6, 0.5)
    score = rec_tracker.recoverability_score()
    assert score > 0

    # 4. Compress stable state
    compressor = AdaptiveCompressionEngine()
    compressor.compress("sync_routes", 100.0, layer="context")
    assert compressor.get_stats()["total_compressions"] == 1

    # 5. Optimize next sync decision
    sync_opt = SyncCostOptimizer()
    sync_decision = sync_opt.should_sync("planner", "executor", 0.6, 0.15)
    assert sync_decision.approved

    # 6. Under resource pressure, prioritize
    rcc = ResourceConstrainedCognition()
    rcc.register_operation("continuity", OperationPriority.CRITICAL, 0.1, 0.9)
    rcc.register_operation("repair", OperationPriority.HIGH, 0.2, 0.7)
    rcc.register_operation("sync", OperationPriority.MEDIUM, 0.3, 0.5)
    prioritized = rcc.prioritize(available_resources=0.5)
    assert len(prioritized) >= 2

    # 7. Validate optimization through governance
    gov = SustainabilityGovernance()
    safe_candidate = OptimizationCandidate(
        "opt_1", "sync_interval", 0.4, 0.2, 0.15, 0.85
    )
    gov_decision = gov.validate_optimization(safe_candidate)
    assert gov_decision.approved

    # 8. Check budget stats
    stats = budget_mgr.get_stats()

    print(f"  ✅ Budget manager: {stats['total_observer_budgets']} observers")
    print(f"  ✅ Yield analyzer: {len(ranked)} operations ranked")
    print(f"  ✅ Recovery tracker: score={score:.3f}")
    print(f"  ✅ Compressor: {compressor.get_stats()['total_compressions']} compressions")
    print(f"  ✅ Sync optimizer: approved={sync_decision.approved}")
    print(f"  ✅ Resource cognition: {len(prioritized)} ops prioritized")
    print(f"  ✅ Governance: approved={gov_decision.approved}")


# ─── Run All Tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_1_coherence_yield_basic,
        test_2_coherence_yield_ranking,
        test_3_entropy_budget_consumption,
        test_4_entropy_budget_critical,
        test_5_entropy_budget_manager_hierarchical,
        test_6_recoverability_economics,
        test_7_adaptive_compression,
        test_8_sync_cost_optimizer,
        test_9_resource_constrained_cognition,
        test_10_sustainability_governance,
        test_11_full_integration,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Phase 9 Tests: {passed} passed, {failed} failed, {passed+failed} total")
    if failed == 0:
        print("✅ ALL TESTS PASS — Phase 9 Entropy Economics operational")
    else:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)

    def test_all_providers_represented(self):
        """All major providers should be in the catalog."""
        providers = set(g["provider"] for g in GPU_CATALOG)
        assert "octaspace" in providers
        assert "runpod" in providers
        assert "hetzner" in providers

    def test_quick_decide_integration(self):
        """quick_decide should work end-to-end."""
        result = quick_decide("inference", vram=12, hours=4)
        assert result["action"] == "burst"
        assert result["provider"] == "octaspace"
        assert result["cost"] > 0
        assert result["coherence"] > 0
