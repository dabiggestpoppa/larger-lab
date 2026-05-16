---
name: srra-oph-build
description: >
  SRRA-OPH (Self-Repairing Recursive Architecture — Observer Patch Harness) build skill.
  Use when building, testing, or transitioning between SRRA-OPH phases.
  Covers all 9 phases. Updated with Book 2 integration: overlap-first architecture,
  collar consensus theory, reconstructive continuity, repair-first cognition.
version: 2.0.0
---

# SRRA-OPH Build Skill v2

## Architecture Overview

SRRA-OPH is bounded adaptive cognition infrastructure. Not agents — **infrastructure that thinks**.

### Core Principles (NEVER violate)
1. **No global state** — Every patch is bounded and incomplete
2. **Repair before scale** — Stabilize topology before adding complexity
3. **Memory must compress** — Sublinear persistence growth
4. **Every node self-stabilizes** — Local repair, selective sync
5. **Consensus must emerge** — No hardcoded truth authority
6. **Overlap is computation** — Edges are active reconciliation regions, not communication links
7. **Repair creates continuity** — No repair = no stable cognition
8. **Identity is trajectory** — Reconstructable directional coherence, not persistent state

## Phase Map

| Phase | Name | Status | Key Components |
|-------|------|--------|----------------|
| 0 | Foundational Reality Check | ✅ | Bounded cognition definition |
| 1 | Minimal Observer Mesh | ✅ | 4 patches + CollarLayer + AgentBridge |
| 2 | Reconstruction + Recoverability | ✅ | Anchors, drift, validation, synthesis, resolution, propagation |
| 3 | Emergent Topology (UPDATED) | 🔄 | Active collar fields, local consensus, overlap routing, repair-first continuity, MSR |
| 4 | Workspace Integration (UPDATED) | 📋 | Capability fields, overlap-aware tooling, reconstruction-safe execution, entropy-aware scheduling |
| 5 | Long-Horizon Continuity (UPDATED) | 📋 | Trajectory reconstruction, continuity collars, drift-tolerant identity, temporal attractors, MCR |
| 6 | Recursive Self-Modeling | 📋 | Topology mapping, sync analytics, repair optimization |
| 7 | Multi-Scale Cognitive Fields | 📋 | Nested observer hierarchies, regional clusters |
| 8 | Operator Coevolution | 📋 | Pattern recognition, strategic alignment |
| 9 | Entropy Economics | 📋 | Coherence-per-resource optimization |
| 4 | Workspace Integration | 📋 | Tool adapter layer, surface abstraction, cross-tool sync |
| 5 | Long-Horizon Continuity | 📋 | Temporal compression, identity attractors, drift tracking |
| 6 | Recursive Self-Modeling | 📋 | Topology mapping, sync analytics, repair optimization |
| 7 | Multi-Scale Cognitive Fields | 📋 | Nested observer hierarchies, regional clusters |
| 8 | Operator Coevolution | 📋 | Pattern recognition, strategic alignment |
| 9 | Entropy Economics | 📋 | Coherence-per-resource optimization |

## Component Patterns

### Observer Patch (all phases)
```python
class BasePatch:
    - patch_id: str
    - local_state: dict (bounded)
    - collar_schema: dict
    - repair_loop(): bool
    - sync_with_collar(other_patch): dict
```

### Collar Protocol (Phase 1+)
```json
{
  "overlap_id": "patch_a_patch_b",
  "coherence_score": 0.0-1.0,
  "constraint_alignment": 0.0-1.0,
  "drift_flags": [],
  "entropy_load": 0.0-1.0
}
```

### Recovery Anchor (Phase 2+)
```python
- anchor_id: str
- content: str (compressed invariant)
- weight: float (0-1, reinforcement-based)
- source: str
- created_at: datetime
- last_reinforced: datetime
- decay_rate: float
```

### Dynamic Coupling (Phase 3)
```python
- edge_weight: float (interaction frequency × repair density)
- sync_utility_score: float
- adaptive: bool (weights update based on operational reality)
```

## Testing Requirements Per Phase

### Phase 1 Tests
- [ ] Patch independence (no total-state dependency)
- [ ] Collar inconsistency detection
- [ ] Local repair activation
- [ ] Partial failure survival

### Phase 2 Tests
- [ ] Sparse reconstruction (90% deletion → coherent core)
- [ ] Drift detection (stale/weight drift)
- [ ] Contradiction detection and resolution
- [ ] Constraint propagation ripple

### Phase 3 Tests
- [ ] Dynamic coupling adaptation (edge weights adjust)
- [ ] Topological routing (lowest entropy path)
- [ ] Distributed convergence (no master node)
- [ ] Stress recovery (patch kill → reroute)

### Phase 4+ Tests
- [ ] Tool swap survival
- [ ] Workspace loss recovery
- [ ] Execution verification
- [ ] Routing overload adaptation

## Phase 3 (Updated) — Adaptive Topology + Overlap Consensus Geometry

### Core Shift
- **OLD:** Observer nodes exchange synchronization, memory, repair info
- **NEW:** Overlap collars are the actual continuity engine; observers are local bounded reconstruction fields

### New Principle
> Coherence emerges from active overlap reconciliation under bounded observer visibility.

### Active Collar Fields (Key Upgrade)
Edges become **active computational reconciliation regions** that perform:
- Continuity reconciliation, contradiction stabilization, sparse consensus formation, trajectory reconstruction
- Each collar maintains: overlap state, contradiction map, repair queue, confidence gradients, entropy score, reconstruction viability

### Local Consensus Engines
- Synchronization transfers information; **consensus produces stable overlap closure**
- Consensus only occurs where overlap exists. Probabilistic closure, not universal truth. Remains local.

### Overlap Geometry Routing
Routes through **high-reconstruction-efficiency regions**, not arbitrary shortest paths.
Routing weights: overlap stability, repair efficiency, entropy burden, continuity compatibility, constraint resonance.

### Repair-First Continuity
**Repair CREATES continuity** (not just supports it). Continuous, low-amplitude, distributed, overlap-localized.

### Minimal Stable Realization (MSR)
> min(T) such that Recoverable Coherence(T) ≥ λ

## Phase 4 (Updated) — Instrumentation Abstraction + Overlap-Aware Execution

### Core Shift
- **OLD:** Tool routing infrastructure → **NEW:** Overlap-mediated execution continuity infrastructure

### Capability Fields
Tools are NOT isolated callable endpoints. Capabilities are **distributed execution potentials within topology space**.
Each field exposes: execution affordances, entropy profile, reconstruction risk, synchronization burden, repair compatibility.

### Reconstruction-Safe Execution
> Unrecoverable execution is invalid execution. Every execution must support: replayability, rollback, repair reconstruction.

### Entropy-Aware Scheduling
Optimizes: Recoverable Coherence / (Synchronization Cost + Execution Entropy).

## Phase 5 (Updated) — Long-Horizon Continuity + Reconstructable Trajectory Fields

### Core Shift
- **OLD:** Persistent state preservation → **NEW:** Recoverable trajectory reconstruction under overlap consistency

### New Continuity Law
> Identity exists only to the degree that trajectory reconstruction remains viable.

### Trajectory Reconstruction Fields
Continuity is NOT stored state. It's the ability to reconstruct coherent directional trajectories from sparse overlap evidence.

### Continuity Collars
Long-horizon continuity emerges at **overlap boundaries**, not isolated memory stores.

### Drift-Tolerant Identity
Identity tolerates local drift, partial contradiction — as long as reconstructable directional coherence remains.

### Repair-Generated Persistence
Persistence emerges from continual distributed repair. NOT passive archival storage.

### Minimal Continuity Realization (MCR)
> min(C) such that Reconstructable Continuity(C) ≥ λ

## File Conventions

```
srrs_opc/
├── __init__.py
├── base_patch.py          # Abstract base for all patches
├── planner_patch.py       # Phase 1
├── execution_patch.py     # Phase 1
├── memory_patch.py        # Phase 1
├── repair_patch.py        # Phase 1
├── collar_layer.py        # Phase 1
├── agent_bridge.py        # Phase 1
├── recovery_anchors.py    # Phase 2
├── drift_detector.py      # Phase 2
├── consistency_validator.py # Phase 2
├── reconstruction_synthesizer.py # Phase 2
├── contradiction_resolver.py # Phase 2
├── constraint_propagator.py # Phase 2
├── dynamic_coupling.py    # Phase 3 (TODO)
├── topological_router.py  # Phase 3 (TODO)
├── distributed_consensus.py # Phase 3 (TODO)
├── docs/
│   ├── phase3_design.md   # Phase 3 design doc
│   └── phase4_design.md   # Phase 4 design doc
├── reports/
│   └── hr_phase3_test_report.md
└── tests/
    ├── test_phase1.py
    └── test_phase2_e2e.py
```

## Phase Transition Checklist

Before moving from Phase N to Phase N+1:
1. All Phase N tests pass
2. All Phase N success criteria met
3. Phase N+1 design doc written
4. Phase N+1 components implemented
5. Phase N+1 tests written and passing
6. Integration tests (N + N+1) passing
7. Documentation updated (CODEMAP, WORKFLOW_PROTOCOL)
8. Progress files synced

## Key Metrics to Track

| Metric | Phase | Target |
|--------|-------|--------|
| Local Recovery Time | 1+ | < 5s |
| Entropy Spread Radius | 1+ | < 2 hops |
| Reconstruction Accuracy | 2+ | > 0.8 |
| Anchor Compression Ratio | 2+ | > 5:1 |
| Coupling Efficiency | 3+ | Adaptive |
| Routing Adaptability | 3+ | < 3 reroutes |
| Consensus Convergence | 3+ | < 10 iterations |
| Continuity Stability | 5+ | > 0.9 |
| Memory Growth Rate | 5+ | Sublinear |
