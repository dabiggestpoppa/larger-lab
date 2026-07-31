import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 3 End-to-End Integration Test
=====================================
Tests emergent topology: dynamic coupling, topological routing, distributed consensus.

Success criteria:
1. Dynamic coupling: edge weights adapt based on interaction frequency
2. Topographic routing: finds lowest-entropy paths, reroutes on patch failure
3. Distributed consensus: converges without master orchestrator
4. System survives patch kill and reroutes
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.dynamic_coupling import DynamicCouplingEngine
from srrs_opc.topological_router import TopologicalRouter
from srrs_opc.distributed_consensus import DistributedConsensus


def test_1_dynamic_coupling():
    """Test 1: Edge weights adapt based on interaction frequency."""
    print("\n=== Test 1: Dynamic Coupling ===")

    engine = DynamicCouplingEngine()

    # Record interactions
    engine.record_interaction("planner", "execution")
    engine.record_interaction("planner", "execution")
    engine.record_interaction("planner", "execution")
    engine.record_interaction("execution", "memory")
    engine.record_interaction("memory", "repair")

    # Check weights
    w_pe = engine.get_edge_weight("planner", "execution")
    w_em = engine.get_edge_weight("execution", "memory")
    w_mr = engine.get_edge_weight("memory", "repair")

    assert w_pe > w_em, f"Stronger interaction should have higher weight: {w_pe} vs {w_em}"
    print(f"  ✓ planner-execution weight: {w_pe:.3f} (3 interactions)")
    print(f"  ✓ execution-memory weight: {w_em:.3f} (1 interaction)")

    # Test repair weakens coupling
    engine.record_repair("planner", "execution")
    w_pe_after = engine.get_edge_weight("planner", "execution")
    assert w_pe_after < w_pe, f"Repair should weaken coupling: {w_pe_after} vs {w_pe}"
    print(f"  ✓ After repair: planner-execution weight: {w_pe_after:.3f} (weakened)")

    # Test clusters
    clusters = engine.get_clusters(threshold=0.3)
    print(f"  ✓ Clusters found: {len(clusters)}")

    # Test strongest edges
    strongest = engine.get_strongest_edges("planner")
    assert len(strongest) > 0
    print(f"  ✓ Strongest edges for planner: {len(strongest)}")

    print("  ✅ Test 1 PASSED")


def test_2_topological_routing():
    """Test 2: Routing finds lowest-entropy paths and reroutes on failure."""
    print("\n=== Test 2: Topological Routing ===")

    coupling = DynamicCouplingEngine()
    # Build topology
    coupling.record_interaction("planner", "execution")
    coupling.record_interaction("planner", "execution")
    coupling.record_interaction("execution", "memory")
    coupling.record_interaction("memory", "repair")
    coupling.record_interaction("repair", "planner")
    coupling.record_interaction("execution", "repair")

    router = TopologicalRouter(coupling)

    # Find best route
    route = router.find_best_route("planner", "repair")
    assert route is not None, "Should find a route"
    assert route.path[0] == "planner"
    assert route.path[-1] == "repair"
    print(f"  ✓ Best route: {' -> '.join(route.path)} (entropy={route.total_entropy:.3f})")

    # Find alternative routes
    routes = router.find_all_routes("planner", "repair", max_routes=3)
    print(f"  ✓ Found {len(routes)} routes")

    # Stress test: kill a patch
    results = router.stress_test(
        ["planner", "execution", "memory", "repair"],
        kill_patch="execution"
    )
    print(f"  ✓ After killing 'execution': {len(results['rerouted'])} rerouted, {len(results['failed'])} failed")

    # Should still have some routes (via repair->planner or memory->repair)
    assert len(results['rerouted']) > 0, "Should reroute around killed patch"
    print("  ✅ Test 2 PASSED")


def test_3_distributed_consensus():
    """Test 3: Consensus converges without master orchestrator."""
    print("\n=== Test 3: Distributed Consensus ===")

    consensus = DistributedConsensus(convergence_threshold=0.6, sync_probability=0.9)

    # Patches propose values (majority agree, one disagrees)
    consensus.propose("planner", "strategy", "mean_reversion", 0.8)
    consensus.propose("execution", "strategy", "mean_reversion", 0.7)
    consensus.propose("memory", "strategy", "mean_reversion", 0.6)
    consensus.propose("repair", "strategy", "momentum", 0.4)  # Outlier

    # Run gossip rounds until convergence or max rounds
    max_rounds = 10
    converged = False
    for i in range(max_rounds):
        results = consensus.run_gossip_round("strategy")
        check = consensus.check_convergence("strategy")
        if check["converged"]:
            converged = True
            print(f"  ✓ Converged after {i+1} rounds")
            break

    final = consensus.check_convergence("strategy")
    print(f"  ✓ Convergence check: {json.dumps(final, indent=2)}")

    # Get consensus value
    value = consensus.get_consensus_value("strategy")
    if value:
        print(f"  ✓ Consensus value: {value['value']} (conf={value['confidence']:.3f})")

    stats = consensus.get_stats()
    print(f"  ✓ Stats: {json.dumps(stats, indent=2)}")

    assert converged, "Should converge with high sync probability and majority agreement"
    print("  ✅ Test 3 PASSED")


def test_4_patch_kill_survival():
    """Test 4: System survives patch kill — continuity persists."""
    print("\n=== Test 4: Patch Kill Survival ===")

    coupling = DynamicCouplingEngine()
    # Build fully connected topology
    patches = ["planner", "execution", "memory", "repair"]
    for i, a in enumerate(patches):
        for b in patches[i+1:]:
            coupling.record_interaction(a, b)
            coupling.record_interaction(a, b)

    router = TopologicalRouter(coupling)

    # Verify all routes work before kill
    pre_kill_routes = 0
    for src in patches:
        for dst in patches:
            if src != dst:
                route = router.find_best_route(src, dst)
                if route:
                    pre_kill_routes += 1
    print(f"  ✓ Pre-kill routes: {pre_kill_routes}")

    # Kill "execution"
    results = router.stress_test(patches, kill_patch="execution")

    # Verify surviving patches can still route
    surviving = ["planner", "memory", "repair"]
    post_kill_routes = 0
    for src in surviving:
        for dst in surviving:
            if src != dst:
                route = router.find_best_route(src, dst)
                if route:
                    post_kill_routes += 1

    print(f"  ✓ Post-kill routes (3 surviving patches): {post_kill_routes}")
    assert post_kill_routes > 0, "Surviving patches should still route"
    print("  ✅ Test 4 PASSED")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 3: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_dynamic_coupling,
        test_2_topological_routing,
        test_3_distributed_consensus,
        test_4_patch_kill_survival,
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

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
