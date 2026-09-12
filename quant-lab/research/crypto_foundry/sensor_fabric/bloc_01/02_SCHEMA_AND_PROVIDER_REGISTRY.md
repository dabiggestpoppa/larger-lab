# BLOC 1 — CANONICAL SCHEMAS & PROVIDER REGISTRY

**Status:** implementation-grade specification  
**Depends on:** `01_BLOC_01_CONTRACTS_AND_SEMANTICS.md`  

---

## 1. Purpose

This document turns the Bloc 1 semantics into concrete schema contracts that later implementation code must follow.

The execution agent may choose exact Python module names within the planned tree, but may not alter field meaning without human review.

---

## 2. Common base observation

All T1 canonical observations inherit the following logical base.

```yaml
CanonicalObservationBase:
  observation_id: string
  sensor_family: enum
  provider: string
  venue: string
  evidence_class: enum
  retrieval_mode: enum

  instrument_native: string
  instrument_id_canonical: string | null
  market_type: enum
  base_asset: string | null
  quote_asset: string | null
  settlement_asset: string | null
  contract_type: enum | null
  contract_multiplier: float | null
  is_inverse: bool | null

  effective_at: datetime
  observed_at: datetime
  ingested_at: datetime
  window_start: datetime | null
  window_end: datetime | null
  source_interval: string | null

  endpoint_id: string
  source_record_id: string | null
  raw_object_uri: string
  raw_checksum: string

  access_class: enum
  semantic_equivalence: enum
  quality_flags: list[enum]

  adapter_version: string
  schema_version: string
  identity_version: string
  normalization_version: string
  methodology_version: string
```

### Required invariants

- `ingested_at >= observed_at` is expected for live ingestion, but historical backfills may have modern ingestion after old observed/effective timestamps.
- `effective_at <= observed_at` unless the provider explicitly publishes future-effective information such as an announced funding event; exceptions require methodology documentation.
- `raw_object_uri` and `raw_checksum` are always populated for persisted T1 records.
- `instrument_native` never null.
- canonical asset fields may be null when identity resolution fails; quality flag must explain why.

---

## 3. ProviderEnvelope schema

```yaml
ProviderEnvelope:
  envelope_id: string
  provider: string
  venue_hint: string | null
  sensor_family_hint: enum
  endpoint_id: string
  request_id: string | null
  retrieval_mode: REST | WS | BULK_FILE | COMMUNITY_ARCHIVE
  request_started_at: datetime
  response_received_at: datetime
  source_symbol: string | null
  source_interval: string | null
  requested_start: datetime | null
  requested_end: datetime | null
  raw_object_uri: string
  raw_checksum: string
  http_status: int | null
  access_class: enum
  adapter_version: string
  quality_flags: list[enum]
  source_metadata: dict
```

`ProviderEnvelope` is storage/provenance metadata around raw source content, not a canonical market observation itself.

---

## 4. MechanicalTrade schema

```yaml
MechanicalTrade:
  base: CanonicalObservationBase
  trade_id: string | null
  price_native: decimal
  quantity_native: decimal
  quantity_unit: string
  quote_notional_native: decimal | null
  quote_notional_usd: decimal | null
  aggressor_side: BUY | SELL | UNKNOWN
  maker_side: BUY | SELL | UNKNOWN
  aggregation_type: INDIVIDUAL | AGGREGATED
  source_trade_count: int | null
```

### Side rule

A provider's maker/taker boolean is not accepted until a provider fixture test proves the mapping.

No global assumption such as `isBuyerMaker=false => aggressive buy` may exist outside the provider-specific semantics module.

---

## 5. MechanicalLiquidation schema

```yaml
MechanicalLiquidation:
  base: CanonicalObservationBase
  event_shape: TRADE_LEVEL | INTERVAL_AGGREGATE | TOTAL_AGGREGATE
  liquidation_side: LONG | SHORT | BOTH | UNKNOWN
  liquidation_role: MAKER | TAKER | BOTH | UNKNOWN
  price_native: decimal | null
  quantity_native: decimal | null
  quantity_unit: string | null
  liquidation_quote_native: decimal | null
  liquidation_usd: decimal | null
  liquidation_count: int | null
  source_long_liq_native: decimal | null
  source_short_liq_native: decimal | null
  source_long_liq_usd: decimal | null
  source_short_liq_usd: decimal | null
```

### Non-equivalence rule

A trade-level liquidation record is not numerically merged with a provider's interval aggregate before T2 aggregation.

---

## 6. MechanicalOpenInterest schema

```yaml
MechanicalOpenInterest:
  base: CanonicalObservationBase
  oi_native: decimal
  native_unit: CONTRACTS | BASE_ASSET | QUOTE_ASSET | USD | OTHER
  oi_base: decimal | null
  oi_quote: decimal | null
  oi_usd: decimal | null
  mark_price_used: decimal | null
  index_price_used: decimal | null
  conversion_timestamp: datetime | null
  normalization_method: string | null
```

### Required invariant

If `oi_usd` is derived from a price external to the OI payload, provenance for the price source must be recorded in methodology/source metadata.

---

## 7. MechanicalFunding schema

```yaml
MechanicalFunding:
  base: CanonicalObservationBase
  funding_rate_native: decimal
  funding_interval_seconds: int | null
  funding_rate_8h_equivalent: decimal | null
  annualized_context: decimal | null
  predicted_or_realized: REALIZED | PREDICTED | UNKNOWN
```

No derived equivalent may replace native funding.

---

## 8. MechanicalBookSnapshot schema

```yaml
MechanicalBookSnapshot:
  base: CanonicalObservationBase
  best_bid: decimal | null
  best_ask: decimal | null
  bids: list[PriceLevel] | null
  asks: list[PriceLevel] | null
  provider_level_count: int | null
  source_depth_definition: string
  is_full_depth: bool
  sequence_id: string | null
```

```yaml
PriceLevel:
  price: decimal
  quantity: decimal
  quantity_unit: string
```

If provider exposes only aggregate book analytics rather than levels, use `MechanicalBookMetric`, not fake snapshots.

---

## 9. MechanicalBookMetric schema

```yaml
MechanicalBookMetric:
  base: CanonicalObservationBase
  metric_name: string
  metric_value: decimal
  metric_unit: string
  side: BID | ASK | BOTH | NONE
  distance_bps: decimal | null
  trade_notional_usd: decimal | null
  methodology_id: string
```

Initial canonical metric names:

```text
SPREAD_BPS
DEPTH_BID_5BPS
DEPTH_ASK_5BPS
DEPTH_BID_10BPS
DEPTH_ASK_10BPS
DEPTH_BID_25BPS
DEPTH_ASK_25BPS
DEPTH_BID_50BPS
DEPTH_ASK_50BPS
BOOK_IMBALANCE_10BPS
BOOK_IMBALANCE_25BPS
SLIPPAGE_BUY_10K_USD
SLIPPAGE_SELL_10K_USD
SLIPPAGE_BUY_100K_USD
SLIPPAGE_SELL_100K_USD
```

Not all metrics are required for all instruments. Missing support is explicit.

---

## 10. MechanicalPositioning schema

```yaml
MechanicalPositioning:
  base: CanonicalObservationBase
  positioning_metric: enum
  long_value: decimal | null
  short_value: decimal | null
  ratio_value: decimal | null
  population_definition: string
```

Initial metric enum examples:

```text
GLOBAL_LONG_SHORT_RATIO
TOP_TRADER_ACCOUNT_RATIO
TOP_TRADER_POSITION_RATIO
TAKER_LONG_SHORT_RATIO
USER_LONG_SHORT_RATIO
```

Do not equate different populations.

---

## 11. MechanicalBasis schema

```yaml
MechanicalBasis:
  base: CanonicalObservationBase
  basis_native: decimal
  basis_bps: decimal | null
  reference_price: decimal | null
  reference_type: SPOT | INDEX | MARK | OTHER
  tenor_seconds: int | null
```

---

## 12. Provider registry schema

Planned config path:

`config/crypto_sensor_fabric/provider_registry.yaml`

Top-level logical shape:

```yaml
providers:
  KRAKEN_FUTURES:
    evidence_class: FIRST_PARTY_EXCHANGE
    status: CANDIDATE
    access:
      access_class: UNVERIFIED
      verified_at: null
      cost_usd_required: 0
      payment_method_required: false
      staking_required: false
      transaction_required: false
      api_key_required: null
      terms_reference: null
    capabilities:
      liquidations:
        claimed: true
        verified: false
        equivalence_default: NORMALIZABLE_COMPARABLE
      open_interest:
        claimed: true
        verified: false
      funding:
        claimed: true
        verified: false
      order_flow:
        claimed: true
        verified: false
      order_book:
        claimed: true
        verified: false
    fallback_candidates:
      liquidations: [GATE_FUTURES, DERIBIT, COINALYZE]
      open_interest: [GATE_FUTURES, BYBIT_LINEAR, BINANCE_USDM]
```

Bloc 1 does not mark historical access verified. Bloc 2 capability probes do that.

---

## 13. Initial provider candidate registry

The following candidate map should be encoded, with all historical capability flags initially false until probed.

### Kraken Futures

Planned capability candidates:
- liquidations
- OI
- funding
- aggressor differential/CVD
- orderbook analytics
- spreads
- liquidity
- slippage
- basis

Evidence class: `FIRST_PARTY_EXCHANGE`.

### Gate Futures

Candidates:
- long/short liquidation aggregates
- OI
- taker long/short flow
- funding / positioning

Evidence class: `FIRST_PARTY_EXCHANGE`.

### Binance USD-M

Candidates:
- raw trades / aggTrades
- funding
- OI/metrics
- taker flow reconstruction
- book-depth archives/metrics

Historical liquidation should begin as `UNVERIFIED_OR_UNAVAILABLE`, not assumed.

### Bybit

Candidates:
- OI
- funding
- historical trades
- live/public orderbook

### OKX

Candidates:
- historical trades
- funding
- historical orderbook modules
- book reconstruction

### Deribit

Candidates:
- individual trades
- liquidation-tagged trades
- funding
- book/current microstructure

### Coinalyze

Candidates:
- OI
- funding
- liquidations
- ratios

Evidence class: `THIRD_PARTY_AGGREGATOR`.

Never canonical sole provider when first-party alternatives exist.

### Bitfinex liquidation archive

Candidates:
- historical liquidation replication

Evidence class: `COMMUNITY_ARCHIVE`.

Never promoted to first-party truth.

---

## 14. Sensor priority registry

Planned config:

`config/crypto_sensor_fabric/sensor_priority.yaml`

```yaml
critical:
  LIQUIDATION_STATE:
    min_preferred_sources: 2
    source_priority:
      - KRAKEN_FUTURES
      - GATE_FUTURES
      - DERIBIT
      - COINALYZE
      - BITFINEX_COMMUNITY

  OPEN_INTEREST_STATE:
    min_preferred_sources: 2
    source_priority:
      - BYBIT_LINEAR
      - GATE_FUTURES
      - KRAKEN_FUTURES
      - BINANCE_USDM
      - COINALYZE

  FUNDING_STATE:
    min_preferred_sources: 2
    source_priority:
      - BYBIT_LINEAR
      - KRAKEN_FUTURES
      - GATE_FUTURES
      - BINANCE_USDM
      - OKX_SWAP
      - DERIBIT
      - COINALYZE

  ORDER_FLOW_STATE:
    min_preferred_sources: 2
    source_priority:
      - BINANCE_USDM
      - KRAKEN_FUTURES
      - GATE_FUTURES
      - BYBIT_LINEAR
      - OKX_SWAP

  LIQUIDITY_STATE:
    min_preferred_sources: 2
    source_priority:
      - OKX_SWAP
      - KRAKEN_FUTURES
      - BINANCE_USDM
```

Priority means preferred evidence ordering, not fallback substitution without venue identity.

---

## 15. Semantic equivalence registry schema

Planned config:

`config/crypto_sensor_fabric/semantic_equivalence.yaml`

Logical shape:

```yaml
mappings:
  - provider: GATE_FUTURES
    source_metric: long_liq_usd
    canonical_sensor: MECHANICAL_LIQUIDATION
    canonical_field: source_long_liq_usd
    equivalence: NORMALIZABLE_COMPARABLE
    methodology_id: GATE_CONTRACT_STATS_V1

  - provider: DERIBIT
    source_metric: trade.liquidation
    canonical_sensor: MECHANICAL_LIQUIDATION
    canonical_field: liquidation_role
    equivalence: CORROBORATION_ONLY
    methodology_id: DERIBIT_TRADE_LIQ_TAG_V1
```

Every mapping requires:
- source definition
- canonical target
- transformation method
- evidence reference
- equivalence class
- version

---

## 16. Methodology registry

Planned config:

`config/crypto_sensor_fabric/methodology_registry.yaml`

Examples:

```text
OI_CONTRACTS_TO_USD_V1
FUNDING_NATIVE_TO_8H_EQUIV_V1
AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1
DEPTH_BPS_RECONSTRUCTION_V1
CVD_SIGNED_NOTIONAL_V1
LIQ_USD_NATIVE_PROVIDER_V1
```

Every non-trivial derived canonical value references one methodology ID.

---

## 17. Quality state model

Individual record flags are not sufficient for runtime health.

Bloc 1 should define future-compatible quality enums:

```text
GOOD
DEGRADED
STALE
PARTIAL
UNVERIFIED
BLOCKED
```

Later `SensorHealth` can aggregate them without changing the base contracts.

---

## 18. Schema evolution rules

### Backward-compatible change

Examples:
- optional field added
- new quality flag
- new provider registry capability

Allowed under minor schema version bump.

### Breaking change

Examples:
- field meaning changes
- unit meaning changes
- required field removed
- timestamp semantics altered

Requires major schema version and migration note.

### Forbidden silent changes

- changing funding normalization formula under same methodology ID
- changing aggressor side interpretation under same adapter version
- changing OI unit assumptions under same normalization version

---

## 19. Serialization requirements

Future implementation must support:

- Pydantic v2 model validation
- JSON serialization
- JSON Schema export
- Parquet/Arrow-friendly primitive types
- deterministic canonical enum/string values

Use decimals carefully at source boundaries; analytical T2 layers may convert to floats with documented precision policy.

---

## 20. Research interoperability requirements

Canonical schemas must be easy to load into Polars/DuckDB.

Expected canonical partition columns later:

```text
sensor_family
provider
venue
instrument_id_canonical
effective_date
```

But storage partitioning is not implemented in Bloc 1.

---

## 21. No hidden aggregation rule

Schemas must never expose ambiguous names like:

```text
volume
liquidations
interest
flow
```

without explicit definition/unit/window.

Prefer:

```text
liquidation_usd
source_long_liq_usd
oi_native
funding_rate_native
quote_notional_usd
```

Ambiguous shorthand belongs only in visualization labels, not canonical data.

---

## 22. Bloc 1 schema deliverables for implementation agent

Expected later implementation files:

```text
src/crypto_sensor_fabric/contracts/enums.py
src/crypto_sensor_fabric/contracts/base.py
src/crypto_sensor_fabric/schemas/provider_envelope.py
src/crypto_sensor_fabric/schemas/trade.py
src/crypto_sensor_fabric/schemas/liquidation.py
src/crypto_sensor_fabric/schemas/open_interest.py
src/crypto_sensor_fabric/schemas/funding.py
src/crypto_sensor_fabric/schemas/book.py
src/crypto_sensor_fabric/schemas/positioning.py
src/crypto_sensor_fabric/schemas/basis.py
src/crypto_sensor_fabric/registry/provider_registry.py
src/crypto_sensor_fabric/registry/semantic_equivalence.py
src/crypto_sensor_fabric/registry/methodology_registry.py
config/crypto_sensor_fabric/provider_registry.yaml
config/crypto_sensor_fabric/sensor_priority.yaml
config/crypto_sensor_fabric/semantic_equivalence.yaml
config/crypto_sensor_fabric/methodology_registry.yaml
```

Test tree planned in the acceptance document.
