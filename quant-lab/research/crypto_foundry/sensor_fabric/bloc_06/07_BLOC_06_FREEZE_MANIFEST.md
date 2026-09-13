# BLOC 6 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze the quality, redundancy, comparability and failover control plane before historical backfill is planned.

---

## 1. Frozen architectural decisions

### F1 — Provider health and sensor health are separate

Provider reachability is not sufficient evidence that a specific sensor is usable.

Frozen hierarchy:

```text
ProviderHealth
FeedHealth
ObservationHealth
CanonicalSensorHealth
```

### F2 — Quality is scoped

No unqualified global `healthy=true`.

Health is keyed by:

```text
sensor_family
instrument/universe scope
time/granularity
historical/live mode
use_case
```

### F3 — Cross-venue economic synthesis remains downstream

Bloc 6 may compare providers and emit T2 eligibility metadata.

It does not create economic cross-venue composite formulas.

### F4 — Redundancy is independence-aware

Provider/source count does not equal independent evidence count.

Aggregators, mirrors and shared upstream sources are collapsed through a `SourceDependencyGraph`.

### F5 — Unknown dependency is conservative

Unknown aggregator/upstream lineage does not increase strict independent quorum.

### F6 — Semantic comparability gates evidence use

Frozen classes:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

Different operations require different minimum classes.

### F7 — Valid zero is an observation

No event is not the same as no data.

`VALID_ZERO`, `PROVIDER_EMPTY_CONFIRMED`, `GAP_DETECTED`, `NOT_EXPECTED`, `UNSUPPORTED`, `HISTORY_UNAVAILABLE` remain distinct.

### F8 — Gap detection is layered

```text
G0 transport
G1 source interval
G2 projection
G3 T1 normalization
G4 canonical sensor coverage
```

### F9 — Failover restores sensor coverage, not venue identity

A Gate fallback never becomes a Kraken observation.

### F10 — No silent resolution downgrade

A daily fallback cannot satisfy a strict 5m request unless downgrade permission is explicit.

### F11 — No silent universe downgrade

U0 healthy and U1 degraded must remain separately visible.

### F12 — Disagreement is first-class

High cross-venue disagreement can represent real economic heterogeneity.

Outlier source exclusion requires diagnostics; no blind majority vote.

### F13 — Quality uses hard gates plus a vector

Frozen quality dimensions include:

```text
ACCESS
INTEGRITY
FRESHNESS
COMPLETENESS
PIT_VALIDITY
IDENTITY_CONFIDENCE
SEMANTIC_CONFIDENCE
INDEPENDENCE
REDUNDANCY
AGREEMENT
COVERAGE
REPRODUCIBILITY
```

PIT/integrity/semantic hard failures cannot be averaged into a pass.

### F14 — Operating modes are explicit

```text
FULL
DEGRADED_REDUNDANT
DEGRADED_PARTIAL
RESEARCH_ONLY
DATA_BLOCKED
```

Downstream objects inherit mode and cannot silently upgrade it.

### F15 — Quorum is use-case specific

Policies depend on:

```text
sensor
universe tier
strict replay vs canonical research vs live shadow vs exploratory
historical/live
granularity
instrument family
```

### F16 — Venue-local and market-wide claims are different

Single-venue data can support venue-local analysis without satisfying a market-wide quorum.

### F17 — Specialist sources stay specialist

A source such as Deribit liquidation-tagged trades can be highly valuable without being treated as numerically equivalent to broad interval liquidation totals.

### F18 — Aggregator double-counting is forbidden

Third-party aggregate evidence remains useful for corroboration but cannot inflate independent quorum when it reuses direct sources already counted.

### F19 — Reconciliation emits eligibility, not synthetic truth

Bloc 6 output includes allowed operations such as:

```text
VENUE_LOCAL_FEATURES
CROSS_VENUE_BREADTH
CROSS_VENUE_CONSENSUS
CROSS_VENUE_DISPERSION
NOTIONAL_SUM
WEIGHTED_AGGREGATION
CORROBORATION_ONLY
```

Actual formulas remain Bloc 9 work.

### F20 — Sum eligibility is stricter than comparison eligibility

Comparable observations are not automatically safe to sum.

### F21 — Quarantine is scoped

A broken Kraken OI parser does not automatically quarantine Kraken funding/liquidation feeds.

### F22 — Quality policy is versioned

Every decision records policy, dependency graph, comparability registry and T1 generation versions.

### F23 — Provider recovery uses anti-flap state

A single good response does not immediately restore a failed source to preferred healthy routing.

### F24 — Historical and live failover policies remain distinct

A source can be historical primary and live secondary for the same sensor.

---

## 2. Frozen core objects

```text
ProviderHealthSnapshot
FeedHealthSnapshot
ObservationHealthSnapshot
CanonicalSensorHealthSnapshot
ObservationExpectation
SourceDependencyGraph
QuorumPolicy
QuorumResult
DisagreementResult
CrossProviderReconciliation
T2Eligibility
SourceConfidenceProfile
QualityVector
FailoverRoute
FailoverDecision
RecoveryState
QuarantineRecord
```

---

## 3. Frozen health vocabulary

```text
HEALTHY
PARTIAL
DEGRADED
STALE
GAPPED
SCHEMA_DRIFT
SEMANTIC_REVIEW_REQUIRED
ACCESS_BLOCKED
RATE_LIMITED
PROVIDER_DOWN
HISTORY_INCOMPLETE
INTEGRITY_FAILURE
REVISION_CONFLICT
UNVERIFIED
DATA_BLOCKED
```

---

## 4. Frozen redundancy vocabulary

```text
R0_NONE
R1_SINGLE_INDEPENDENT
R2_TWO_INDEPENDENT
R3_THREE_PLUS_INDEPENDENT
RX_DEPENDENCY_AMBIGUOUS
```

Additional counts remain explicit:

```text
raw_source_count
eligible_source_count
independent_source_count
venue_count
first_party_count
third_party_count
community_count
```

---

## 5. Frozen disagreement vocabulary

```text
LOW_EXPECTED
MODERATE_EXPECTED
HIGH_ECONOMIC_HETEROGENEITY
SUSPECT_DATA_DIVERGENCE
SEMANTIC_MISMATCH
INSUFFICIENT_COMPARABLE_SOURCES
```

Outlier handling:

```text
ECONOMIC_OUTLIER_KEEP
DATA_OUTLIER_QUARANTINE
UNKNOWN_REVIEW_REQUIRED
```

---

## 6. Frozen reconciliation states

```text
ALIGNED
ALIGNED_WITH_ECONOMIC_DISPERSION
PARTIALLY_ALIGNED
CORROBORATION_ONLY
DEPENDENCY_AMBIGUOUS
SEMANTIC_MISMATCH
UNIT_MISMATCH
TIME_ALIGNMENT_FAILED
INSUFFICIENT_EVIDENCE
DATA_QUALITY_CONFLICT
```

---

## 7. Frozen initial critical redundancy goals

These are engineering targets, not guarantees.

```text
LIQUIDATIONS
  >=2 independent for strict U0 cross-venue use where coverage permits

OPEN_INTEREST
  >=2 independent

FUNDING
  >=2 independent, prefer >=3 where available

ORDER_FLOW
  >=2 independent for cross-venue state
  single venue allowed for venue-local research

DEPTH/LIQUIDITY
  >=2 independent for U0 cross-venue state
  single venue allowed for venue-local microstructure
```

Lower universe tiers may operate in explicitly degraded/research-only modes.

---

## 8. Frozen planned configuration files

```text
quality_policy.yaml
redundancy_policy.yaml
source_dependencies.yaml
comparability_policy.yaml
quorum_policy.yaml
failover_routes.yaml
recovery_policy.yaml
```

No quality thresholds should be buried only in source code.

---

## 9. Frozen planning history

```text
SENSOR-PLAN-B6A
  quality/redundancy/failover architecture

SENSOR-PLAN-B6B
  source independence/comparability/quorum

SENSOR-PLAN-B6C
  freshness/gaps/disagreement/failover routing

SENSOR-PLAN-B6D
  quality scoring/degraded modes/continuation policy

SENSOR-PLAN-B6E
  cross-provider reconciliation/evidence policy

SENSOR-PLAN-B6F
  acceptance tests/staged implementation commits

SENSOR-PLAN-B6G
  freeze manifest / Bloc 7 handoff
```

---

## 10. Frozen future implementation sequence

```text
SENSOR-B6-I01  enums/models/modes
SENSOR-B6-I02  expectations/freshness
SENSOR-B6-I03  layered gap detection
SENSOR-B6-I04  provider/feed/observation health
SENSOR-B6-I05  source dependency graph
SENSOR-B6-I06  semantic comparability
SENSOR-B6-I07  quorum/redundancy
SENSOR-B6-I08  disagreement diagnostics
SENSOR-B6-I09  reconciliation/T2 eligibility
SENSOR-B6-I10  quarantine/invariants
SENSOR-B6-I11  quality vector/hard gates
SENSOR-B6-I12  operating-mode policy
SENSOR-B6-I13  routing/failover
SENSOR-B6-I14  recovery/anti-flap
SENSOR-B6-I15  policy/version lineage
SENSOR-B6-I16  historical T1 integration
SENSOR-B6-I17  live provider-health boundary
SENSOR-B6-I18  evidence/reporting
SENSOR-B6-I19  adversarial/property/determinism suite
SENSOR-B6-I20  full acceptance
SENSOR-B6-I21  Bloc 7 handoff
```

No squashing during staged review.

---

## 11. Blocking acceptance gates

Implementation must later prove:

- provider/sensor health separation;
- explicit missingness and valid-zero semantics;
- independence-aware redundancy;
- semantic comparability gating;
- PIT preservation;
- provider identity preserved through failover;
- no blind majority vote;
- deterministic degraded modes;
- hard quality gates are non-compensatory;
- scope-aware quality/quorum;
- cross-venue economic formulas remain outside Bloc 6;
- versioned/replayable quality decisions.

Any failure is blocking.

---

## 12. Bloc 7 handoff — Historical Backfill Program

Bloc 7 must plan the **2020-06 → present historical backfill program** using Blocs 2–6.

It must not merely download everything in one giant job.

Required topics:

1. exact target start/end horizons by sensor/provider;
2. U0/U1/U2 universe policy over time;
3. PIT instrument-lifecycle-aware task generation;
4. provider/sensor backfill priority order;
5. deterministic sharding;
6. shard size by source type;
7. restart/resume using Bloc 3/4 contracts;
8. T0 acquisition + T1 normalization pipeline coupling;
9. Bloc 6 quality evaluation after each shard/window;
10. dynamic source coverage — do not require every provider every year;
11. first-party versus aggregator evidence roles;
12. historical source mutation handling;
13. rate-limit budgeting;
14. disk/quota budgeting;
15. provider-specific archive/API strategies;
16. orderbook footprint controls;
17. coverage heatmaps;
18. gap registry and reattempt policy;
19. backfill reconciliation generations;
20. acceptance gates by sensor family;
21. evidence package proving what historical mechanical coverage truly exists.

### Backfill priority should initially favor scientific value

```text
1. liquidations
2. open interest
3. funding
4. aggressor flow / trades
5. depth / spread / liquidity
6. positioning / basis
```

This order may be adjusted only when provider dependencies make another order necessary.

### Critical Bloc 7 doctrine

Historical coverage is allowed to be ragged.

The system must record:

```text
sensor_available
source_count
independent_source_count
source_set
quality_mode
coverage
```

through time rather than forcing a rectangular fake panel.

---

## 13. Completion checklist

- [x] provider vs sensor health separated
- [x] feed/observation/canonical health objects defined
- [x] freshness expectation model defined
- [x] layered gap taxonomy defined
- [x] valid-zero semantics preserved
- [x] dependency graph defined
- [x] aggregator double-count protection defined
- [x] semantic comparability usage rules defined
- [x] quorum model defined
- [x] redundancy classes defined
- [x] venue-local vs cross-venue claim distinction defined
- [x] disagreement diagnostics defined
- [x] outlier/quarantine policy defined
- [x] quality vector + hard gates defined
- [x] degraded modes defined
- [x] continuation policies defined
- [x] failover route logic defined
- [x] historical/live route split defined
- [x] anti-flap recovery defined
- [x] reconciliation/T2 eligibility boundary defined
- [x] planned modules/configs defined
- [x] adversarial/property tests defined
- [x] staged implementation commits defined
- [x] Bloc 7 historical-backfill handoff defined

---

## 14. Final planning verdict

`PASS_BLOC_06_PLAN_FROZEN`

Rationale:

The fabric now has a complete quality control plane capable of distinguishing provider availability from actual sensor usability, measuring independence-aware redundancy, preventing aggregator double counting, enforcing semantic/PIT gates, detecting stale/gapped evidence, preserving economically meaningful disagreement, routing around provider failures without falsifying provenance, exposing deterministic degraded modes, quarantining scoped bad evidence, and handing only explicitly eligible source sets to downstream T2 construction.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 7`
