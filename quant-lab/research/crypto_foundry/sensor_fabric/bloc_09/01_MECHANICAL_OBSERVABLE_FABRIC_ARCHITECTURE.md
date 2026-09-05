# BLOC 9 — MECHANICAL OBSERVABLE FABRIC ARCHITECTURE

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent blocs:** 1–8 frozen  
**Purpose:** convert canonical T1 mechanical observations into versioned, PIT-safe T2 mechanical state objects without collapsing provider identity, inventing hidden certainty, or producing strategy signals.

---

## 1. Mission

Bloc 9 is the first interpretation layer above canonical observations.

```text
T0 exact evidence
   ↓
T1 canonical observations
   ↓
Bloc 6 quality / eligibility
   ↓
T2 venue-local mechanical observables
   ↓
T2 cross-venue mechanical observables
   ↓
Bloc 10 read-only canonical sensor service
```

Hard rule:

> T2 describes mechanics. It does not decide trades.

No entry, exit, target, stop, position size, leverage, portfolio weight, execution route, expected PnL, or alpha score belongs here.

---

## 2. Doctrine

The observable layer must preserve the project framing:

```text
STRUCTURE → STATE → CONSTRAINT → REGIME → TRIGGER → EXECUTION → RISK
```

Bloc 9 operates primarily at **STATE / CONSTRAINT**.

Its job is to answer questions like:

- are liquidations isolated or broadening?
- is leverage expanding, compressing, or rotating across venues?
- is funding pressure locally extreme or market-wide?
- is aggressor flow coherent across venues or fragmented?
- is liquidity being withdrawn, replenished, or merely redistributed?
- are positioning/basis conditions aligned or dislocated?

It must not answer:

- should we buy/sell?
- what direction comes next?
- what is the optimal trade?

Direction remains downstream/emergent.

---

## 3. Two-stage T2 architecture

### T2A — venue-local mechanical state

Each provider/venue remains separately observable.

Examples:

```text
Kraken BTC LiquidationState
Gate BTC LiquidationState
Binance BTC LeverageState
OKX BTC LiquidityState
```

### T2B — cross-venue mechanical state

Only Bloc 6-approved comparable/eligible T2A states may participate.

Examples:

```text
CrossVenueLiquidationState
CrossVenueLeverageState
CrossVenueFundingState
CrossVenueOrderFlowState
CrossVenueLiquidityState
CrossVenuePositioningState
CrossVenueBasisState
```

Cross-venue objects preserve:

- contributors;
- excluded contributors;
- independence groups;
- weighting method;
- disagreement;
- quality mode;
- coverage;
- methodology version.

---

## 4. Canonical mechanical state families

Bloc 9 freezes seven primary state families.

### 4.1 LiquidationState

Minimum candidate coordinates:

```text
long_liq_notional
short_liq_notional
total_liq_notional
liq_imbalance
liq_intensity_vs_oi
liq_intensity_vs_volume
liq_count
liq_velocity
liq_acceleration
liq_burstiness
liq_breadth
liq_persistence
liq_recovery
```

Long/short semantics must use Bloc 5 liquidation-side definitions.

### 4.2 LeverageState

```text
oi_native
oi_usd_or_quote_validated
oi_change
oi_velocity
oi_acceleration
oi_percentile
oi_change_vs_price
oi_change_vs_volume
leverage_expansion_flag
leverage_compression_flag
cross_venue_oi_dispersion
```

No claim that OI equals leverage amount; OI is a leverage-state proxy/coordinate.

### 4.3 FundingState

```text
funding_native
funding_normalized_interval
funding_percentile
funding_change
funding_velocity
funding_dispersion
funding_extreme_breadth
funding_sign_consensus
```

Realized, predicted and indicative funding remain distinct.

### 4.4 OrderFlowState

```text
taker_buy_notional
taker_sell_notional
signed_aggressor_flow
taker_imbalance
cvd
cvd_velocity
flow_persistence
flow_breadth
flow_consensus
flow_dispersion
```

Aggressor semantics inherit Bloc 5 provider-specific fixture validation.

### 4.5 LiquidityState

```text
spread_bps
depth_bid_5bps
depth_ask_5bps
depth_bid_10bps
depth_ask_10bps
depth_bid_25bps
depth_ask_25bps
depth_bid_50bps
depth_ask_50bps
book_imbalance
slippage_buy
slippage_sell
depth_withdrawal
spread_expansion
liquidity_recovery
```

Do not compare raw level counts across venues as though they have equal economics.

### 4.6 PositioningState

```text
long_short_ratio_native
account_ratio_native
position_ratio_native
ratio_percentile
ratio_change
positioning_dispersion
```

Provider-native methodologies must remain visible.

### 4.7 BasisState

```text
basis_native
basis_bps
basis_percentile
basis_change
basis_curve_slope_where_available
basis_dispersion
```

No cross-contract basis comparison without economic-contract compatibility.

---

## 5. Observable classes

Each T2 value receives a class:

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

This prevents a raw T1-derived number and a learned classification from looking equally direct.

---

## 6. Static + rolling temporal protocol

Whenever a temporal observable is defined, implementation must support both static horizon views and rolling-window views where the source frequency allows it.

Frozen default research horizons:

```text
STATIC / EVENT HORIZONS
1D / 3D / 7D / 14D / 30D / 60D

ROLLING WINDOWS
3D / 7D / 14D / 30D
+ 60D when support is adequate
```

Intraday mechanical states may additionally support:

```text
1m / 5m / 15m / 1h / 4h / 12h
```

but these do not replace static+rolling multi-day protocol for research comparisons.

Window outputs must record:

```text
window_type
window_length
min_required_coverage
actual_coverage
sample_count
quality_mode
```

---

## 7. Baseline / normalization doctrine

No universal z-score is assumed.

Permitted baselines include:

```text
rolling empirical percentile
rolling robust z / MAD-style standardization
expanding historical percentile where PIT-safe
venue-local seasonal baseline
cross-sectional PIT baseline
```

Every standardized value must retain physical amplitude alongside normalized amplitude whenever economically possible.

Example:

```text
liq_usd = $28m
liq_sigma = 2.1
liq_percentile = 96.4
```

The system may not let `2.1σ` erase the fact that physical size is only `$28m`.

---

## 8. Quality gating

Bloc 6 provides T2 eligibility.

A T2 calculation must record:

```text
input_quality_mode
eligible_source_ids
excluded_source_ids
independence_groups
comparability_classes
coverage_fraction
quality_flags
```

If the required source semantics are blocked, the T2 result is:

```text
DATA_BLOCKED
```

not a guessed proxy unless the observable methodology explicitly defines a proxy and labels it as such.

---

## 9. Versioned observable specifications

Every T2 observable has a registry entry:

```text
observable_id
observable_family
version
status
input_schema_versions
required_fields
allowed_quality_modes
window_definition
normalization_method
aggregation_method
output_schema
valid_region
invalid_region
methodology_notes
```

Statuses:

```text
DRAFT
RESEARCH_EXPERIMENTAL
VALIDATED_LOCAL
VALIDATED_CROSS_VENUE
PROMOTED_RUNTIME
DEPRECATED
BLOCKED
```

No formula may silently change under the same version.

---

## 10. Required T2 lineage

Every T2 row must trace to:

```text
T2 observable
  ↓
T2 methodology version
  ↓
T1 observation IDs / partition refs
  ↓
T1 generation
  ↓
T0 acquisition/evidence lineage
```

Cross-venue T2 must additionally trace:

```text
SourceDependencyGraph version
Bloc 6 policy version
quorum/eligibility decision
weighting method
```

---

## 11. Storage model

T2 output target:

```text
Parquet analytical store
DuckDB discovery/query
PostgreSQL metadata/spec registry only
```

Suggested partition keys:

```text
observable_family
observable_id
version
scope_type          # venue / cross_venue
canonical_asset
granularity
year/month/day
```

Do not place giant T2 time series in PostgreSQL.

---

## 12. In scope

- venue-local state calculations;
- cross-venue breadth/consensus/dispersion;
- normalized + physical representations;
- static+rolling windows;
- quality-gated computation;
- versioned methodologies;
- PIT-safe state computation;
- full lineage;
- historical and live parity.

## 13. Out of scope

- alpha scoring;
- opportunity ranking;
- directional prediction;
- strategy rules;
- portfolio sizing;
- execution;
- live order placement;
- ML models whose target is future return/PnL.

---

## 14. Core implementation objects

```text
ObservableSpec
ObservableInputContract
ObservableWindow
ObservableComputationContext
ObservableValue
VenueMechanicalState
CrossVenueMechanicalState
ObservableLineage
ObservableQualityEnvelope
ObservableGeneration
ObservableRegistry
```

---

## 15. Bloc 9 success condition

Bloc 9 succeeds when the system can compute the same mechanical state definition over:

```text
historical T1
and
live T1
```

and produce equivalent schema/semantics, explicit quality, deterministic lineage, and no provider-specific research coupling.

`human_review_required = TRUE`
