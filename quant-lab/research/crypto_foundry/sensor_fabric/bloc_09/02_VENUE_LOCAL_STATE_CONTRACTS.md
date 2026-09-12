# BLOC 9 — VENUE-LOCAL MECHANICAL STATE CONTRACTS

## 1. Purpose

Freeze how T1 observations become venue-local T2A states before any cross-venue synthesis occurs.

Venue-local state is the safest place to begin because it preserves the actual mechanics of the venue and contract.

---

## 2. VenueMechanicalState envelope

Every venue-local state carries:

```text
state_id
observable_family
observable_version
provider
venue
contract_instance_id
canonical_asset
instrument_type
settlement_asset
granularity
window_type
window_start
window_end
as_of
input_generation
quality_mode
coverage_fraction
source_count
physical_values
normalized_values
state_labels
quality_flags
lineage_ref
```

No field may erase native venue identity.

---

## 3. LiquidationState local contract

Inputs may include interval liquidation totals, individual liquidation-tagged trades, provider liquidation events, or provider analytics.

Required semantic fields where available:

```text
long_liq_notional_native
short_liq_notional_native
long_liq_usd_validated
short_liq_usd_validated
liq_event_count
maker_liquidation_count
taker_liquidation_count
```

Derived candidates:

```text
total_liq
liq_imbalance = directional asymmetry under canonical side semantics
liq_intensity_vs_oi
liq_intensity_vs_turnover
liq_velocity
liq_acceleration
liq_burst_index
liq_percentile
liq_sigma_robust
liq_persistence
```

State labels may include descriptive tags such as:

```text
QUIET
ELEVATED
BURST
CASCADE_LOCAL
RECOVERY
```

but thresholds must be versioned, empirical, and research-validated. They are not trading triggers.

---

## 4. LeverageState local contract

Inputs:

```text
OI native
OI base if provider supports
OI quote/USD if provider supports or PIT-valid conversion exists
price reference
turnover/volume where used
```

Derived candidates:

```text
oi_change_abs
oi_change_pct
oi_velocity
oi_acceleration
oi_percentile
oi_robust_sigma
price_return_same_window
oi_price_quadrant
```

Descriptive quadrant labels:

```text
PRICE_UP_OI_UP
PRICE_UP_OI_DOWN
PRICE_DOWN_OI_UP
PRICE_DOWN_OI_DOWN
```

These are observed state relations, not future-direction predictions.

---

## 5. FundingState local contract

Inputs must preserve:

```text
funding_type
native_rate
native_interval
realized/predicted/indicative status
```

Derived candidates:

```text
normalized_8h_equivalent  # only when mathematically/semantically defensible
funding_percentile
funding_robust_sigma
funding_change
funding_velocity
funding_persistence
```

Do not annualize and then treat annualized funding as physical cash actually paid. Annualization is contextual only.

---

## 6. OrderFlowState local contract

Inputs:

```text
trades or aggTrades
aggressor/taker side
notional
trade count
provider CVD where semantically verified
```

Derived candidates:

```text
taker_buy_notional
taker_sell_notional
signed_aggressor_notional
taker_imbalance
cvd
cvd_change
cvd_velocity
flow_persistence
large_trade_share where threshold method is versioned
```

If aggressor side is not safely known:

```text
ORDER_FLOW_SIGN_BLOCKED
```

No guessed sign.

---

## 7. LiquidityState local contract

Preferred economically normalized coordinates:

```text
spread_bps
bid_depth_5bps
ask_depth_5bps
bid_depth_10bps
ask_depth_10bps
bid_depth_25bps
ask_depth_25bps
bid_depth_50bps
ask_depth_50bps
book_imbalance_10bps
book_imbalance_25bps
```

Optional executable-slippage coordinates:

```text
buy_slippage_bps_{size_bucket}
sell_slippage_bps_{size_bucket}
```

Size buckets must be contract-aware and versioned. Absolute `$10k` may be useful for BTC/ETH but meaningless for some long-tail contracts; percentile/liquidity-relative buckets may be needed.

Derived candidates:

```text
depth_change
depth_withdrawal_rate
spread_change
spread_expansion
book_imbalance_change
liquidity_recovery_rate
```

A reconstructed full book and provider-native analytics must remain separately typed.

---

## 8. PositioningState local contract

Provider positioning ratios are methodology-sensitive.

Each state retains:

```text
ratio_type
population_definition
provider_methodology_id
native_ratio
```

Derived candidates:

```text
ratio_percentile
ratio_change
ratio_velocity
ratio_extreme_flag
```

No cross-provider arithmetic before Bloc 9 comparability permission.

---

## 9. BasisState local contract

Inputs:

```text
perp/future reference
spot/index/reference price
contract maturity if dated future
provider basis analytics where available
```

Derived:

```text
basis_native
basis_bps
basis_change
basis_percentile
curve_slope where multiple maturities valid
```

Perpetual basis and dated-future annualized basis are not automatically identical objects.

---

## 10. Multi-horizon local states

The same venue state may be emitted across multiple horizons:

```text
5m
15m
1h
4h
12h
1D
3D
7D
14D
30D
60D
```

Only horizons supported by source frequency/coverage may be produced.

No resampling that implies precision the source did not have.

---

## 11. Physical + standardized pairing

Whenever standardization is used, persist:

```text
physical_value
standardized_value
baseline_id
baseline_window
baseline_sample_count
```

A normalized extreme without its physical scale is incomplete.

---

## 12. Null / blocked behavior

Venue state computation returns typed non-values:

```text
NO_DATA_EXPECTED
DATA_GAP
INSUFFICIENT_COVERAGE
SEMANTIC_BLOCKED
IDENTITY_BLOCKED
PIT_BLOCKED
QUALITY_BLOCKED
METHODOLOGY_BLOCKED
```

Never convert these to zeros.

---

## 13. Venue-local validation

For each state family, implementation tests must include:

- quiet interval;
- stressed interval;
- valid zero;
- sparse interval;
- provider gap;
- insufficient baseline;
- contract migration/listing boundary;
- stablecoin conversion stress where relevant;
- historical/live equivalence.

---

## 14. Frozen rule

Cross-venue state construction is forbidden until venue-local states pass lineage, semantics, coverage and quality gates.
