# BLOC 11 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze deterministic historical replay, event-context compilation and Market OS bridge architecture before final system-wide Bloc 12 validation planning.

---

## 1. Frozen decisions

### F1 — Replay is local and read-only

Historical replay consumes canonical local T1/T2 state through approved service/store interfaces.

No provider calls, backfill mutations, execution, order routing or trading credentials.

### F2 — `AS_KNOWN_THEN` is the default scientific mode

Future revisions, future listings, future conversion observations and future-informed baselines are excluded.

### F3 — Replay clock is not causal structure

Clock progression schedules measurement; it does not explain state transition.

### F4 — Generation sets are fully locked

Each run pins T0/T1/T2, identity, normalization, quality, dependency graph, observable, baseline, Market OS schema and code revisions.

No floating generation during a run.

### F5 — PIT universe is mandatory

No current-universe backprojection.

### F6 — Static + rolling both survive

```text
STATIC 1D / 3D / 7D / 14D / 30D / 60D
ROLLING 3D / 7D / 14D / 30D
ROLLING 60D only with adequate support
```

### F7 — Mechanical state remains multidimensional

Replay preserves liquidation, leverage, funding, flow, liquidity, positioning, basis, breadth, consensus and dispersion rather than collapsing them into one stress score.

### F8 — Physical + standardized amplitude coexist

Standardized state cannot replace economic magnitude.

### F9 — Event stages are supplied by research artifacts

Replay cannot invent PRE-SHOCK/ABSORPTION/REORGANIZATION/PROPAGATION/CONTAINMENT labels.

### F10 — Event contexts are descriptive measurement objects

No strategy, expected-return, direction or execution outputs.

### F11 — Distributional summaries are retained

p25/p50/p75/p90/n/coverage where supported; median-only compression is insufficient for rate-vs-reach work.

### F12 — Market OS bridge preserves global/local resolution

Global FieldSnapshot and local PatchSnapshot can coexist.

### F13 — Scientific status cannot be promoted by infrastructure

No automatic:

```text
DESCRIPTIVE → LOCAL
LOCAL → PROMOTED
PARKED → ACTIVE
NULL → AVAILABLE
DATA_BLOCKED → INFERRED
```

### F14 — Null boundaries are first-class outputs

Missing/invalid mechanical coordinates create explicit `NullBoundary` objects rather than zero-fill, stale carry-forward or proxy substitution.

### F15 — Historical/live parity is mandatory

Finalized shadow-live and historical replay must converge under identical interval/method/generation contracts.

### F16 — Parity tolerances are field-specific and versioned

No global permissive tolerance.

### F17 — Research packets expose sample exclusions

Dropped events, asymmetric missingness and quality exclusions are reported explicitly.

### F18 — MECH-21 and LF14 consume canonical state only

No provider-native field leakage into research agents.

### F19 — Replay ordering does not establish causality

Causal promotion remains downstream under the L0–L6 ladder.

### F20 — Bloc 11 does not restart research

It prepares the bridge. Bloc 12 owns final restart authorization.

---

## 2. Frozen core objects

```text
ReplayPlan
ReplayClock
ReplayFrame
ReplayRunManifest
GenerationLockSet
UniverseSnapshot
MechanicalSnapshot
ResearchEventAnchor
MechanicalEventContext
TransitionContext
ContextLineageManifest
ParityEvidencePacket
ResearchPacket
ResearchReproducibilityReceipt
NullBoundary
```

---

## 3. Frozen replay modes

```text
FIXED_INTERVAL
EVENT_DRIVEN
HYBRID_EVENT_ANCHORED
SINGLE_SNAPSHOT
```

Knowledge/revision modes:

```text
AS_KNOWN_THEN
LATEST_RECONSTRUCTED
EXACT_GENERATION
```

No silent mode substitution.

---

## 4. Frozen Market OS targets

```text
FieldSnapshot
PatchSnapshot
RelationalSnapshot
LifecycleSnapshot
ConstraintSnapshot
ShockSnapshot
ResearchEvidence
NullBoundary
```

`DirectionalSnapshot` is not required for Bloc 11 and must not become a trading-signal path.

---

## 5. Frozen mechanical families

Venue-local:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

Cross-venue:

```text
LiquidationBreadth
LeverageCompression
FundingConsensus
FlowConsensus
LiquidityWithdrawalBreadth
VenueDispersion
```

All outputs carry quality, coverage, independent source count, generation and lineage.

---

## 6. Frozen research handoff

### MECH-21

Replay may provide mechanical context around:
- gain/ceiling transitions;
- sterile saturation;
- absorptive capacity;
- realization/non-realization;
- forcing mixtures;
- low-gain episodes;
- 2022/recurrent modulation;
- calendar/seasonality analysis.

### LOWER-FIELD-14

Replay may provide matched mechanical contexts across:

```text
PRE-SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

with liquidation/OI/funding/flow/liquidity and cross-venue breadth/dispersion, plus full missingness/exclusion accounting.

No variable selection is optimized for sign separation by Bloc 11.

---

## 7. Frozen null reasons

At minimum:

```text
NO_VERIFIED_FREE_SOURCE
HISTORY_UNAVAILABLE
PROVIDER_GAP
IDENTITY_AMBIGUOUS
PIT_AMBIGUOUS
SEMANTIC_MISMATCH
INSUFFICIENT_REDUNDANCY
QUALITY_FAILURE
BASELINE_UNAVAILABLE
REVISION_CONFLICT
NOT_EXPECTED
```

Nulls are scientific boundary evidence.

---

## 8. Frozen event evidence tiers

```text
E0_BLOCKED
E1_SINGLE_SOURCE
E2_REDUNDANT
E3_CROSS_VENUE
E4_MULTI_MECHANIC
E5_MULTI_MECHANIC_REDUNDANT
```

These are evidence-availability tiers only, not signal strength.

---

## 9. Frozen planning commits

```text
SENSOR-PLAN-B11A
  historical replay + Market OS bridge architecture

SENSOR-PLAN-B11B
  clock / as-of / PIT universe / generation locks

SENSOR-PLAN-B11C
  event context + mechanical snapshot compilation

SENSOR-PLAN-B11D
  shadow-live equivalence + runtime object bridge

SENSOR-PLAN-B11E
  MECH21 / LF14 research integration + null boundaries

SENSOR-PLAN-B11F
  acceptance tests + staged implementation commits

SENSOR-PLAN-B11G
  freeze manifest + Bloc 12 handoff
```

---

## 10. Frozen future implementation sequence

```text
SENSOR-B11-I01  replay models/enums
SENSOR-B11-I02  generation locks
SENSOR-B11-I03  replay clock
SENSOR-B11-I04  AS_KNOWN_THEN
SENSOR-B11-I05  latest/exact revision modes
SENSOR-B11-I06  PIT universe
SENSOR-B11-I07  baseline eligibility
SENSOR-B11-I08  Bloc10 local client boundary
SENSOR-B11-I09  frame compiler
SENSOR-B11-I10  static views
SENSOR-B11-I11  rolling views
SENSOR-B11-I12  transitions
SENSOR-B11-I13  event anchor interface
SENSOR-B11-I14  event contexts
SENSOR-B11-I15  distribution summaries
SENSOR-B11-I16  neutral comparison helper
SENSOR-B11-I17  checkpoint/resume
SENSOR-B11-I18  deterministic exports
SENSOR-B11-I19  Market OS schemas
SENSOR-B11-I20  Field/Patch bridge
SENSOR-B11-I21  Lifecycle/Constraint bridge
SENSOR-B11-I22  Shock bridge
SENSOR-B11-I23  Evidence/NullBoundary bridge
SENSOR-B11-I24  scientific-status preservation
SENSOR-B11-I25  shadow-live compiler
SENSOR-B11-I26  parity harness
SENSOR-B11-I27  MECH21 packet
SENSOR-B11-I28  LF14 packet
SENSOR-B11-I29  adversarial integrity suite
SENSOR-B11-I30  bounded-memory performance
SENSOR-B11-I31  acceptance evidence packet
SENSOR-B11-I32  Bloc12 handoff
```

No squashing during staged review.

---

## 11. Blocking acceptance gates

Bloc 11 implementation cannot pass with:

```text
future leakage
unlocked/mixed generations
PIT universe leakage
broken T2→T1→T0 lineage
silent null coercion
scientific status promotion by bridge
historical/live semantic mismatch
historical/live quality mismatch
provider/network dependency in replay layer
silent research sample filtering
```

Ragged provider history is acceptable when represented honestly.

---

## 12. Frozen evidence outputs

```text
REPLAY_ACCEPTANCE_REPORT.md
PIT_LEAKAGE_TEST_REPORT.md
GENERATION_DETERMINISM_REPORT.md
LINEAGE_CLOSURE_REPORT.md
NULL_BOUNDARY_REPORT.md
STATIC_ROLLING_COMPLETENESS.csv
MARKET_OS_SCHEMA_VALIDATION.json
SHADOW_LIVE_PARITY_REPORT.md
MECH21_PACKET_FIXTURE/
LF14_PACKET_FIXTURE/
REPLAY_GOLDEN_CHECKSUMS.json
BLOC_11_IMPLEMENTATION_MANIFEST.json
```

---

## 13. Bloc 12 handoff

Bloc 12 is the final **full-system validation and research-restart packet**.

It must audit the complete chain:

```text
B1 contracts
→ B2 capability proof
→ B3 adapters
→ B4 T0 evidence
→ B5 PIT/T1 normalization
→ B6 quality/redundancy
→ B7 historical backfill
→ B8 live recorder
→ B9 mechanical observables
→ B10 canonical service
→ B11 replay/Market OS bridge
```

Bloc 12 must define:
1. final free-only/$0 audit;
2. provider capability and access revalidation;
3. end-to-end T0→T2 lineage tests;
4. PIT/adversarial leakage audit;
5. historical coverage/redundancy thresholds;
6. live recorder resilience acceptance;
7. cross-provider semantic consistency audit;
8. shadow-live/replay parity;
9. Market OS schema/bridge validation;
10. performance/local-machine operating envelope;
11. backup/recovery exercise;
12. security/no-trading-credential audit;
13. reproducibility packet;
14. unresolved DATA_BLOCKED registry;
15. go/no-go statuses by research scope;
16. explicit MECH-21 and LF14 restart authorization or continued block;
17. final master implementation handoff requirements.

Bloc 12 must not hide partial coverage merely to reach a green final status.

---

## 14. Completion checklist

- [x] deterministic replay architecture defined
- [x] clock modes defined
- [x] `AS_KNOWN_THEN` defined
- [x] generation locks defined
- [x] PIT universe defined
- [x] baseline eligibility defined
- [x] static + rolling protocol preserved
- [x] mechanical snapshot defined
- [x] event context defined
- [x] transition packaging defined
- [x] distributional summaries preserved
- [x] neutral comparison boundary defined
- [x] Market OS bridge defined
- [x] global/local dual resolution preserved
- [x] scientific-status preservation defined
- [x] NullBoundary defined
- [x] shadow-live equivalence defined
- [x] parity evidence defined
- [x] MECH21 packet defined
- [x] LF14 packet defined
- [x] asymmetric missingness audit defined
- [x] reproducibility receipts defined
- [x] staged implementation commits defined
- [x] acceptance gates defined
- [x] Bloc12 handoff defined

---

## 15. Final planning verdict

`PASS_BLOC_11_PLAN_FROZEN`

Rationale:

The fabric now has an implementation-grade deterministic time-travel layer: strict as-of knowledge semantics, full generation locking, PIT universe reconstruction, static+rolling mechanical snapshots, event-context compilation, cross-venue state preservation, first-class null boundaries, Market OS runtime-object transport, shadow-live/historical parity, exact research packet contracts for MECH-21/LF14, reproducibility receipts and 32 staged implementation checkpoints.

`human_review_required = TRUE`
`research_restart_authorized = FALSE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 12`
