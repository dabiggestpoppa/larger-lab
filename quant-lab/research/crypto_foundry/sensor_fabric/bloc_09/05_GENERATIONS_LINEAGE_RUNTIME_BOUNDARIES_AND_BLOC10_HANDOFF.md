# BLOC 9 — T2 GENERATIONS, LINEAGE, RUNTIME BOUNDARIES & BLOC 10 HANDOFF

## 1. Purpose

Freeze how mechanical observables are versioned, stored, regenerated, queried and handed to Bloc 10 without provider coupling or silent methodology drift.

---

## 2. T2 generation model

A T2 generation is identified by at least:

```text
t2_generation_id
created_at
observable_registry_version
t1_generation_id
quality_policy_version
source_dependency_graph_version
baseline_registry_version
code_revision
```

A methodology or upstream semantic change creates a new generation where affected.

No silent in-place overwrite.

---

## 3. Rebuildability

T2 is derived and therefore rebuildable from T1 + methodology registry.

Authoritative hierarchy:

```text
T0 exact evidence
> T1 canonical observation truth
> T2 derived mechanical observables
```

T2 may be discarded/rebuilt if its lineage remains reproducible.

---

## 4. T2 lineage object

Minimum lineage:

```text
observable_id
observable_version
t2_generation_id
input_t1_generation
input_partition_refs / row refs
baseline_id + version
quality_policy_version
eligibility_decision_id
source_dependency_graph_version
methodology_hash
code_revision
```

Cross-venue lineage additionally stores:

```text
contributors
excluded_sources
independence_groups
coverage denominator policy
aggregation/summary method
```

---

## 5. Determinism contract

Given the same:

```text
T1 generation
observable registry
baseline registry
quality policy
code revision
query boundary
```

the T2 result must be deterministic except for explicitly documented floating-point tolerance.

---

## 6. Historical/live parity

Historical and live computation may differ operationally but not semantically.

```text
historical T1 → batch T2
live T1 → incremental T2
```

For a closed interval after late-arriving permitted observations settle, batch and incremental outputs must converge under the same generation/methodology.

This becomes a mandatory acceptance test.

---

## 7. Late arrivals and revisions

When late T1 evidence arrives:

```text
late T1 observation
→ affected T2 windows identified
→ old T2 generation remains auditable
→ new/revised T2 generation emitted
```

No silent mutation of previously materialized historical states.

For live display, current state may update, but lineage/version must show the revision.

---

## 8. Observable registry lifecycle

Registry statuses:

```text
DRAFT
RESEARCH_EXPERIMENTAL
VALIDATED_LOCAL
VALIDATED_CROSS_VENUE
PROMOTED_RUNTIME
DEPRECATED
BLOCKED
```

Promotion requires evidence packet, tests and human review.

No research notebook may self-promote an observable into runtime.

---

## 9. Runtime boundary

Bloc 9 owns computation and materialization.

Bloc 10 owns **read-only serving**.

Bloc 10 may:

- query latest valid venue-local state;
- query cross-venue state;
- query historical slices;
- expose quality/coverage/lineage;
- expose available observable versions.

Bloc 10 may not:

- redefine formulas;
- mutate T2 history;
- choose a different source weighting ad hoc;
- call providers directly;
- bypass Bloc 6 quality decisions.

---

## 10. Planned read model for Bloc 10

Bloc 9 should materialize a query-friendly schema around:

```text
MechanicalStateQuery
MechanicalStateResult
ObservableCatalogEntry
StateQualityEnvelope
StateLineageSummary
AvailableCoverage
```

Suggested query dimensions:

```text
observable_family
observable_id
asset
venue or cross_venue
granularity
window
as_of/start/end
generation
minimum_quality_mode
```

---

## 11. Research-facing export

Research agents need deterministic event-context tables.

Bloc 9 should support export specs such as:

```text
asset
anchor events
time grid
requested observable set
static horizons
rolling windows
quality requirements
```

Output must include missing/blocked states rather than silently dropping rows.

---

## 12. Research firewall

MECH/LF research consumes:

```text
T2 observable IDs
```

not:

```text
Gate long_liq_usd
Kraken aggressor endpoint field
Binance isBuyerMaker raw flag
```

Provider-specific fields stop below T1/T2 boundaries.

---

## 13. No target leakage

Bloc 9 methods may use only contemporaneous/past observations allowed by their declared window.

Forbidden inside T2 runtime features:

```text
future return
future max adverse move
future liquidation total
future containment outcome
future label from research experiment
```

Research may later evaluate T2 against outcomes, but the observable itself remains target-free.

---

## 14. Bloc 10 handoff requirements

Before Bloc 10 implementation planning can be accepted, Bloc 9 must define:

1. observable registry schema;
2. venue-local state schemas;
3. cross-venue state schemas;
4. quality envelope;
5. generation/version rules;
6. lineage contract;
7. deterministic query dimensions;
8. historical/live parity rule;
9. availability/missingness representation;
10. no-mutation service boundary.

---

## 15. Bloc 10 objective preview

Bloc 10 will design the **Read-Only Canonical Sensor Service**.

Its job is to make the fabric easy for research agents and Market OS components to consume without teaching them where files live or how providers work.

Expected properties:

```text
read only
local first
version aware
as_of aware
quality aware
lineage aware
provider independent
historical + latest
```

---

## 16. Frozen rule

A T2 mechanical state is a versioned scientific measurement object, not a dashboard decoration and not a trading signal.
