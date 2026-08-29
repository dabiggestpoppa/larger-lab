# BLOC 11 — RESEARCH INTEGRATION: MECH-21, LF14 & NULL BOUNDARIES

## 1. Objective

Define the exact research-facing handoff from the sensor fabric into the paused global and local research programs without allowing replay infrastructure to become a hypothesis generator, signal engine, or scientific authority.

---

## 2. Research consumer contract

Research agents consume:

```text
ReplayFrame
MechanicalSnapshot
MechanicalEventContext
Market OS runtime objects
Quality/Coverage summaries
Lineage manifests
NullBoundary objects
```

They do not consume provider-native fields directly.

No research module should import Kraken/Gate/Binance/etc. adapters.

---

## 3. MECH-21 handoff

MECH-21 may request mechanical context for:

```text
gain transitions
ceiling transitions
sterile saturation
realization / non-realization
absorptive capacity
distance-to-resolution
forcing mixtures
2022 / recurrent low-gain episodes
calendar / seasonal modulation
```

Recommended mechanical coordinates include, where available:

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
FlowConsensus
LiquidityWithdrawalBreadth
FundingConsensus
VenueDispersion
```

Bloc 11 does not predefine how these relate to MECH response-law coordinates. MECH-21 tests that relationship.

---

## 4. LF14 handoff

LF14's primary unresolved scientific question is the local downside sign-asymmetry mechanism.

Replay must support matched upside/downside event contexts conditioned on already-specified controls such as:

```text
physical shock magnitude
sigma magnitude
rank
liquidity state
capacity state
recency
global state
```

and align mechanical context through:

```text
PRE-SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

where stage labels are supplied by LF research artifacts.

High-value LF14 coordinates:

```text
liquidation intensity / breadth
OI level/change/compression
funding state/change
taker/aggressor imbalance
CVD / signed flow
spread expansion
depth withdrawal
slippage change
venue breadth / concentration / dispersion
```

---

## 5. Sign-asymmetry first-divergence packet

Bloc 11 should make it easy for LF14 to request a neutral packet containing:

```text
matched event IDs
alignment scheme
mechanical coordinate matrix
static horizon matrix
rolling horizon matrix
quality matrix
coverage matrix
missingness matrix
venue breadth / dispersion matrix
physical and standardized amplitudes
distribution summaries p25/p50/p75/p90
lineage refs
```

LF14 then performs the inferential/mechanism analysis.

Bloc 11 does not optimize which variables create the largest sign separation.

---

## 6. Mechanical sensor availability statuses

For every research event × sensor:

```text
MECHANICALLY_OBSERVED
PARTIALLY_OBSERVED
CORROBORATION_ONLY
QUALITY_BLOCKED
HISTORY_UNAVAILABLE
NOT_EXPECTED
DATA_BLOCKED
```

If a requested mechanical family remains unavailable, the research status stays blocked rather than being replaced by proxy mining.

---

## 7. Null boundary architecture

`NullBoundary` minimum fields:

```text
null_id
scope
sensor_or_state
start_at
end_at
reason
quality_mode
coverage
attempted_sources
independent_sources
repair_status
valid_neighboring_region
evidence_refs
generation_set
```

Reasons may include:

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

A null boundary is a first-class scientific output, not an error to hide.

---

## 8. Event eligibility tiers

To avoid silently mixing evidence quality, event-context exports should label:

```text
E0_BLOCKED
E1_SINGLE_SOURCE
E2_REDUNDANT
E3_CROSS_VENUE
E4_MULTI_MECHANIC
E5_MULTI_MECHANIC_REDUNDANT
```

These tiers describe evidence availability only.

They do not imply stronger effect size or better trading opportunity.

---

## 9. Static + rolling requirement

Any MECH/LF research packet using temporal context must, unless impossible, include both:

```text
STATIC 1D / 3D / 7D / 14D / 30D / 60D
ROLLING 3D / 7D / 14D / 30D
ROLLING 60D where supported
```

If one view cannot be computed, report it explicitly.

Disagreement between static and rolling views is evidence, not a nuisance to average away.

---

## 10. Causal discipline

Replay order alone does not establish causality.

Bloc 11 outputs are tagged as:

```text
OBSERVED
DERIVED_MEASUREMENT
RESEARCH_ANNOTATION
```

Causal level remains controlled by the project's L0–L6 ladder and the downstream research artifact.

Bloc 11 cannot promote a relation to causal status.

---

## 11. Research export reproducibility receipt

Each research packet includes:

```text
packet_id
request hash
replay plan hash
generation lock hash
research event registry version
sensor registry version
quality policy version
code revision
output checksum
created_at
```

This receipt must allow later reproduction after the active generations have advanced.

---

## 12. No silent sample filtering

If events are dropped because required mechanics are unavailable, export:
- original requested N;
- included N;
- excluded N;
- exclusion reasons by sensor/year/rank/sign;
- whether exclusions are asymmetric across groups.

This is mandatory for LF14 sign work because data availability itself could create apparent sign differences.

---

## 13. Research restart boundary

Bloc 11 provides the bridge but does **not** authorize MECH-21 or LF14 to restart.

Restart authority belongs to Bloc 12 after full-system validation.

Until then:

```text
research_bridge_ready = possible
research_restart_authorized = FALSE
```

---

## 14. Required tests

- MECH packet cannot contain provider-native fields;
- LF14 matched-event packet preserves both signs and exclusion accounting;
- blocked mechanics produce NullBoundary rather than zero/proxy;
- static+rolling package completeness is audited;
- event eligibility tier reflects independence/coverage, not raw source count;
- no research status is promoted by replay;
- causal labels are not invented;
- reproducibility receipt pins all generations;
- asymmetric missingness is surfaced;
- restart remains unauthorized until Bloc 12.