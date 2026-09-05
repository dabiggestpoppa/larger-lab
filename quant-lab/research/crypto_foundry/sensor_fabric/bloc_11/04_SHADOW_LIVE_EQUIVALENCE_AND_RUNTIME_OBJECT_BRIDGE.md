# BLOC 11 — SHADOW-LIVE EQUIVALENCE & RUNTIME OBJECT BRIDGE

## 1. Objective

Guarantee that historical replay and shadow-live computation describe the same market state when given the same evidence, generation set, closed interval, and quality policy.

This is the bridge from research-grade replay into Market OS runtime compatibility.

---

## 2. Core equivalence principle

For any fully closed interval `I`:

```text
historical_replay(I, generation=G)
```

and

```text
shadow_live_capture(I, generation=G)
```

must converge to the same canonical T2/Market OS state within declared numerical tolerance.

Allowed differences:
- acquisition lineage may differ (live capture vs historical archive);
- ingestion timestamps differ;
- source revision paths differ if the plan intentionally compares modes.

Not allowed:
- different economic state because codepaths use different formulas;
- different quality semantics;
- different window closure rules;
- different universe membership under the same PIT definition.

---

## 3. Shadow-live mode

Shadow-live is read-only observation/computation.

It may:
- consume live recorder outputs;
- compile T1/T2 state;
- emit Market OS runtime objects;
- compare with replay once intervals close.

It may not:
- place orders;
- route execution;
- size risk;
- call strategy engines;
- mutate provider data;
- authorize research promotion.

---

## 4. Runtime object mapping

### `MechanicalSnapshot` → `FieldSnapshot`

Carries global mechanical condition, cross-venue breadth/dispersion, quality and generation metadata.

### `MechanicalSnapshot` → `PatchSnapshot`

Carries venue/local/asset-specific state where locality matters.

### Event transition data → `LifecycleSnapshot`

Carries state age, transition history, persistence and recovery context where already defined.

### Mechanical stress/constraint coordinates → `ConstraintSnapshot`

Carries observable constraints such as leverage compression, liquidity withdrawal, funding pressure and forced-deleveraging state without turning them into directional forecasts.

### Shock-aligned event context → `ShockSnapshot`

Carries the measured mechanical response surrounding a known research shock/event.

### Lineage graph → `ResearchEvidence`

Carries source refs, generation refs, quality status and reproducibility receipt.

### Missing/invalid regions → `NullBoundary`

Carries why a state cannot be asserted.

---

## 5. Runtime object contract

Every emitted object must include at least:

```text
object_id
schema_version
as_of
universe
inputs
state
confidence
quality_flags
evidence_refs
valid_region
invalid_region
status
generation_set
computed_at
```

`confidence` is evidence/measurement confidence only.

It is not trade confidence or probability of direction.

---

## 6. Scientific status preservation

The bridge cannot upgrade:

```text
DESCRIPTIVE → LOCAL
LOCAL → PROMOTED
PARKED → ACTIVE
NULL → AVAILABLE
DATA_BLOCKED → INFERRED
```

without an explicit upstream scientific decision artifact.

The runtime bridge is a transport/compiler layer.

---

## 7. Dual-resolution architecture

Global and local mechanics remain separate where evidence requires it.

The bridge must allow:

```text
GLOBAL FIELD STATE
+
LOCAL PATCH STATES
+
RELATIONAL / CROSS-VENUE COORDINATES
```

rather than force all mechanics into one global object.

This is compatible with the project's established stable-topology + adaptive/local-coordinate architecture.

---

## 8. Live/replay generation discipline

A shadow-live process pins its active generation set at startup or controlled reload.

If a new T2 generation is promoted while the process runs:
- current generation finishes its interval;
- new generation begins at an explicit boundary;
- boundary is recorded;
- no mixed-generation state is emitted.

Historical replay can later reproduce either segment exactly.

---

## 9. Interval closure

Parity is only asserted after a comparable interval is closed.

Example:

```text
5m flow state at 14:05
```

cannot be compared with a historical closed 14:00–14:05 bar while the live interval is still receiving late data.

Each sensor declares:
- event-time closure rule;
- allowed lateness;
- revision/grace period;
- finalization state.

States:

```text
OPEN
PROVISIONAL_CLOSED
FINALIZED
REVISED
```

Research-grade parity uses `FINALIZED` unless a study explicitly examines provisional state.

---

## 10. Parity evidence packet

For every parity test store:

```text
parity_id
interval
asset_scope
historical_generation
shadow_generation
historical_checksum
shadow_checksum
field_diffs
quality_diffs
coverage_diffs
lineage_diff_summary
verdict
```

Verdicts:

```text
EXACT_MATCH
WITHIN_TOLERANCE
EXPECTED_LINEAGE_ONLY_DIFFERENCE
SEMANTIC_MISMATCH
QUALITY_MISMATCH
GENERATION_MISMATCH
INSUFFICIENT_COMPARABILITY
```

Semantic/quality mismatch is blocking.

---

## 11. Runtime service boundary

Bloc 10 remains the canonical read interface.

Bloc 11 may add replay endpoints/services such as:

```text
compile_snapshot(as_of,...)
run_replay(plan)
compile_event_context(event_id,...)
export_market_os_object(...)
compare_shadow_live(...)
```

but all data access flows through approved local canonical stores/service contracts.

No provider adapter is imported into the runtime bridge.

---

## 12. Failure behavior

If one required state is blocked:
- object can remain PARTIAL if contract allows;
- blocked coordinate is explicit;
- quality cannot be upgraded;
- `NullBoundary` is emitted where useful.

If generation or PIT semantics are inconsistent:
- object emission fails closed.

---

## 13. Required tests

1. historical/live state parity on closed intervals;
2. generation switch occurs only at explicit boundary;
3. provisional live state is not treated as finalized;
4. bridge preserves LOCAL/DESCRIPTIVE/PARKED/NULL status;
5. blocked coordinate produces explicit null boundary;
6. global/local patch states can coexist;
7. runtime object contains full evidence refs;
8. no provider/network dependency exists in bridge package;
9. no execution/trading imports are allowed;
10. parity mismatch generates blocking evidence packet.