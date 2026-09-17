# BLOC 6 — FRESHNESS, GAPS, DISAGREEMENT & FAILOVER ROUTING

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define deterministic rules for:

- what counts as fresh;
- how expected observations are inferred;
- how gaps differ from legitimate non-events;
- how provider disagreement is measured without treating venue heterogeneity as error;
- how failover routes are selected;
- how degraded operation is surfaced.

---

## 2. Freshness is sensor-specific

A single stale threshold is invalid across the stack.

Freshness policy must depend on:

```text
sensor_family
feed_mode
native_cadence
requested_cadence
universe_tier
historical_vs_live
```

Examples:

- trade stream expected sub-second/seconds;
- OI may update every 5m;
- realized funding may update every several hours;
- historical monthly archive is not "stale" because it is monthly;
- a liquidation interval with zero events may still be valid if the provider explicitly emits a zero/empty interval.

---

## 3. Expected observation model

`ObservationExpectation`:

```text
provider_id
feed_id
sensor_family
instrument_id
expected_cadence
expected_window_rule
market_hours_rule
source_publish_delay
allowed_lateness
expected_empty_semantics
policy_version
```

Crypto is 24/7, but provider maintenance and instrument lifecycle still matter.

No gap can be declared without an expectation model.

---

## 4. Freshness states

```text
FRESH
LATE_WITHIN_TOLERANCE
STALE
UNKNOWN_CADENCE
NOT_EXPECTED
```

`NOT_EXPECTED` includes:

- pre-listing period;
- post-delisting period;
- provider-declared archive boundary;
- sensor unsupported for instrument.

This must not be collapsed into `MISSING`.

---

## 5. Missingness / gap taxonomy

Minimum:

```text
OBSERVED
VALID_ZERO
PROVIDER_EMPTY_CONFIRMED
LATE
GAP_DETECTED
HISTORY_UNAVAILABLE
NOT_EXPECTED
UNSUPPORTED
ACCESS_BLOCKED
INTEGRITY_BLOCKED
SEMANTIC_BLOCKED
REVISION_BLOCKED
UNKNOWN
```

Important distinction:

> no liquidation event != no liquidation data.

`VALID_ZERO` requires provider semantics proving that zero means a measured zero.

If a provider simply returns no row:

```text
PROVIDER_EMPTY_CONFIRMED
```

or `GAP_DETECTED`, depending on endpoint semantics and expectation model.

---

## 6. Gap detection layers

### G0 — transport gap

Expected fetch/feed heartbeat missing.

### G1 — source interval gap

Provider response exists, but expected interval absent.

### G2 — projection gap

T0A exists but T0B projection missed rows/intervals.

### G3 — T1 normalization gap

Raw evidence exists but canonical row blocked by identity/semantic issue.

### G4 — canonical sensor coverage gap

Too few eligible independent providers remain for requested scope.

The system must state which layer failed.

---

## 7. Gap healing policy

Allowed actions:

```text
RETRY_SAME_PROVIDER
BACKFILL_ARCHIVE
ALTERNATE_ENDPOINT_SAME_PROVIDER
ALTERNATE_PROVIDER_FOR_SENSOR_COVERAGE
MARK_KNOWN_GAP
HUMAN_REVIEW
```

Not allowed:

- zero-fill;
- forward-fill by default;
- interpolation presented as observed data;
- relabeling another venue as the missing venue;
- hiding unresolved gaps in aggregate coverage.

---

## 8. Disagreement framework

Disagreement can be measured only among observations that pass:

1. time alignment;
2. instrument/economic scope alignment;
3. semantic comparability;
4. unit normalization;
5. minimum quality threshold.

`DisagreementResult`:

```text
sensor_family
scope
window
eligible_sources[]
comparison_method
center
spread
pairwise_differences
normalized_dispersion
sign_agreement
rank_agreement
outlier_sources[]
disagreement_class
quality_flags[]
```

---

## 9. Disagreement classes

```text
LOW_EXPECTED
MODERATE_EXPECTED
HIGH_ECONOMIC_HETEROGENEITY
SUSPECT_DATA_DIVERGENCE
SEMANTIC_MISMATCH
INSUFFICIENT_COMPARABLE_SOURCES
```

The quality plane may say:

> disagreement is high but plausibly economic.

It does not need to force a winner.

---

## 10. Sensor-specific disagreement examples

### Funding

Different venue funding rates may legitimately diverge while still being comparable.

High dispersion is often economic state, not quality failure.

### OI

Absolute OI differs by venue by design.

Quality comparison should emphasize:

- impossible jumps;
- unit consistency;
- timestamp alignment;
- venue-local continuity;
- normalized change where appropriate.

Cross-venue absolute mismatch is not an error.

### Liquidations

Different venues will have different liquidation notional.

Agreement may be assessed on:

- event presence;
- long/short dominance;
- normalized intensity;
- broad timing.

### Order flow

Sign disagreement can itself be meaningful.

It is not automatically parser error unless provider-native validation fails.

### Books

Liquidity levels are venue-specific. Quality disagreement needs internal structural checks before cross-venue comparison.

---

## 11. Outlier detection doctrine

Outlier detection is diagnostic only.

An outlier source is not auto-discarded merely because it differs from peers.

Before exclusion test:

- source continuity;
- native payload integrity;
- known venue event;
- contract identity;
- unit conversion;
- timestamp alignment;
- provider methodology;
- cross-check with price/volume where allowed.

Possible outcomes:

```text
ECONOMIC_OUTLIER_KEEP
DATA_OUTLIER_QUARANTINE
UNKNOWN_REVIEW_REQUIRED
```

---

## 12. Failover route model

`FailoverRoute` is configuration-driven:

```text
route_id
sensor_family
scope
preferred_sources[]
fallback_sources[]
specialist_sources[]
minimum_semantic_class
minimum_evidence_class
minimum_independent_sources
allowed_operating_modes[]
```

Routes are not hard-coded in notebooks.

---

## 13. Routing algorithm

Pseudo-flow:

```text
REQUEST sensor/scope/use_case
        ↓
load eligible capabilities
        ↓
apply free-only gate
        ↓
apply PIT availability
        ↓
apply health/freshness/integrity
        ↓
apply semantic comparability
        ↓
collapse dependency groups
        ↓
evaluate preferred route
        ↓
if quorum met -> FULL
else evaluate fallbacks
        ↓
if reduced quorum sufficient -> DEGRADED_REDUNDANT / DEGRADED_PARTIAL
else -> RESEARCH_ONLY or DATA_BLOCKED
```

Every routing decision emits evidence.

---

## 14. Historical vs live failover

Historical failover and live failover must be separate policies.

Example:

- Binance public archive may be excellent for historical trades.
- Kraken analytics may be better for live cross-sensor monitoring.

A provider may therefore be:

```text
HISTORICAL_PRIMARY
LIVE_SECONDARY
```

for the same sensor.

---

## 15. No silent time-resolution downgrade

If requested:

```text
5m OI
```

and only daily history remains, the router may return:

```text
DEGRADED_PARTIAL
available_granularity = 1d
```

only if the caller explicitly permits granularity downgrade.

Otherwise:

```text
DATA_BLOCKED
reason = GRANULARITY_REQUIREMENT_UNMET
```

---

## 16. No silent universe downgrade

If U0 BTC/ETH coverage is healthy but U1 alt coverage collapses, the system must not state "liquidation sensor healthy" globally.

Health is always scoped:

```text
sensor_family
universe_scope
instrument_scope
```

---

## 17. Recovery and re-promotion

A failed source should not jump immediately from DOWN to HEALTHY after one good response.

Use configurable recovery criteria:

```text
minimum_consecutive_successes
minimum_good_duration
schema_stability_checks
freshness_checks
```

States:

```text
FAILED
RECOVERING
HEALTHY
```

This prevents flapping routes.

---

## 18. Route flapping control

Routing must include hysteresis at the **infrastructure** level.

This is not market hysteresis.

Controls:

- minimum source hold time;
- health recovery threshold;
- failure backoff;
- preference stability;
- deterministic tie-break.

The aim is operational stability, not economic inference.

---

## 19. Evidence artifacts

Implementation must later emit:

```text
provider_health.parquet
feed_health.parquet
observation_health.parquet
canonical_sensor_health.parquet
gap_registry.parquet
disagreement_registry.parquet
failover_decisions.parquet
routing_audit.jsonl
```

Small summary reports may be Markdown/CSV.

---

## 20. Tests required

1. valid zero liquidation interval not marked gap;
2. missing row from a provider with explicit empty semantics classified correctly;
3. pre-listing period classified NOT_EXPECTED;
4. stale provider excluded from strict live quorum;
5. daily fallback rejected for 5m strict query;
6. high funding dispersion classified economic rather than automatically corrupt;
7. source outlier retained when native integrity passes and venue event is plausible;
8. parser-unit error triggers suspect-data divergence;
9. route recovers only after configured consecutive successes;
10. U0 healthy / U1 partial scopes remain distinct.

---

## 21. Frozen principle

> **Failover restores sensor coverage, not provider identity. Disagreement is preserved until evidence shows it is a data problem rather than market structure.**

`human_review_required = TRUE`
