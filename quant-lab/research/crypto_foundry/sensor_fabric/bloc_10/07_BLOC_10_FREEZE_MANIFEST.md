# BLOC 10 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze the read-only canonical consumer boundary before replay/Market OS integration.

---

## 1. Frozen decisions

### F1 — One canonical consumer boundary

Research agents, replay and future Market OS consumers read canonical mechanics through Bloc 10 service contracts rather than provider APIs, raw filesystem paths or ad hoc SQL.

### F2 — Service is read-only

No provider calls, data acquisition, backfill, live collection or mutation occurs inside the query service.

### F3 — Offline-first is mandatory

Canonical queries must work with outbound network disabled.

### F4 — T1 and T2 remain versioned truth surfaces

The service serves accepted generations; it does not redefine normalization or mechanical observables.

### F5 — `as_of` semantics are first-class

Supported modes include:

```text
STRICT_REPRODUCIBLE
LATEST_ACCEPTED
AS_KNOWN_THEN
LIVE_CURRENT
DEBUG_LINEAGE
```

### F6 — Future knowledge is blocked

Historical `AS_KNOWN_THEN` cannot use later revisions, symbol knowledge, conversion data or quality-policy state that was not available by the requested historical boundary unless the explicit query mode requests later knowledge.

### F7 — Generation ambiguity fails closed

Strict mode never silently substitutes latest for a missing/pinned generation.

### F8 — Quality is part of the answer

Every canonical state response carries quality, coverage, redundancy, independence, missingness and warnings.

### F9 — Empty is typed

Valid zero, gap, not expected, unsupported, history unavailable, blocked, revision conflict and quality failure remain distinct.

### F10 — Static + rolling retrieval is canonical

Research protocol supports:

```text
STATIC 1/3/7/14/30/60D
ROLLING 3/7/14/30D
ROLLING 60D where support permits
```

Intraday horizons may coexist without replacing this protocol.

### F11 — Provider-native fields are hidden by default

Provider details are available through explicit lineage/debug queries, not leaked into ordinary research APIs.

### F12 — Lineage is traversable

```text
T2 → T1 → T0B → AcquisitionRecord → T0A SHA256
```

Broken canonical lineage is blocking.

### F13 — Historical/live finalized parity is required

Equivalent closed intervals under identical frozen methodology must converge within declared tolerance.

### F14 — Generation publication is atomic

In-flight requests remain pinned to their resolved generation even if a newer accepted generation is published during execution.

### F15 — Cache is rebuildable

Caches are keyed by generation/policy/version and never become canonical truth.

### F16 — Readiness is scope-specific

No global `data_ready` flag.

### F17 — Cross-venue operation eligibility is enforced

The service cannot perform breadth/consensus/notional aggregation if Bloc 6/T2 policy does not permit that operation.

### F18 — Event context is first-class

The service can return phase-aligned mechanical context for research episodes while preserving phase-specific quality and PIT boundaries.

### F19 — Research agent firewall is hard

Canonical research jobs cannot bypass the service by importing provider adapters or using raw lake paths as a substitute for accepted canonical data.

### F20 — No strategy semantics

Bloc 10 serves observations/mechanical states. It does not emit entries, exits, trade directions, sizing, leverage, deployment or PnL optimization.

---

## 2. Frozen service objects

```text
SensorQuery
ObservationQuery
MechanicalStateQuery
WindowQuery
EventContextQuery
EventBatchQuery
CoverageQuery
ReadinessQuery
LineageQuery
SchemaQuery
GenerationQuery
CanonicalSensorResponse
CoverageSummary
ReproducibilityReceipt
```

---

## 3. Frozen backend roles

```text
Parquet = canonical T1/T2 local data artifacts
DuckDB = rebuildable read/query engine
PostgreSQL = operational metadata/catalog only
local filesystem = local-first storage substrate
```

No provider/network clients in service tree.

---

## 4. Frozen failure classes

Minimum:

```text
InvalidQuery
UnknownSensor
UnknownAsset
UnknownContract
UnknownGeneration
GenerationConflict
RevisionConflict
AsOfViolation
QualityRequirementNotMet
CoverageRequirementNotMet
RedundancyRequirementNotMet
OperationNotEligible
LineageUnavailable
SchemaVersionMismatch
BackendUnavailable
LocalCatalogInconsistent
QueryResourceLimit
DataBlocked
```

---

## 5. Frozen lineage levels

```text
L0 summary
L1 canonical inputs
L2 T0 evidence lineage
L3 operator/provider debug
```

Default research responses use L0 unless deeper lineage is requested.

---

## 6. Frozen event-context phases

For LF14-style mechanism work the service supports explicit phase-aligned retrieval:

```text
PRE_SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

Phase definitions are supplied/versioned by research manifests; the service does not invent them.

---

## 7. Frozen planning history

```text
SENSOR-PLAN-B10A
  read-only canonical sensor service architecture

SENSOR-PLAN-B10B
  as-of / generation / revision semantics

SENSOR-PLAN-B10C
  quality / coverage / readiness / failure contracts

SENSOR-PLAN-B10D
  query surfaces / lineage / agent interface

SENSOR-PLAN-B10E
  local backend / caching / runtime policy

SENSOR-PLAN-B10F
  acceptance tests + staged implementation commits

SENSOR-PLAN-B10G
  freeze manifest + Bloc 11 handoff
```

---

## 8. Frozen future implementation sequence

```text
SENSOR-B10-I01  service enums/models/errors
SENSOR-B10-I02  request fingerprint + response envelope
SENSOR-B10-I03  generation catalog
SENSOR-B10-I04  revision/as-of resolver
SENSOR-B10-I05  Parquet read backend
SENSOR-B10-I06  DuckDB read backend
SENSOR-B10-I07  Postgres metadata backend
SENSOR-B10-I08  canonical observation queries
SENSOR-B10-I09  venue-local T2 state queries
SENSOR-B10-I10  cross-venue T2 state queries
SENSOR-B10-I11  static/rolling window queries
SENSOR-B10-I12  quality/coverage propagation
SENSOR-B10-I13  readiness/eligibility queries
SENSOR-B10-I14  lineage resolver L0-L3
SENSOR-B10-I15  event-context query
SENSOR-B10-I16  deterministic batch/event query
SENSOR-B10-I17  schema/generation introspection
SENSOR-B10-I18  explain-response + receipts
SENSOR-B10-I19  deterministic pagination/cursors
SENSOR-B10-I20  local cache layer
SENSOR-B10-I21  atomic generation publication/read pinning
SENSOR-B10-I22  CLI/local API surface
SENSOR-B10-I23  offline/network firewall tests
SENSOR-B10-I24  historical-live parity suite
SENSOR-B10-I25  quality/revision adversarial suite
SENSOR-B10-I26  performance/resource limits
SENSOR-B10-I27  research-agent fixture integration
SENSOR-B10-I28  golden reproducibility packet
SENSOR-B10-I29  final acceptance evidence
SENSOR-B10-I30  Bloc 11 handoff
```

No squashing during staged review.

---

## 9. Bloc 10 acceptance gates

Implementation must later prove:

- complete offline operation;
- strict PIT/as-of correctness;
- deterministic generation pinning;
- revision ambiguity failure;
- typed missingness;
- quality/coverage propagation;
- independence/redundancy visibility;
- complete T2→T0 lineage;
- historical/live finalized parity;
- read-only authority;
- bounded resource use;
- reproducibility receipt equivalence;
- provider-independent research-agent integration.

PIT, lineage, read-only, offline or generation-determinism failure is blocking.

---

## 10. Bloc 11 handoff

Bloc 11 must design **Historical Replay + Market OS Bridge** on top of Bloc 10 rather than reading T1/T2 directly.

Required topics:

1. deterministic `mechanical_replay(t)`;
2. replay session/manifest objects;
3. frozen generation/policy resolution per replay;
4. `AS_KNOWN_THEN` historical state reconstruction;
5. point-in-time universe membership;
6. event-aligned research context packets;
7. replay ordering and clock semantics;
8. historical/live shadow equivalence;
9. Market OS runtime object mapping;
10. quality/degraded-mode propagation into OS snapshots;
11. no provider-specific leakage;
12. research exports for MECH-21/LF14;
13. replay caching without future leakage;
14. deterministic reruns and evidence receipts;
15. read-only bridge into downstream OS layers.

Bloc 11 must not introduce strategies, execution, sizing or live trading.

---

## 11. Completion checklist

- [x] service boundary defined
- [x] read-only authority frozen
- [x] offline-first requirement frozen
- [x] query/response contracts defined
- [x] as-of policies defined
- [x] generation resolution defined
- [x] revision semantics defined
- [x] static/rolling queries defined
- [x] quality/coverage contract defined
- [x] missingness contract defined
- [x] readiness contract defined
- [x] operation eligibility defined
- [x] lineage levels defined
- [x] event-context queries defined
- [x] batch agent interface defined
- [x] schema introspection defined
- [x] deterministic pagination defined
- [x] local backend roles defined
- [x] caching policy defined
- [x] atomic publication/read pinning defined
- [x] resource limits defined
- [x] offline/network firewall test defined
- [x] historical/live parity gate defined
- [x] 30 staged implementation commits defined
- [x] Bloc 11 handoff defined

---

## 12. Final planning verdict

`PASS_BLOC_10_PLAN_FROZEN`

Rationale:

The fabric now has a complete canonical consumer boundary: local-first and read-only, PIT/as-of aware, generation/revision pinned, quality/coverage explicit, provider-independent, fully lineage-traceable, deterministic under strict mode, capable of phase-aligned event research, protected by an agent firewall, and ready to become the sole data interface for historical replay and Market OS integration.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 11`
