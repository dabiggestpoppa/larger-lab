# BLOC 9 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze T2 mechanical-observable semantics before any execution agent turns T1 data into interpreted market-mechanics states.

---

## 1. Frozen decisions

### F1 — Bloc 9 is state/constraint interpretation, not strategy

No trade signals, future-return targets, PnL optimization, sizing, leverage, execution or portfolio logic.

### F2 — Two T2 layers

```text
T2A venue-local mechanical states
T2B cross-venue mechanical states
```

Venue-local state must exist before cross-venue synthesis.

### F3 — Seven primary state families

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

### F4 — No universal master mechanical score in v1

Parallel coordinates are preserved until research earns compression.

### F5 — Physical amplitude survives standardization

Percentile/z-score/robust-sigma never replaces physical notional/depth/spread/rate where physical measurement is valid.

### F6 — Static + rolling temporal protocol

Research-facing temporal analysis supports:

```text
STATIC: 1D / 3D / 7D / 14D / 30D / 60D
ROLLING: 3D / 7D / 14D / 30D
+ 60D when support allows
```

Intraday horizons may coexist where source frequency allows.

### F7 — Continuous coordinates are primary

State labels are descriptive convenience layers, not primitive truth.

### F8 — Bloc 6 eligibility controls aggregation

Cross-venue calculations cannot bypass independence, comparability, quality or allowed-operation gates.

### F9 — Fake redundancy is forbidden

Dependent/aggregated sources do not inflate strict cross-venue breadth/quorum.

### F10 — Missing contributors never become zero

Coverage and breadth are reported separately.

### F11 — Venue disagreement is preserved

Valid heterogeneity becomes dispersion/locality/concentration information, not automatic error cleanup.

### F12 — Distribution-first cross-venue reporting

Prefer breadth, median, p25/p75, p90 where supported, dispersion and concentration before opaque means/sums.

### F13 — Notional summation requires explicit comparability permission

No casual addition of incompatible exchange measurements.

### F14 — No universal clock

State age/persistence/recovery are sensor/local-context dependent unless evidence supports wider law.

### F15 — Baselines are versioned and PIT-safe

No later data may enter earlier baselines.

### F16 — Materiality remains multidimensional

Physical amplitude, standardized amplitude, breadth, persistence, coverage and concentration remain separate coordinates in v1.

### F17 — T2 is derived/rebuildable

T0 exact evidence > T1 canonical observations > T2 observables.

### F18 — T2 generations are immutable/auditable

Methodology/upstream revisions create new generations where required.

### F19 — Historical and live semantics must match

Batch historical T2 and incremental live T2 converge for the same closed interval under the same methodology/generation.

### F20 — Full T2 lineage is mandatory

Every observable traces to T1 generation and ultimately T0 evidence.

### F21 — Research consumes observable IDs, not provider-native fields

No direct Kraken/Gate/Binance field coupling in MECH/LF research.

### F22 — Bloc 10 is read-only serving

Bloc 10 may expose/query T2 but cannot redefine, mutate or bypass its semantics.

---

## 2. Frozen cross-venue descriptive objects

Initial high-value objects include:

```text
MechanicalBreadth
LiquidationBreadth
LeverageCompression
FundingConsensus
FlowConsensus
LiquidityWithdrawalBreadth
VenueDispersion
```

These remain separate; no one-number stress score.

---

## 3. Frozen observable classes

```text
DIRECT_TRANSFORM
NORMALIZED_TRANSFORM
WINDOW_STATISTIC
CROSS_VENUE_BREADTH
CROSS_VENUE_CONSENSUS
CROSS_VENUE_DISPERSION
STATE_CLASSIFICATION
RESEARCH_EXPERIMENTAL
```

---

## 4. Frozen observable lifecycle

```text
DRAFT
RESEARCH_EXPERIMENTAL
VALIDATED_LOCAL
VALIDATED_CROSS_VENUE
PROMOTED_RUNTIME
DEPRECATED
BLOCKED
```

Runtime promotion requires evidence and human review.

---

## 5. Frozen blocked/null states

```text
NO_DATA_EXPECTED
DATA_GAP
INSUFFICIENT_COVERAGE
SEMANTIC_BLOCKED
IDENTITY_BLOCKED
PIT_BLOCKED
QUALITY_BLOCKED
METHODOLOGY_BLOCKED
DATA_BLOCKED
```

No implicit zero-fill.

---

## 6. Frozen generation identity

T2 generation includes at least:

```text
observable registry version
T1 generation
quality policy version
source dependency graph version
baseline registry version
code revision
```

---

## 7. Frozen lineage requirements

Every T2 value stores:

```text
observable/version
t2 generation
input T1 refs/generation
baseline/version
quality policy
eligibility decision
methodology hash
code revision
```

Cross-venue states additionally retain:

```text
contributors
excluded sources
independence groups
coverage denominator policy
aggregation/summary method
```

---

## 8. Frozen planning history

```text
SENSOR-PLAN-B9A
  mechanical observable fabric architecture

SENSOR-PLAN-B9B
  venue-local state contracts

SENSOR-PLAN-B9C
  cross-venue breadth / consensus / dispersion

SENSOR-PLAN-B9D
  temporal baselines / transitions / materiality

SENSOR-PLAN-B9E
  T2 generations / lineage / Bloc 10 boundary

SENSOR-PLAN-B9F
  acceptance tests + staged implementation commits

SENSOR-PLAN-B9G
  freeze manifest + Bloc 10 handoff
```

---

## 9. Frozen future implementation sequence

Thirty reviewable implementation checkpoints are defined in `06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md`, covering:

```text
registry/baselines/common context
→ seven venue-local families
→ temporal/state transitions
→ Bloc 6 eligibility
→ breadth/consensus/dispersion
→ cross-venue schemas
→ T2 generations/materialization
→ historical batch compiler
→ live incremental compiler
→ revision recomputation
→ research exporter
→ golden/adversarial/parity/performance suites
→ acceptance + Bloc 10 handoff
```

No squashing during staged review.

---

## 10. Mandatory pilot

Pilot must cover where data exists:

```text
BTC / ETH / SOL
2022 stress
2024 ordinary
2026 recent
```

with venue-local:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
```

and cross-venue:

```text
LiquidationBreadth
LeverageCompression
FlowConsensus
LiquidityWithdrawalBreadth
FundingConsensus
VenueDispersion
```

Both static and rolling temporal views are required.

---

## 11. Bloc 9 acceptance gates

Blocking failures:

- future leakage;
- missing T1/T0 lineage;
- provider identity erased;
- fake source independence;
- unsupported cross-venue aggregation;
- missing→zero conversion;
- physical amplitude discarded;
- historical/live semantic mismatch;
- silent methodology changes;
- strategy/trading contamination.

---

## 12. Bloc 10 handoff

Bloc 10 must design the **Read-Only Canonical Sensor Service** over T1/T2.

Required topics:

1. read-only API/query contracts;
2. latest-state retrieval;
3. historical range queries;
4. strict `as_of` queries;
5. generation/version selection;
6. quality filters;
7. availability/coverage endpoints;
8. lineage summaries;
9. observable catalog discovery;
10. venue-local vs cross-venue queries;
11. static/rolling window retrieval;
12. local-first DuckDB/Parquet backend;
13. optional in-process service boundary;
14. caching without changing truth;
15. deterministic pagination/result ordering;
16. research-agent ergonomics;
17. no provider/network calls from service layer;
18. no mutation endpoints.

The service must make the sensor fabric easy to consume without allowing consumers to reinterpret it.

---

## 13. Completion checklist

- [x] T2 architecture defined
- [x] venue-local states defined
- [x] seven primary families frozen
- [x] cross-venue eligibility boundary frozen
- [x] breadth defined
- [x] consensus defined
- [x] dispersion/locality defined
- [x] dependency-aware source counting defined
- [x] physical vs standardized doctrine defined
- [x] static + rolling protocol defined
- [x] transition/persistence semantics defined
- [x] materiality envelope defined
- [x] event-relative slicing defined
- [x] baseline registry defined
- [x] T2 generations defined
- [x] late-arrival/revision behavior defined
- [x] historical/live parity defined
- [x] research firewall defined
- [x] no-target-leakage rule defined
- [x] staged implementation commits defined
- [x] acceptance/adversarial tests defined
- [x] Bloc 10 handoff defined

---

## 14. Final planning verdict

`PASS_BLOC_09_PLAN_FROZEN`

Rationale:

The sensor fabric now has an implementation-grade interpretation layer that converts canonical T1 observations into venue-local and cross-venue mechanical states while preserving physical scale, PIT truth, source independence, venue heterogeneity, quality/coverage, methodology versioning, immutable generations and complete lineage. It explicitly avoids a premature universal stress score and remains upstream of direction, alpha, strategy and execution.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 10`
