# BLOC 11 — EVENT CONTEXT & MECHANICAL SNAPSHOT COMPILATION

## 1. Objective

Define how replay frames become scientifically useful event contexts without turning the replay layer into a research-model or strategy engine.

The compiler packages already-earned mechanical states around a research anchor and preserves their temporal evolution, quality, missingness and lineage.

---

## 2. Event anchor object

`ResearchEventAnchor` minimum fields:

```text
event_id
event_type
anchor_at
asset_scope
contract_scope
venue_scope
source_research_ref
anchor_definition_version
anchor_quality
notes
```

The anchor may come from:
- prior Field Model event registry;
- LF shock registry;
- MECH state transition registry;
- externally supplied research timestamps;
- manually approved event set.

Bloc 11 does not redefine whether an event is scientifically valid.

---

## 3. Event-relative windows

The compiler must support both fixed horizons and rolling windows.

### Canonical daily static checkpoints

```text
1D / 3D / 7D / 14D / 30D / 60D
```

### Canonical rolling windows

```text
3D / 7D / 14D / 30D
60D where support is adequate
```

### Event-relative checkpoints

For mechanism work:

```text
PRECONDITION
INITIATION
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
RECOVERY / REJOIN / DECOUPLING where defined
```

These stage labels are research annotations. Replay must not infer them from mechanical data unless a versioned upstream research definition supplies the mapping.

---

## 4. `MechanicalSnapshot`

A compact state object at one frame:

```text
snapshot_id
frame_at
as_of
asset_scope
universe_snapshot_id
liquidation_state
leverage_state
funding_state
order_flow_state
liquidity_state
positioning_state
basis_state
cross_venue_states
quality_vector
coverage_vector
missingness_vector
state_transitions
lineage_refs
generation_lock_hash
status
```

No field is mandatory to be numerically populated if evidence is unavailable.

---

## 5. `MechanicalEventContext`

Packages an anchor plus a sequence of snapshots.

```text
context_id
event_id
anchor_at
pre_window
post_window
snapshots
static_views
rolling_views
transition_summary
quality_summary
coverage_summary
blocked_coordinates
lineage_manifest
```

The summary is descriptive only.

Examples of valid descriptive outputs:
- liquidation breadth expanded before anchor;
- OI contracted after anchor;
- sell aggressor flow was broad across three independent venues;
- spread/depth deterioration was venue-local rather than broad;
- funding remained neutral while forced deleveraging rose;
- evidence for depth was DATA_BLOCKED for part of the event.

Invalid outputs at this layer:
- therefore price will fall;
- short signal;
- expected return;
- target / stop;
- execution recommendation.

---

## 6. Transition context

Replay should expose transitions already defined in Bloc 9, such as:

```text
QUIET → ELEVATED → BURST
OI_EXPANSION → OI_COMPRESSION
LIQUIDITY_STABLE → WITHDRAWAL → RECOVERY
FLOW_LOCAL → FLOW_BROAD
DISPERSED → CONSENSUS
```

For each transition preserve:

```text
from_state
to_state
transition_at
state_age_before
state_age_after
transition_velocity
physical_change
standardized_change
coverage_at_transition
source_count
independent_source_count
```

No causal claim is attached merely because a transition preceded another.

---

## 7. Cross-venue event geometry

Event context should preserve:

```text
breadth
consensus
dispersion
concentration
venue-local extremes
source independence
```

A broad market event and a single-venue stress event must remain distinguishable.

Useful v1 descriptors:

```text
MARKET_WIDE
MULTI_VENUE_PARTIAL
VENUE_CONCENTRATED
VENUE_LOCAL
INSUFFICIENT_COVERAGE
```

These are descriptive topology labels, not strategy states.

---

## 8. Rate vs reach support

Because LF13/14 explicitly separates propagation rate from peer reach, the event-context compiler must preserve distributional summaries rather than median-only views.

Where the underlying research object provides them, expose:

```text
p25
p50
p75
p90
mean
coverage
n
```

for reach/intensity/response variables.

Do not synthesize peer-response distributions from derivatives data unless a downstream research module explicitly defines the relation.

---

## 9. Mechanical first-divergence helper

For matched-event studies such as LF14 sign asymmetry, Bloc 11 may provide a neutral comparison utility:

`compare_event_contexts(group_a, group_b, coordinates, alignment)`

Allowed outputs:
- difference in means/quantiles;
- first timestamp/stage where a prespecified coordinate diverges under supplied statistical criterion;
- coverage differences;
- missingness differences;
- venue-breadth differences.

The utility must not choose the variables to optimize predictive separation.

It is a measurement helper, not feature-selection or alpha mining.

---

## 10. Quality-aware context compilation

Each coordinate includes:

```text
value
quality_mode
coverage
independent_sources
warnings
```

If quality falls below the request requirement:

```text
coordinate = NULL
status = DATA_BLOCKED or QUALITY_BLOCKED
```

No context-level average may conceal blocked coordinates.

---

## 11. Exact lineage

Every event context must be reproducible back to:

```text
research event anchor
→ replay plan/frame
→ T2 state
→ T1 observations
→ T0 acquisitions
→ exact source blob SHA256
```

A `ContextLineageManifest` stores the transitive evidence graph.

---

## 12. Export profiles

Planned profiles:

```text
FULL_RESEARCH
COMPACT_RESEARCH
EVENT_MATRIX
HUMAN_REVIEW
```

`FULL_RESEARCH` includes all state/quality/lineage references.

`EVENT_MATRIX` provides one deterministic tabular row or row-set per event for controlled analysis, never silently dropping quality/missingness fields.

---

## 13. Required tests

- event windows honor anchor exactly;
- static and rolling views are both available;
- stage labels are not invented by replay;
- null coordinates stay null;
- lineage closes to T0;
- cross-venue breadth preserves source count/coverage;
- transition timestamps are deterministic;
- distributional summaries do not collapse to medians only;
- comparison utility does not perform target optimization;
- identical event plan/generation produces identical context checksum.