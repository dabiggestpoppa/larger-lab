# BLOC 9 — CROSS-VENUE BREADTH, CONSENSUS & DISPERSION

## 1. Purpose

Define how venue-local T2A states become cross-venue T2B mechanical states without erasing venue heterogeneity or double-counting dependent sources.

---

## 2. Eligibility first

Cross-venue calculations consume Bloc 6 `T2Eligibility` decisions.

Each candidate contributor must provide:

```text
source_id
venue
independence_group
comparability_class
quality_mode
coverage
allowed_operations
```

Only operations explicitly permitted by Bloc 6 may be executed.

---

## 3. Three distinct cross-venue objects

The fabric freezes three primary synthesis families.

### 3.1 Breadth

Question:

> How widespread is the condition?

Examples:

```text
fraction of independent venues with elevated liquidations
fraction with OI compression
fraction with negative funding
fraction with sell-aggressor dominance
fraction with depth withdrawal
```

Breadth is usually less sensitive to scale differences than notional sums.

### 3.2 Consensus

Question:

> How aligned are independent venues on sign/state?

Examples:

```text
flow sign consensus
funding sign consensus
OI expansion/compression consensus
liquidity withdrawal consensus
```

Consensus is not majority truth. It is an observed alignment statistic.

### 3.3 Dispersion

Question:

> How heterogeneous are venues?

Examples:

```text
OI change dispersion
funding dispersion
liquidation intensity dispersion
spread/depth dispersion
flow imbalance dispersion
```

High dispersion may itself be a useful state and must never be automatically treated as bad data.

---

## 4. Independence-aware counting

If multiple sources share one upstream origin, strict breadth/quorum counts the independence group once unless methodology explicitly uses provider-reported secondary corroboration.

Example:

```text
Binance native OI
Bybit native OI
Coinalyze aggregate containing Binance+Bybit
```

Strict independent count:

```text
2
```

not 3.

The third source can still be retained as corroboration evidence.

---

## 5. CrossVenueLiquidationState

Candidate coordinates:

```text
independent_venue_count
liq_breadth_elevated
liq_breadth_extreme
long_liq_breadth
short_liq_breadth
liq_intensity_median
liq_intensity_p75
liq_intensity_p90
liq_intensity_dispersion
liq_concentration_top_venue
venue_locality_score
```

Notional sums are allowed only when:

- units are normalized with PIT-valid conversion;
- contracts are semantically compatible for the operation;
- double counting is controlled;
- methodology is explicit.

Otherwise use breadth/distributional summaries.

---

## 6. CrossVenueLeverageState

Candidate coordinates:

```text
oi_expansion_breadth
oi_compression_breadth
oi_change_median
oi_change_p25/p75
oi_change_dispersion
price_oi_quadrant_breadth
venue_leverage_rotation
```

Potential descriptive state labels:

```text
BROAD_EXPANSION
BROAD_COMPRESSION
MIXED_ROTATION
VENUE_LOCAL_EXPANSION
VENUE_LOCAL_COMPRESSION
```

No label implies future return direction.

---

## 7. CrossVenueFundingState

Candidate coordinates:

```text
positive_funding_breadth
negative_funding_breadth
extreme_positive_breadth
extreme_negative_breadth
funding_consensus
funding_median_percentile
funding_dispersion
```

Because funding methodologies/intervals differ, normalized percentile/state comparisons may be safer than raw summation.

---

## 8. CrossVenueOrderFlowState

Candidate coordinates:

```text
buy_aggressor_breadth
sell_aggressor_breadth
flow_sign_consensus
signed_flow_standardized_median
flow_dispersion
flow_concentration
```

Where notional comparability is strong, optional cross-venue signed notional may be computed. Otherwise distributional summaries dominate.

---

## 9. CrossVenueLiquidityState

Candidate coordinates:

```text
spread_expansion_breadth
depth_withdrawal_breadth
liquidity_recovery_breadth
depth_change_median
depth_change_dispersion
spread_dispersion
slippage_dispersion
```

A key research object:

```text
LIQUIDITY_WITHDRAWAL_BREADTH
```

This is explicitly separate from price movement.

---

## 10. CrossVenuePositioningState / BasisState

Because provider methodologies differ, these default to:

```text
CORROBORATION / DISTRIBUTIONAL MODE
```

unless Bloc 6 marks exact/normalizable comparability.

Candidate outputs:

```text
positioning_extreme_breadth
positioning_dispersion
basis_sign_breadth
basis_dispersion
basis_extreme_breadth
```

---

## 11. Market-wide mechanical composite objects

Bloc 9 may expose **separate** high-level descriptive objects:

```text
MechanicalBreadth
VenueDispersion
LeverageCompression
LiquidationBreadth
FlowConsensus
LiquidityWithdrawalBreadth
FundingConsensus
```

But it must NOT create one opaque universal `MechanicalStressScore` in v1.

Reason:

The project has repeatedly found parallel constraints/equifinality. A single master scalar would destroy useful structure before research earns compression.

---

## 12. Distribution-first reporting

Preferred cross-venue summary order:

```text
n independent venues
coverage
breadth
median
p25/p75
p90 where supported
dispersion
concentration
contributors
```

Avoid mean-only reporting when venue distributions are skewed.

---

## 13. Dynamic source sets

Cross-venue state must tolerate changing contributors through time.

Each row stores:

```text
eligible_set_hash
actual_contributor_set
independence_group_count
excluded_source_reasons
```

A 2021 state with 2 venues and a 2026 state with 6 venues are not silently assumed to have equal measurement depth.

---

## 14. Missing contributor behavior

A missing venue does not become zero.

Breadth denominator may use only expected+eligible contributors under a versioned policy.

The output must record both:

```text
observed_breadth
coverage_fraction
```

so 2/2 and 2/6 never look identical.

---

## 15. Disagreement as state

Bloc 6 distinguishes likely data divergence from valid economic heterogeneity.

Bloc 9 preserves valid heterogeneity as observables such as:

```text
VENUE_DISPERSION
VENUE_CONCENTRATION
VENUE_LOCALITY
```

This is a feature, not a cleanup problem.

---

## 16. Frozen rule

Cross-venue synthesis may compress **measurements**, but it may not erase the original venue-local states or source membership used to create them.
