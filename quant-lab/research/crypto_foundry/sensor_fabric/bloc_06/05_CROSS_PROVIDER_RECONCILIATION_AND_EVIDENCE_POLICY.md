# BLOC 6 — CROSS-PROVIDER RECONCILIATION & EVIDENCE POLICY

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define how multiple provider observations can be compared, reconciled for quality purposes, and handed forward without prematurely creating a synthetic market value.

The quality layer must answer:

> Are these observations mutually usable as evidence for the same economic sensor?

It does **not** answer:

> What is the final cross-venue liquidation/OI/order-flow composite?

That belongs to Bloc 9.

---

## 2. Reconciliation stages

Cross-provider evidence passes through:

```text
T1 observations
  ↓
ALIGN TIME
  ↓
ALIGN ECONOMIC CONTRACT SCOPE
  ↓
VERIFY SEMANTIC CLASS
  ↓
VERIFY UNITS / METHODOLOGY
  ↓
COLLAPSE DEPENDENCY GROUPS
  ↓
COMPARE / DIAGNOSE
  ↓
QUALITY RECONCILIATION RESULT
  ↓
T2 ELIGIBILITY METADATA
```

No numeric averaging is required at this stage.

---

## 3. Reconciliation result

`CrossProviderReconciliation`:

```text
sensor_family
scope
window
input_observation_ids[]
eligible_observation_ids[]
excluded_observation_ids[]
exclusion_reasons[]
semantic_classes{}
dependency_groups{}
time_alignment_state
unit_alignment_state
methodology_alignment_state
comparison_metrics{}
reconciliation_state
T2_eligibility
quality_flags[]
evidence_refs[]
```

---

## 4. Reconciliation states

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

## 5. Time alignment

Provider intervals may differ in:

- timestamp anchor;
- left/right closure;
- publish delay;
- native cadence;
- aggregation window.

Comparison requires an explicit window policy.

Example:

```text
Gate 5m liquidation stats: 12:00–12:05
Kraken 5m analytics: 12:00–12:05
```

may be aligned.

But:

```text
Gate 5m interval
Coinalyze 1d interval
```

cannot be treated as exact contemporaneous equivalents.

Possible use:

```text
CORROBORATION_ONLY
```

---

## 6. Economic-scope alignment

Two sources may both say BTC but represent different scopes:

```text
BTCUSDT linear perp
BTCUSD inverse perp
all BTC derivatives aggregate
BTC perpetual only
BTC futures + perpetual aggregate
```

Bloc 5 identity resolves these scopes.

Bloc 6 must compare only within policies that explicitly allow scope differences.

---

## 7. Unit alignment

Cross-provider comparison may use derived comparable fields while always retaining native fields.

Examples:

```text
liquidation_usd
OI_usd_equivalent
funding_8h_equivalent
signed_trade_notional_usd
fixed-bps depth usd
```

Every comparison field retains:

```text
methodology_id
conversion_input_ids[]
```

No comparison is allowed when the conversion source itself fails PIT or quality gates.

---

## 8. Provider analytics versus local reconstruction

Provider-native analytics and locally reconstructed metrics must remain distinct evidence classes.

Example:

```text
Kraken CVD = provider-derived analytic
Binance CVD = local reconstruction from public trades
```

The reconciliation layer compares them only after verifying:

- aggressor convention;
- notional basis;
- interval semantics;
- contract scope.

Metadata:

```text
measurement_origin = PROVIDER_ANALYTIC | LOCAL_RECONSTRUCTION | RAW_MEASURE
```

---

## 9. Aggregators

Third-party aggregators can be useful for:

- coverage checks;
- broad-state corroboration;
- detection of missing exchange-native feeds;
- external sanity checking.

But they must not silently dominate first-party evidence.

Rules:

1. upstream venues recorded when known;
2. aggregator never increases strict independent count when composed from already-counted sources;
3. unknown upstream composition triggers dependency ambiguity;
4. aggregator methodology changes require new version/evidence;
5. aggregate value never substitutes for a missing venue-specific value.

---

## 10. Community archives

Community archives are allowed when provenance is acceptable, but evidence class remains explicit.

Example:

```text
BITFINEX_COMMUNITY_ARCHIVE
```

can provide historical liquidation corroboration.

It cannot be described as first-party Bitfinex truth unless the exact evidence is directly exchange-sourced and independently verified.

Fields:

```text
evidence_class = COMMUNITY_ARCHIVE
origin_claim
origin_verification
archive_integrity
```

---

## 11. Reconciliation diagnostics by sensor

### Liquidations

Compare:

- occurrence timing;
- side dominance;
- normalized intensity;
- notional magnitude distribution;
- cross-venue breadth.

Do not expect exact magnitudes across venues.

### OI

Compare:

- venue-local continuity;
- change direction;
- normalized change;
- impossible jumps;
- cross-provider same-venue duplicates where available.

Do not expect equal absolute OI across venues.

### Funding

Compare:

- sign;
- normalized interval equivalent;
- percentile/extreme state;
- publication schedule.

### Order flow

Compare:

- aggressor sign;
- normalized imbalance;
- local CVD trend;
- burst timing.

### Depth/liquidity

Compare:

- normalized bps-band depth;
- spread;
- imbalance;
- slippage approximations;
- withdrawal/recovery timing.

---

## 12. Quality conflict investigation sequence

When sources disagree beyond configured tolerance:

```text
1. check native payload integrity
2. check instrument identity
3. check time alignment
4. check units/conversion
5. check semantic-equivalence registry
6. check source revision
7. check provider methodology drift
8. check known venue-specific event
9. classify as economic heterogeneity / data conflict / unknown
```

No automatic peer-majority exclusion before this sequence.

---

## 13. Quarantine semantics

A source may be quarantined for:

```text
PARSER_ERROR
UNIT_ERROR
SCHEMA_DRIFT
SEMANTIC_DRIFT
INTEGRITY_FAILURE
IMPOSSIBLE_VALUE
TIME_ALIGNMENT_BUG
REVISION_CONFLICT
```

Quarantine is scoped.

Example:

```text
Kraken OI parser quarantined
```

does not automatically quarantine:

```text
Kraken funding
Kraken liquidation
```

unless provider-wide evidence warrants it.

---

## 14. Impossible-value checks

Quality controls should include provider/sensor-specific invariants such as:

- negative OI when impossible;
- malformed timestamps;
- funding outside parser/domain sanity bounds without raw support;
- crossed books after snapshot reconstruction where impossible under format semantics;
- duplicate event IDs with conflicting immutable content;
- liquidation notional inconsistent with raw amount/price/multiplier conversion;
- trade aggressor flag outside known enum.

These checks flag evidence. They do not "repair" it silently.

---

## 15. T2 eligibility metadata

Bloc 6 hands Bloc 9 a structured eligibility object rather than a cleaned aggregate.

`T2Eligibility`:

```text
sensor_family
scope
window
eligible_source_ids[]
eligible_independent_groups[]
excluded_source_ids[]
semantic_compatibility
quality_mode
coverage
reconciliation_state
allowed_operations[]
```

Allowed operations examples:

```text
VENUE_LOCAL_FEATURES
CROSS_VENUE_BREADTH
CROSS_VENUE_CONSENSUS
CROSS_VENUE_DISPERSION
NOTIONAL_SUM
WEIGHTED_AGGREGATION
CORROBORATION_ONLY
```

Bloc 9 still decides the actual formulas.

---

## 16. Sum eligibility is stricter than comparison eligibility

A source set can be comparable without being safely summable.

Example:

```text
Binance OI + Bybit OI
```

may be sum-eligible after normalization if scope is distinct and compatible.

But:

```text
Binance OI + Coinalyze aggregate OI
```

is not sum-eligible because the aggregate may already contain Binance.

Therefore operations are explicit.

---

## 17. Historical reconciliation versions

Reconciliation logic is versioned.

If later research discovers a semantic mistake:

- old T0 remains unchanged;
- old T1 generation remains reproducible;
- old reconciliation decision remains auditable;
- new registry/methodology creates new reconciliation generation.

No silent retroactive rewrite.

---

## 18. Required outputs

Implementation should later produce:

```text
source_dependency_graph.parquet
semantic_comparability_matrix.parquet
reconciliation_results.parquet
quarantine_registry.parquet
T2_eligibility.parquet
source_exclusion_audit.parquet
reconciliation_summary.md
```

---

## 19. Tests required

1. same venue direct + mirror not sum-eligible;
2. aggregator does not double-count upstream direct source;
3. Deribit liquidation-tagged trades classified corroboration-only against Gate interval totals;
4. identical semantic fields with different funding intervals normalize with lineage;
5. inverse vs linear OI comparison fails without valid conversion;
6. high economic venue dispersion stays eligible when data checks pass;
7. isolated parser error quarantines one sensor/feed, not whole provider;
8. corrected methodology creates new reconciliation generation;
9. T2 eligibility distinguishes comparison from summation;
10. community archive evidence remains explicitly lower provenance class.

---

## 20. Frozen principle

> **Reconciliation decides what evidence can be compared or combined; it does not erase venue structure or manufacture a market-wide number.**

`human_review_required = TRUE`
