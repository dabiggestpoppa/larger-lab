# BLOC 5 — SENSOR-SPECIFIC NORMALIZATION RULES

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Purpose:** define provider-independent T1 normalization semantics for the canonical mechanical sensor families without collapsing venue-specific meaning.

---

## 1. Scope

This document covers:

```text
MECHANICAL_TRADE
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT
MECHANICAL_BOOK_METRIC
MECHANICAL_POSITIONING
MECHANICAL_BASIS
```

The output is T1 canonical observation data.

No cross-venue synthesis or research-state features are created here.

---

# 2. MECHANICAL_TRADE

## 2.1 Canonical fields

```text
trade_id_provider optional
provider_sequence_id optional
price_native
price_canonical optional
quantity_native
quantity_native_unit
quantity_base optional
notional_quote optional
notional_usd optional
buyer_side optional
seller_side optional
aggressor_side
maker_side optional
trade_flags
```

### `aggressor_side`

Allowed:

```text
BUY
SELL
UNKNOWN
```

Aggressor means the side crossing/resting liquidity according to provider semantics.

It must not be inferred from price direction.

## 2.2 Binance example

For Binance-style `isBuyerMaker` semantics:

```text
isBuyerMaker = true
→ buyer is maker
→ seller is taker/aggressor
→ aggressor_side = SELL

isBuyerMaker = false
→ buyer is taker/aggressor
→ aggressor_side = BUY
```

This mapping gets its own methodology ID and fixture tests.

Do not duplicate this logic in research code.

## 2.3 Trade duplicates

Prefer provider trade ID/sequence when available.

Do not dedupe trades across venues.

REST/archive/live duplication for the same venue is handled by the duplicate policy later in this bloc.

---

# 3. MECHANICAL_LIQUIDATION

Liquidation semantics are especially easy to corrupt.

The system must keep separate:

```text
position_side_liquidated
execution_side
aggressor_side optional
maker_taker_liquidation_role optional
```

## 3.1 Position side

Allowed:

```text
LONG
SHORT
UNKNOWN
```

A long liquidation generally requires sell execution, but the system must not encode this as the only representation.

Keep both:

```text
position_side_liquidated = LONG
execution_side = SELL
```

where provider evidence supports both.

## 3.2 Deribit liquidation flags

Deribit-style maker/taker liquidation roles should remain explicit, e.g. conceptually:

```text
MAKER_LIQUIDATED
TAKER_LIQUIDATED
BOTH_LIQUIDATED
```

This is richer than simple long/short aggregate liquidation volume and should remain available for mechanism work.

## 3.3 Canonical fields

```text
liquidation_event_id optional
position_side_liquidated
execution_side
maker_taker_role optional
quantity_native
quantity_native_unit
quantity_base optional
liquidation_quote_notional optional
liquidation_usd optional
price_native optional
price_reference optional
count optional
aggregation_scope
```

`aggregation_scope`:

```text
TRADE_LEVEL
EVENT_LEVEL
INTERVAL_AGGREGATE
PROVIDER_MULTI_EVENT_AGGREGATE
UNKNOWN
```

## 3.4 Long/short aggregate fields

Provider fields such as `long_liq_usd` and `short_liq_usd` map to the **position side liquidated**, not buy/sell aggressor flow.

This distinction is mandatory.

## 3.5 Zero intervals

A zero liquidation interval is permitted only when:

- provider reports completed intervals including zero activity; and
- interval coverage is verified.

No missing interval becomes zero.

---

# 4. MECHANICAL_OPEN_INTEREST

OI is a stock/snapshot quantity, not a flow.

## 4.1 Canonical fields

```text
oi_native_value
oi_native_unit
oi_contracts optional
oi_base optional
oi_quote optional
oi_usd optional
snapshot_or_interval
reference_price_ref optional
```

`snapshot_or_interval`:

```text
POINT_SNAPSHOT
INTERVAL_LAST
INTERVAL_AVERAGE
PROVIDER_AGGREGATE
UNKNOWN
```

## 4.2 Do not confuse OI units

Provider OI may be reported in:

```text
contracts
base asset
quote currency
USD-like notional
provider-specific units
```

T1 preserves native.

Conversions depend on contract terms.

## 4.3 OI USD conversion

For linear contracts:

- use verified contract-size semantics;
- use PIT-valid price if needed.

For inverse contracts:

- use the contract's documented inverse exposure formula;
- record price reference and methodology.

No universal formula across all venues.

## 4.4 Aggregator OI

If Coinalyze or another aggregator provides venue-specific OI, store provider and venue separately.

If it reports multi-venue aggregate OI, do not assign it to one venue.

---

# 5. MECHANICAL_FUNDING

Funding requires both **rate semantics** and **interval semantics**.

## 5.1 Native fields

```text
funding_rate_native
funding_rate_unit
funding_interval_seconds optional
funding_period_start_at optional
funding_period_end_at optional
published_at optional
effective_at optional
predicted_or_realized
```

`predicted_or_realized`:

```text
REALIZED
PREDICTED
INDICATIVE
UNKNOWN
```

Predicted funding must never overwrite realized funding.

## 5.2 Normalized equivalents

Optional comparable fields:

```text
funding_rate_per_8h_simple_equiv
funding_rate_per_day_simple_equiv
```

only if the native rate/interval structure supports the transform.

Annualized funding belongs in later analytical layers unless required for a specific canonical view.

## 5.3 Simple vs compounded

Do not silently annualize with arbitrary compounding.

If equivalent transformations exist, the methodology ID must state whether conversion is:

```text
SIMPLE_LINEAR
COMPOUNDED
```

T1 defaults to preserving native rate plus simple comparable interval equivalents.

---

# 6. MECHANICAL_BOOK_SNAPSHOT

Full books are high-volume evidence and require exact side/level semantics.

## 6.1 Canonical snapshot fields

```text
snapshot_id
provider_sequence optional
bids[]
asks[]
best_bid optional
best_ask optional
snapshot_depth_levels optional
is_full_snapshot
update_semantics
```

Each level:

```text
side
price_native
quantity_native
quantity_native_unit
quantity_base optional
quote_notional optional
```

## 6.2 Snapshot vs delta

Allowed:

```text
FULL_SNAPSHOT
DELTA_UPDATE
PARTIAL_SNAPSHOT
TOP_OF_BOOK
UNKNOWN
```

Delta updates cannot be treated as standalone complete books unless reconstructed through verified sequence logic.

Book reconstruction implementation must fail on sequence gaps rather than silently continue.

## 6.3 Cross-provider bps depth

Depth at ±5/10/25/50 bps is a later common metric unless directly supplied as provider-native analytics.

T1 stores normalized levels and provider-native book metrics.

Bloc 9 derives common liquidity metrics from canonical levels.

---

# 7. MECHANICAL_BOOK_METRIC

Some providers expose native analytics:

- spread;
- liquidity;
- slippage;
- orderbook depth;
- imbalance.

Canonical fields:

```text
metric_name_native
metric_value_native
metric_unit_native
provider_methodology_ref optional
canonical_metric_family optional
semantic_equivalence_class
```

Policy:

> Provider-native liquidity/slippage scores are T1 evidence, not automatically equivalent to Fabric-defined LiquidityState metrics.

If exact methodology is undocumented, classify as `CORROBORATION_ONLY` or `NOT_COMPARABLE`.

---

# 8. MECHANICAL_POSITIONING

Positioning ratios are heterogeneous.

Examples:

- account long/short ratio;
- top-trader account ratio;
- top-trader position ratio;
- taker buy/sell ratio;
- retail ratio;
- provider aggregate.

These cannot share one generic `long_short_ratio` field without a population definition.

Canonical fields:

```text
positioning_metric_type
numerator_definition
denominator_definition
population_scope
value_native
unit
interval_semantics
```

Initial metric types:

```text
ACCOUNT_LONG_SHORT_RATIO
TOP_TRADER_ACCOUNT_RATIO
TOP_TRADER_POSITION_RATIO
TAKER_BUY_SELL_RATIO
PROVIDER_DEFINED_RATIO
```

---

# 9. MECHANICAL_BASIS

Basis fields need reference identity.

Canonical:

```text
basis_value_native
basis_unit
spot_reference
futures_reference
annualization_method optional
expiry optional
provider_methodology_ref
```

Possible units:

```text
ABSOLUTE_PRICE
PERCENT
BPS
ANNUALIZED_PERCENT
```

Never compare an annualized basis with a raw percentage basis without explicit transformation.

---

# 10. Cross-sensor identity links

When economically useful, T1 records may reference related contemporaneous observations, but should not fuse them.

Examples:

```text
OI conversion → reference price observation
liquidation USD conversion → reference price/FX observation
funding → contract instance
book quantity conversion → contract terms
```

These are lineage links, not T2 features.

---

# 11. Provider-specific side mapping registry

Every provider requiring side interpretation gets a versioned mapping.

Example config:

```yaml
binance_usdm:
  trade:
    isBuyerMaker:
      true: SELL_AGGRESSOR
      false: BUY_AGGRESSOR
```

Gate liquidation fields may explicitly identify long/short liquidated positions.

Deribit liquidation flags preserve maker/taker roles.

No provider side convention is assumed globally.

---

# 12. Quantity normalization guardrails

For every sensor:

- preserve raw quantity;
- preserve unit;
- resolve contract terms at event time;
- use PIT-valid reference price only when needed;
- record conversion input;
- leave normalized field null if conversion cannot be defended.

Do not make a row unusable merely because USD normalization is blocked when the native quantity is still valid.

---

# 13. Aggregated interval semantics

For interval data, retain:

```text
aggregation_function
aggregation_window
aggregation_population
```

Allowed examples:

```text
SUM
LAST
MEAN
MEDIAN
MAX
MIN
PROVIDER_DEFINED
```

If provider documentation does not reveal the aggregation function:

```text
aggregation_function = PROVIDER_DEFINED
semantic_equivalence_class <= CORROBORATION_ONLY
```

unless independent evidence justifies more.

---

# 14. No cross-venue synthesis at T1

T1 output remains venue/provider scoped.

No:

```text
market_liquidations = Kraken + Gate + Binance
```

inside normalization.

That belongs to Bloc 9 after Bloc 6 quality/redundancy rules are available.

---

# 15. Required implementation modules

```text
normalization/sensors/
  trades.py
  liquidations.py
  open_interest.py
  funding.py
  books.py
  book_metrics.py
  positioning.py
  basis.py
  provider_side_maps.py
```

Each module implements a common normalizer protocol and is offline-fixture testable.

---

# 16. Blocking semantic errors

Examples:

```text
AGGRESSOR_SIDE_UNVERIFIED
LIQUIDATION_POSITION_SIDE_UNVERIFIED
OI_UNIT_UNVERIFIED
FUNDING_INTERVAL_UNVERIFIED
BOOK_SEQUENCE_GAP
POSITIONING_POPULATION_UNVERIFIED
BASIS_REFERENCE_UNVERIFIED
```

These do not delete source evidence. They downgrade/block specific canonical fields.

---

# 17. Sensor invariants

1. trade aggressor side never inferred from price direction;
2. liquidation position side and execution side remain separate;
3. OI remains a stock/snapshot object;
4. predicted funding never masquerades as realized funding;
5. book deltas require sequence-safe reconstruction before full-book claims;
6. positioning ratios retain population semantics;
7. basis retains reference and units;
8. native values remain available even when normalized values are blocked.

---

# 18. Handoff

The next Bloc 5 document defines **T1 lineage, duplicates, revisions, quality, storage generations, and canonical query behavior**.
