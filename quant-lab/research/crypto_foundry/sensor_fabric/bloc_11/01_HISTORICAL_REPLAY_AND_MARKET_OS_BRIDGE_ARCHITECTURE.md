# BLOC 11 — HISTORICAL REPLAY + MARKET OS BRIDGE ARCHITECTURE

**Status:** planning only — implementation not started  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent:** Bloc 10 read-only canonical sensor service  
**Purpose:** define deterministic historical reconstruction of mechanical market state and bridge it into Market OS runtime objects without provider calls, future leakage, execution logic, or hidden quality upgrades.

---

## 1. Mission

Build a deterministic local replay layer capable of answering:

```text
What mechanical market state was knowable at time t?
```

using only previously materialized T0/T1/T2 evidence and the Bloc 10 read-only canonical sensor service.

The replay engine must compile the exact same families used by live research while honoring historical availability, PIT universe, revision mode, quality, coverage, lineage and generation locks.

---

## 2. Architecture

```text
T0 exact evidence
   ↓
T1 PIT canonical observations
   ↓
Bloc 6 quality / eligibility
   ↓
T2 mechanical states
   ↓
Bloc 10 canonical sensor service
   ↓
REPLAY CLOCK + REPLAY PLAN
   ↓
MechanicalReplayFrame
   ↓
EventContext / TransitionContext
   ↓
Market OS runtime objects
   ↓
MECH / LOWER-FIELD research
```

Hard boundary:

> The replay engine cannot call a provider, initiate a backfill, modify canonical data, rewrite history, or fabricate unavailable state.

---

## 3. Core replay objects

### 3.1 `ReplayPlan`

Minimum fields:

```text
replay_id
plan_version
start_at
end_at
clock_mode
step
universe_policy
revision_mode
as_of_mode
t1_generation
t2_generation
quality_policy_version
observable_registry_version
baseline_registry_version
required_sensor_families
required_quality_mode
missingness_policy
output_profile
created_at
```

### 3.2 `ReplayClock`

Responsible only for deterministic temporal progression.

Supported v1 modes:

```text
FIXED_INTERVAL
EVENT_DRIVEN
HYBRID_EVENT_ANCHORED
SINGLE_SNAPSHOT
```

### 3.3 `ReplayFrame`

One immutable reconstruction point:

```text
replay_id
frame_id
frame_at
as_of
universe_snapshot_id
source_generation_set
mechanical_states
quality_state
coverage_state
missingness_state
lineage_refs
status
warnings
```

### 3.4 `ReplayRunManifest`

Contains:
- plan hash;
- code revision;
- generation locks;
- baseline/quality versions;
- exact frame count;
- skipped/blocked frames;
- coverage summary;
- checksum of exported result set.

---

## 4. Replay clock doctrine

Time is a measured coordinate, not a causal explanation.

Replay therefore separates:

```text
clock progression
from
state transition
```

A one-hour replay step does not imply the market evolves because one hour passed.

The engine only reconstructs which state was observable/knowable at each requested time.

---

## 5. Historical truth modes

### `AS_KNOWN_THEN`

Default scientific mode.

Only evidence/identity/revisions/quality knowledge valid by the requested historical `as_of` may be used.

### `LATEST_RECONSTRUCTED`

Uses the latest approved historical reconstruction/generation while preserving source revision lineage.

Useful for post-hoc measurement studies, not for claims about what could have been known at the time.

### `EXACT_GENERATION`

Pins exact T1/T2 and policy generations for reproducibility.

No replay may silently switch between these modes.

---

## 6. PIT universe

Every frame must resolve its universe point-in-time.

The engine cannot:
- project current listings backward;
- include future instruments;
- use post-delist observations;
- silently bridge renamed/reissued contracts;
- substitute an economically different contract.

Frame universe lineage must point to the identity/lifecycle registry generation used.

---

## 7. Mechanical state families

Replay must support at least:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState

LiquidationBreadth
LeverageCompression
FundingConsensus
FlowConsensus
LiquidityWithdrawalBreadth
VenueDispersion
```

Each state preserves:
- physical amplitude;
- standardized amplitude;
- static horizon values;
- rolling values;
- transition metadata;
- quality/coverage;
- source independence;
- lineage.

---

## 8. Static + rolling temporal protocol

Research-facing replay must preserve the project-wide protocol:

```text
STATIC: 1D / 3D / 7D / 14D / 30D / 60D
ROLLING: 3D / 7D / 14D / 30D
ROLLING 60D only where sample support is adequate
```

Intraday states may coexist but cannot replace this protocol.

---

## 9. Market OS bridge

The replay engine should emit versioned runtime objects compatible with the existing Market OS architecture.

Minimum bridge targets:

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

Optional future objects may include `DirectionalSnapshot`, but Bloc 11 must not infer directional strategy or trading signals.

### Mechanical bridge fields

Each object should carry, where relevant:

```text
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
```

Status remains constrained to the established research vocabulary:

```text
PROMOTED
LOCAL
DESCRIPTIVE
PARKED
NULL
DATA_BLOCKED
```

Bloc 11 cannot promote scientific status automatically. It transports previously earned status and evidence.

---

## 10. Null / blocked behavior

A replay frame can be valid while one sensor is unavailable.

Explicit states:

```text
AVAILABLE
DEGRADED
PARTIAL
NULL
DATA_BLOCKED
NOT_EXPECTED
```

No zero-fill.
No carry-forward masquerading as observation.
No provider substitution without explicit cross-venue semantics.

A downstream Market OS object must preserve blocked coordinates rather than coercing them into a complete vector.

---

## 11. Determinism

Same:

```text
ReplayPlan
+ T1/T2 generations
+ quality policy
+ baseline registry
+ code revision
```

must produce byte-stable canonical outputs modulo explicitly declared serialization metadata.

Determinism failures are blocking.

---

## 12. Performance model

Replay must be local-first and streamable.

Preferred design:
- partition-pruned Parquet reads;
- DuckDB/local analytical backend where appropriate;
- bounded-memory frame compiler;
- no requirement to load whole multi-year history into RAM;
- resumable long replay jobs;
- deterministic checkpointing.

Performance optimizations cannot change scientific semantics.

---

## 13. Out of scope

Bloc 11 does not define:
- strategy rules;
- PnL;
- entries/exits;
- execution;
- sizing;
- leverage;
- live order routing;
- alpha ranking;
- autonomous trading decisions.

It also does not re-open provider acquisition, T1 normalization, or T2 methodology except to surface incompatibility evidence.

---

## 14. Completion target

Bloc 11 planning is complete only when the execution agent can implement deterministic historical state reconstruction, event-context compilation, Market OS object emission, shadow-live equivalence tests, strict lineage, and direct research handoff without making architectural choices not already specified.