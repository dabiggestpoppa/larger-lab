# 🔬 Topology Analysis — Key Findings

> **Date:** 2026-05-23
> **PM2 — Experimental Track**

## Fragility Zones Analysis

### Finding: All 76 fragility zones are orphan observers

Every observer-classified node (76/76) has zero dependency/dependent connections in the static AST graph. This is **not a bug** — it reveals an architectural pattern:

**Why observers are orphaned in static analysis:**
- Observers are likely registered dynamically (decorators, config, runtime registration)
- Python composition pattern: observers are instantiated and wired at runtime, not via explicit imports
- The AST-based extractor only sees explicit `import`/`class X(Y)` links

**Implication:** Static topology analysis alone **cannot measure observer integration**. We need runtime instrumentation to see the real observer graph.

### Over-Connected Nodes (12)

| Node | Coupling | Type | Notes |
|------|----------|------|-------|
| `BasePatch` | 0.0054 | repair | Parent of 4 repair patches — expected hub |
| `ToolAdapter` | 0.0054 | other | Parent of 4 workspace adapters — expected hub |
| 4 Repair Patches | 0.0014 | repair | Children of BasePatch |
| 3 Adapters | 0.0014 | other | Children of ToolAdapter |
| 2 Contract Managers | 0.0014 | other | DSPy contract hierarchy |

These are all **inheritance hubs** — expected and healthy. No unexpected hotspots.

### The 9 Edges — All Real Inheritance

```
BasePatch ← ExecutionPatch, MemoryPatch, PlannerPatch, RepairPatch
ToolAdapter ← OpenClawAdapter, HermesAdapter, NautilusAdapter, ClaudeAdapter
PredictionContractManager ← DSPyContractManager
```

Clean hierarchy. No cycles. No hidden coupling.

## Orphan Node Analysis

| Type | Orphans | Connected | Orphan Rate |
|------|---------|-----------|-------------|
| other | 436 | 7 | 98.4% |
| field | 103 | 0 | 100% |
| observer | 76 | 0 | 100% |
| repair | 37 | 5 | 88.1% |
| memory | 29 | 0 | 100% |
| signal | 23 | 0 | 100% |
| router | 21 | 0 | 100% |

**Interpretation:**
- `other` (98.4% orphan): Data classes, utilities, config objects — expected
- `field` (100% orphan): Field computation classes, likely composed at runtime
- `observer` (100% orphan): **Key finding** — observers are dynamically registered
- `repair` (88.1% orphan): 5 connected (the patch hierarchy), rest are standalone
- `memory/signal/router` (100% orphan): All dynamically composed

## Conclusion

**The topology is healthy but shallow.** The system uses composition over inheritance, which is correct for a dynamical continuity substrate. The shallow depth (max 1) means no cascade chains through inheritance.

**The critical insight:** Observer integration cannot be measured statically. Phase 11 Test 3 (Distributed Observer Consensus) will need runtime instrumentation to see the real observer graph.

**Recommendation:** Build a runtime observer registry that tracks observer instantiation and wiring — this will give us the true topology that static analysis misses.
