# Phase 3: Emergent Topology — Design Document

> **Author:** AS (Assistant Manager) — based on CC's implementation
> **Date:** 2026-05-16
> **Status:** ✅ Implemented and tested (4/4 tests passing)

## Goal

Allow cognition geometry to self-organize dynamically. The system stops behaving like coordinated services and begins behaving like a recursive adaptive field.

## Architecture

### 1. Dynamic Coupling Engine (`dynamic_coupling.py`)

**Purpose:** Patch relationships adapt based on interaction frequency, repair density, and synchronization necessity.

**Key Design Decisions:**
- Edge weights range from 0.0 (weak/disconnected) to 1.0 (strong/critical)
- Weights increase with interaction frequency (reinforced by repeated use)
- Weights decrease with repair density (frequent repairs = unstable connection)
- No permanent authority hierarchy — all coupling is probabilistic

**Algorithm:**
```
weight = base_weight + (interaction_count × 0.1) - (repair_count × 0.05)
weight = clamp(weight, 0.0, 1.0)
```

### 2. Topological Router (`topological_router.py`)

**Purpose:** Routes messages between patches using entropy-based path selection instead of fixed pipelines.

**Key Design Decisions:**
- Entropy = 1 - edge_weight (higher weight = lower entropy = better path)
- Uses Dijkstra's algorithm on the coupling graph
- Automatically reroutes when patches fail
- No hardcoded routes — all routing emerges from topology

**Algorithm:**
```
entropy(edge) = 1 - edge.weight
path_cost = Σ entropy(edge) for edge in path
best_route = min(path_cost) via Dijkstra
```

### 3. Distributed Consensus (`distributed_consensus.py`)

**Purpose:** No master orchestrator — truth stabilizes recursively through gossip-style probabilistic synchronization.

**Key Design Decisions:**
- Each patch maintains local confidence (0.0-1.0) per topic
- Consensus emerges via gossip protocol (not voting)
- Bayesian-inspired confidence updating:
  - Matching values → reinforce confidence
  - Conflicting values → decrease confidence, consider switching
  - Switch if challenger has significantly higher confidence (+0.3 threshold)
- Convergence detected when all patches agree within confidence tolerance

**Algorithm:**
```
1. Patch receives value + confidence from neighbor
2. If value matches local: confidence += received × 0.1
3. If value differs: confidence -= received × 0.05
4. If challenger_conf > local_conf + 0.3: adopt value at 80% of challenger's confidence
5. Repeat until convergence (all patches agree)
```

## Success Criteria (All Met ✅)

1. ✅ **Dynamic coupling** — Edge weights adjust based on interaction frequency
2. ✅ **Topological routing** — Finds lowest-entropy paths, reroutes on patch failure
3. ✅ **Distributed consensus** — Converges without master orchestrator (3 rounds avg)
4. ✅ **Patch kill survival** — System reroutes and maintains continuity after patch failure

## Test Results

```
=== Test 1: Dynamic Coupling ===
  ✓ planner-execution weight: 0.636 (3 interactions)
  ✓ execution-memory weight: 0.550 (1 interaction)
  ✓ After repair: planner-execution weight: 0.586 (weakened)
  ✅ PASSED

=== Test 2: Topological Routing ===
  ✓ Best route: planner -> repair (entropy=0.450)
  ✓ After killing 'execution': 6 rerouted, 0 failed
  ✅ PASSED

=== Test 3: Distributed Consensus ===
  ✓ Converged after 3 rounds
  ✓ All patches agree: mean_reversion (conf=0.81)
  ✅ PASSED

=== Test 4: Patch Kill Survival ===
  ✓ Pre-kill routes: 12
  ✓ Post-kill routes (3 surviving patches): 6
  ✅ PASSED

Results: 4 passed, 0 failed
```

## Phase 4 Readiness

Phase 3 components are ready for Phase 4 (Workspace Integration):
- Dynamic coupling can drive tool adapter strength
- Topological router can route between workspace surfaces
- Distributed consensus can synchronize across tools

### Next Steps for Phase 4:
1. Create Tool Adapter Layer (bounded adapter interfaces)
2. Implement Operational Surface Abstraction
3. Build Cross-Tool Synchronization
4. Implement Workspace Decoupling
5. Add Execution Verification
6. Set up Persistence Isolation
