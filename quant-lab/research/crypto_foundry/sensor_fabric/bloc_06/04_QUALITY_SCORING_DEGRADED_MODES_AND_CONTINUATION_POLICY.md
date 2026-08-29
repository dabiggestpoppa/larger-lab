# BLOC 6 — QUALITY SCORING, DEGRADED MODES & CONTINUATION POLICY

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define how the fabric turns raw health evidence into an interpretable quality state **without hiding individual failure dimensions inside one magic score**.

The output must tell a caller:

- what is good;
- what is weak;
- which source dimensions failed;
- whether the requested use is still allowed;
- whether a lower-confidence/degraded mode is permitted;
- whether human review is required.

---

## 2. No single quality scalar as truth

The canonical health object must preserve a vector of quality coordinates.

Minimum coordinates:

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

A compact score may be computed for sorting/UI, but must never replace these dimensions.

---

## 3. Quality vector

`QualityVector`:

```text
access_score
integrity_score
freshness_score
completeness_score
pit_score
identity_score
semantic_score
independence_score
redundancy_score
agreement_score
coverage_score
reproducibility_score
blocking_dimensions[]
warning_dimensions[]
```

Initial scores may be normalized `[0,1]`, but exact formulas remain policy/versioned infrastructure semantics, not research facts.

---

## 4. Blocking dimensions

Some failures cannot be averaged away.

Hard blockers for strict canonical use:

```text
ACCESS = invalid/paid-blocked
INTEGRITY = failed
PIT_VALIDITY = failed
IDENTITY_CONFIDENCE = unresolved
SEMANTIC_CONFIDENCE = incompatible
REVISION_STATE = ambiguous under strict policy
```

Example:

```text
freshness = 1.0
coverage = 1.0
semantic = 0.0
```

must not average to a passing score.

Therefore use:

```text
HARD_GATES + SOFT_QUALITY_VECTOR
```

not weighted-average-only logic.

---

## 5. Quality status hierarchy

After hard gates:

```text
HIGH
GOOD
FAIR
LOW
UNUSABLE
```

Status is always accompanied by operating mode.

Possible combination:

```text
quality_status = FAIR
operating_mode = DEGRADED_REDUNDANT
```

---

## 6. Operating-mode decision tree

### FULL

Requirements:

- all hard gates pass;
- requested quorum met;
- required universe/time/granularity covered;
- no unresolved severe integrity/semantic flags.

### DEGRADED_REDUNDANT

Use when:

- preferred provider failed;
- alternate independent sources preserve requested sensor coverage;
- strict minimum quorum still met or configured reduced quorum is explicitly allowed;
- quality flags disclose reduced source set.

### DEGRADED_PARTIAL

Use when:

- some requested instruments/venues/time buckets unavailable;
- granularity or venue breadth reduced;
- evidence still scientifically useful for restricted claims.

### RESEARCH_ONLY

Use when:

- data is not strong enough for canonical runtime/replay state;
- but descriptive/manual research can proceed with explicit limitations.

### DATA_BLOCKED

Use when:

- hard gate fails;
- no allowed quorum;
- PIT or lineage invalid;
- comparability unresolved;
- remaining data would materially misrepresent requested claim.

---

## 7. Continuation policies by use case

Each caller supplies/use-case defaults:

```text
STRICT_HISTORICAL_REPLAY
CANONICAL_RESEARCH_PANEL
SHADOW_LIVE_RUNTIME
EXPLORATORY_RESEARCH
CROSSCHECK
```

### Strict historical replay

Default:

```text
no PIT ambiguity
no unresolved source revision ambiguity
no semantic ambiguity
quorum per policy
no silent granularity downgrade
```

### Canonical research panel

May permit:

- partial venue coverage;
- explicit known gaps;
- variable source count through time;

but every row/window must carry source and quality state.

### Shadow live runtime

May continue in `DEGRADED_REDUNDANT` with sufficient fallback coverage.

### Exploratory research

May use `RESEARCH_ONLY` data if the analyst explicitly requests it and output carries limitations.

---

## 8. Coverage score

Coverage is multidimensional.

Track separately:

```text
time_coverage
instrument_coverage
venue_coverage
sensor_field_coverage
granularity_coverage
```

Do not compress these too early.

Example:

```text
BTC 2022 liquidation:
time = 0.98
venue = 0.40
field = 1.00
```

is different from:

```text
time = 0.40
venue = 0.98
field = 1.00
```

---

## 9. Completeness score

Completeness compares observed data against **expected** data, after lifecycle and source cadence rules.

```text
completeness = observed_expected_units / expected_units
```

but only where expected units are well-defined.

If cadence is unknown:

```text
completeness_state = UNKNOWN
```

not an invented percentage.

---

## 10. Freshness score

Freshness is normalized relative to native cadence and allowed lateness.

Example conceptual mapping:

```text
age <= expected + tolerance -> 1.0
moderately late -> decays
beyond stale boundary -> 0
```

Exact curves remain policy-versioned.

Funding must not be penalized for not updating every minute when its native schedule is 8h.

---

## 11. Integrity score

Integrity considers:

- T0 blob hash validity;
- projection lineage;
- parser validation;
- sequence integrity where relevant;
- manifest consistency;
- revision state.

Some integrity conditions are binary blockers.

---

## 12. Semantic confidence

Derived from:

- field-definition evidence;
- provider docs;
- parser fixtures;
- unit verification;
- semantic-equivalence class;
- methodology version stability.

Possible statuses:

```text
VERIFIED
HIGH
MEDIUM
LOW
UNKNOWN
INCOMPATIBLE
```

`INCOMPATIBLE` blocks aggregation/comparison.

---

## 13. Agreement score is not always "higher is better"

For mechanically venue-specific states, disagreement can be meaningful.

Therefore `agreement_score` is primarily:

- an observation about cross-source consistency;
- a potential quality warning when paired with other anomalies;
- later an economic feature candidate in Bloc 9.

It must **not** universally penalize high real economic dispersion.

Use a separate:

```text
disagreement_interpretation = EXPECTED_ECONOMIC | SUSPECT_DATA | UNKNOWN
```

---

## 14. Source confidence

Each provider/sensor can carry a `SourceConfidenceProfile`:

```text
first_party_status
capability_evidence_level
historical_depth_verified
parser_test_strength
semantic_confidence
integrity_support
known_gap_rate
operational_stability
```

No provider gets one universal confidence rank.

---

## 15. Health aggregation rule

Canonical health should be assembled in layers:

```text
provider/feed health
        ↓
observation health
        ↓
comparability eligibility
        ↓
independence collapse
        ↓
quorum
        ↓
coverage + quality vector
        ↓
operating mode
```

Do not start from one global score and work backward.

---

## 16. Degraded-mode propagation

Downstream objects must inherit quality mode.

Example later T2 state:

```text
LiquidationState:
  status = PROMOTED
  data_mode = DEGRADED_REDUNDANT
  source_count_independent = 2
  missing_venues = [KRAKEN]
```

A downstream node cannot upgrade `DEGRADED_PARTIAL` to `FULL` without new evidence.

Quality may degrade downstream, never silently improve.

---

## 17. Quality provenance

Every quality decision records:

```text
policy_version
input_health_snapshot_ids[]
source_dependency_graph_version
comparability_registry_version
quorum_policy_id
calculated_at
```

This lets historical replay reproduce why the system considered a sensor healthy at a given checkpoint.

---

## 18. Avoiding confidence theater

Quality numbers are infrastructure controls, not Bayesian certainty about market truth.

Do not display:

```text
97% confident liquidation truth
```

unless there is a rigorously defined statistical object behind it.

Prefer:

```text
quality = GOOD
mode = DEGRADED_REDUNDANT
independent_sources = 2
venue_coverage = 0.67
PIT = PASS
integrity = PASS
```

---

## 19. Quality policy config

Planned config:

```yaml
sensor_family: LIQUIDATION
universe_tier: U0
use_case: STRICT_HISTORICAL_REPLAY
hard_gates:
  pit: required
  integrity: required
  semantic: required
quorum:
  independent_sources: 2
coverage:
  min_time_ratio: 0.95
allow:
  granularity_downgrade: false
  research_only_fallback: false
```

All thresholds must be versioned and reviewable.

---

## 20. Quality audit reports

Implementation must produce:

```text
quality_summary_by_sensor.csv
quality_summary_by_provider.csv
quality_summary_by_instrument.csv
quality_summary_by_period.csv
operating_mode_history.parquet
blocked_windows.parquet
degraded_windows.parquet
quality_policy_audit.md
```

---

## 21. Required tests

1. hard semantic failure blocks despite high other scores;
2. provider outage degrades source count but sensor stays FULL if policy still met;
3. quorum reduction yields DEGRADED_REDUNDANT, not FULL;
4. partial instrument coverage yields DEGRADED_PARTIAL;
5. PIT ambiguity forces DATA_BLOCKED in strict replay but can be RESEARCH_ONLY in exploratory mode;
6. disagreement alone does not mark data unusable;
7. downstream object cannot upgrade parent data mode;
8. quality calculation is reproducible from versioned inputs;
9. unknown expected cadence does not fabricate completeness;
10. U0 and U2 policies produce different legitimate modes for same raw source set.

---

## 22. Frozen principle

> **Quality is a vector plus hard gates. Degraded operation must be explicit, scoped and inherited downstream; it is never an excuse to hide missing evidence.**

`human_review_required = TRUE`
