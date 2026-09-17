# BLOC 1 — CONTRACTS & SEMANTICS FOUNDATION

**Status:** implementation-grade planning specification  
**Purpose:** freeze the meaning of the sensor fabric before any provider-specific adapter is written.  
**Parent:** `../README.md`  
**Research consumers:** MECH-21, LOWER-FIELD-14, Market OS L0/L1/L2.  

---

## 1. Bloc objective

Bloc 1 defines the contracts that all later code must obey.

The central design problem is not HTTP ingestion. It is semantic control.

Different venues use different:
- contract identifiers
- quantity units
- quote/settlement assets
- funding intervals
- liquidation definitions
- order-book depths
- timestamp conventions
- aggregation windows
- side conventions

Without a strict contract layer, multi-provider coverage becomes hidden measurement drift.

Bloc 1 therefore freezes:

1. canonical sensor names
2. provider identity requirements
3. point-in-time timestamp fields
4. instrument identity fields
5. raw/canonical/derived boundaries
6. sensor-specific schemas
7. equivalence classes
8. quality flags
9. source access classes
10. fail-closed behavior
11. versioning rules
12. requirements for later probe/adapters

No external endpoint is called in Bloc 1 implementation.

---

## 2. Governing architecture

```text
PROVIDER-NATIVE OBSERVATION
        │
        ▼
ProviderEnvelope
        │
        ├── provider identity
        ├── endpoint identity
        ├── request/retrieval metadata
        ├── raw payload pointer/hash
        └── access/quality state
        │
        ▼
CANONICAL OBSERVATION
        │
        ├── canonical instrument identity
        ├── effective/observed/ingested time
        ├── native values preserved
        ├── normalized values explicit
        └── semantic equivalence status
        │
        ▼
DERIVED SENSOR STATE
```

Hard separation:

- **T0 raw:** what the provider returned.
- **T1 canonical:** semantically normalized observations with provenance.
- **T2 observable:** research features derived from T1.

No T2 feature is allowed inside a T1 canonical observation schema.

---

## 3. Provider-independent sensor vocabulary

The initial canonical sensor families are fixed to the currently justified research needs.

### 3.1 `MECHANICAL_TRADE`

A public venue trade or aggregated trade observation.

Required semantics:
- price
- quantity/native units
- quote notional when reconstructable
- aggressor/taker side when provider semantics permit
- trade timestamp
- unique/source trade ID where available

Not included:
- derived CVD
- derived large-trade classification
- derived imbalance

### 3.2 `MECHANICAL_LIQUIDATION`

A provider-observed forced liquidation event or liquidation aggregate.

This family deliberately supports multiple shapes:

1. trade-level liquidation event
2. interval long/short liquidation aggregate
3. provider-level total liquidation volume

Canonical fields must not pretend these are identical.

### 3.3 `MECHANICAL_OPEN_INTEREST`

A venue/instrument OI observation.

Preserve separately:
- provider-native OI value
- base-unit OI when interpretable
- quote/USD equivalent when reconstructable
- provider unit declaration

Do not replace native values with normalized values.

### 3.4 `MECHANICAL_FUNDING`

A venue/instrument funding observation.

Preserve:
- provider-native funding rate
- native interval
- event/effective timestamp
- derived 8h-equivalent only as a derived normalization field

Never overwrite the native rate.

### 3.5 `MECHANICAL_BOOK_SNAPSHOT`

Raw or provider-aggregated order-book state.

Preserve:
- source depth definition
- source number of levels / bands
- bid/ask arrays or provider-native aggregates
- snapshot timestamp

Do not compare raw level counts across venues as if equivalent.

### 3.6 `MECHANICAL_BOOK_METRIC`

Economically normalized book measurements derived from a valid snapshot or official provider analytics.

Canonical examples:
- spread_bps
- depth_bid_5bps
- depth_ask_5bps
- depth_bid_10bps
- depth_ask_10bps
- depth_bid_25bps
- depth_ask_25bps
- depth_bid_50bps
- depth_ask_50bps
- book_imbalance
- slippage_buy_usd_X
- slippage_sell_usd_X

Provider-native analytics and locally reconstructed metrics must carry different methodology IDs.

### 3.7 `MECHANICAL_POSITIONING`

Public long/short ratios, top-trader ratios, user-position ratios or similar positioning observations.

These are contextual observations and never substitutes for OI.

### 3.8 `MECHANICAL_BASIS`

Perpetual/futures basis or premium observations where provider semantics are clear.

---

## 4. Canonical identity model

Every T1 observation must retain both provider-native and canonical identity.

Required fields:

```text
provider
venue
market_type
instrument_native
instrument_id_canonical
base_asset
quote_asset
settlement_asset
contract_type
contract_multiplier
is_inverse
instrument_start
instrument_end
identity_version
```

### 4.1 `venue`

The economic venue where the observation occurred.

Examples:
- KRAKEN_FUTURES
- GATE_FUTURES
- BINANCE_USDM
- BYBIT_LINEAR
- OKX_SWAP
- DERIBIT

Provider and venue may differ for aggregators.

Example:

```text
provider = COINALYZE
venue = BINANCE_USDM
```

if the aggregator clearly identifies the originating venue.

If venue cannot be determined:

```text
venue = AGGREGATED_UNKNOWN
quality_flags += VENUE_NOT_DECOMPOSABLE
```

### 4.2 Instrument lifecycle

An instrument ID is not timeless.

Later identity logic must represent:
- first known trading timestamp
- final timestamp / delisting
- contract replacement
- symbol rename
- settlement/collateral change

Canonical asset identity does not erase contract identity.

`BTCUSDT` linear perpetual and an inverse `XBTUSD` future may both map to BTC exposure while remaining distinct instruments.

---

## 5. Point-in-time time model

Every observation must expose three conceptually distinct timestamps.

### 5.1 `effective_at`

When the observation economically applies.

Examples:
- trade execution time
- funding settlement time
- OI snapshot time
- book snapshot time

### 5.2 `observed_at`

When the provider says the observation was published/observable if that differs from `effective_at`.

If no separate publication timestamp exists and the source is an immediate market event:

```text
observed_at = effective_at
```

with an explicit timestamp provenance flag.

### 5.3 `ingested_at`

When our system actually retrieved/stored the observation.

Historical replay uses effective/observed semantics, not the modern backfill ingestion time.

### 5.4 Additional time fields

Where needed:

```text
window_start
window_end
source_interval
source_timezone
```

All canonical timestamps stored as UTC.

---

## 6. Observation envelope

Every provider adapter in future blocs must first emit a provider envelope before normalization.

Minimum conceptual schema:

```text
ProviderEnvelope:
  provider
  venue
  sensor_family
  endpoint_id
  request_id
  retrieval_mode        # REST | WS | BULK_FILE | COMMUNITY_ARCHIVE
  effective_at
  observed_at
  ingested_at
  source_interval
  source_symbol
  raw_object_uri
  raw_checksum
  adapter_version
  access_class
  quality_flags[]
  source_metadata{}
```

No provider adapter writes directly into research features.

---

## 7. Access classes

Carry the existing free-only taxonomy:

```text
FREE_AUTOMATED
FREE_LIMITED_AUTOMATED
FREE_REFERENCE_ONLY
PAID_EXCLUDED
UNVERIFIED
```

Required provider registry fields:

```text
provider
sensor_family
access_class
verified_at
verification_method
cost_usd_required
payment_method_required
staking_required
transaction_required
api_key_required
rate_limit
historical_access_claimed
historical_access_verified
terms_reference
fallback_providers[]
status
```

Only `FREE_AUTOMATED` and `FREE_LIMITED_AUTOMATED` may be eligible for required automated ingestion.

Community/open datasets can be free but still carry lower evidence status than exchange-native first-party data.

---

## 8. Evidence/source classes

Separate cost/access from evidentiary provenance.

```text
FIRST_PARTY_EXCHANGE
FIRST_PARTY_AGGREGATOR
THIRD_PARTY_AGGREGATOR
COMMUNITY_ARCHIVE
RECONSTRUCTED_INTERNAL
```

Example:

- Gate official futures API = FIRST_PARTY_EXCHANGE
- Coinalyze = THIRD_PARTY_AGGREGATOR
- Bitfinex liquidation community dump = COMMUNITY_ARCHIVE
- CVD reconstructed from Binance public trades = RECONSTRUCTED_INTERNAL with source provider Binance

Evidence class affects quality/confidence, not whether the record exists.

---

## 9. Semantic equivalence contract

Every provider-native metric mapped to a canonical concept gets one of:

### `EXACT_EQUIVALENT`

Definition/unit/window match tightly enough to combine without semantic transformation other than representation conversion.

Rare. Requires explicit evidence.

### `NORMALIZABLE_COMPARABLE`

Same economic concept but requires unit/window/method normalization.

Examples may include:
- funding rates on different native intervals
- interval liquidation notional across exchanges
- CVD from provider analytics vs reconstructed signed trades

### `CORROBORATION_ONLY`

Related measurement that should not be pooled numerically as the same object.

Examples:
- liquidation-tagged individual Deribit trades vs interval aggregate liquidation totals
- provider-calculated slippage vs locally reconstructed depth metric with materially different methodology

### `NOT_COMPARABLE`

Keep independently; do not synthesize.

The equivalence decision must be machine-readable and versioned.

---

## 10. Native-value preservation rule

Normalization can add values. It cannot destroy provider-native values.

Example OI observation:

```text
oi_native = 125000
native_unit = CONTRACTS
oi_base = 1250 BTC
oi_quote = 82_000_000 USD
normalization_method = CONTRACT_MULTIPLIER_X_MARK
```

If conversion is not defensible:

```text
oi_base = NULL
oi_quote = NULL
quality_flags += UNIT_NORMALIZATION_UNAVAILABLE
```

Never guess.

---

## 11. Missingness contract

Missing is information.

Allowed missing-state categories:

```text
NOT_SUPPORTED
NOT_LISTED
OUTSIDE_PROVIDER_HISTORY
ENDPOINT_UNAVAILABLE
RATE_LIMITED
AUTH_BLOCKED
GEO_BLOCKED
PROVIDER_GAP
PARSE_FAILED
SEMANTIC_UNRESOLVED
DATA_BLOCKED
```

No zero fill.

No carry-forward of liquidations/trades as zero unless the source explicitly reports a valid zero for that interval.

No forward-filled order book/OI measurement presented as fresh.

---

## 12. Quality-flag vocabulary

Initial shared flags:

```text
SOURCE_NATIVE
SOURCE_AGGREGATED
SOURCE_COMMUNITY
RECONSTRUCTED_INTERNAL
TIMESTAMP_ASSUMED
TIMESTAMP_COARSE
UNIT_NATIVE_ONLY
UNIT_NORMALIZED
UNIT_NORMALIZATION_UNAVAILABLE
VENUE_NOT_DECOMPOSABLE
INSTRUMENT_ID_UNRESOLVED
WINDOW_SEMANTICS_UNCERTAIN
PARTIAL_INTERVAL
DUPLICATE_SOURCE_RECORD
SOURCE_GAP
STALE_SOURCE
PROVIDER_DEGRADED
CROSS_PROVIDER_DISAGREEMENT
HISTORICAL_DEPTH_UNVERIFIED
ACCESS_CLASS_UNVERIFIED
PIT_RISK
```

Flags are additive; one record may contain several.

Later blocs may add provider-specific raw flags, but canonical flags require Bloc-governed registry changes.

---

## 13. Versioning

Every canonical record must be reproducible against:

```text
adapter_version
schema_version
identity_version
normalization_version
methodology_version
```

Research artifacts must reference these versions.

Changing normalization logic does not silently mutate historical truth.

Preferred behavior:

```text
v1 raw remains immutable
v2 canonical derivation produced separately
research explicitly selects v2
```

---

## 14. Cross-venue synthesis rule

No cross-venue value exists at T1 unless it is itself a provider aggregate.

Cross-venue synthesis belongs to T2.

T1:

```text
Kraken liquidation
Gate liquidation
Deribit liquidation-tagged trade
```

T2 may derive:

```text
LiquidationBreadth
CrossVenueLiquidationIntensity
VenueDispersion
FlowConsensus
```

This preserves venue-local information for later science.

---

## 15. Research-facing contract

MECH-21/LF14 must never import provider field names.

Bad:

```python
if gate.long_liq_usd > ...
```

Allowed:

```python
mechanical.liquidation_state(...)
mechanical.oi_state(...)
mechanical.orderflow_state(...)
```

Research may explicitly request venue-specific canonical observations, but the provider adapter itself stays below the research layer.

---

## 16. In-scope for Bloc 1 implementation later

The execution agent should create:

```text
src/crypto_sensor_fabric/contracts/
src/crypto_sensor_fabric/schemas/
src/crypto_sensor_fabric/registry/
config/crypto_sensor_fabric/
tests/crypto_sensor_fabric/contracts/
```

Implementation targets include:

- enums
- Pydantic schemas
- JSON-schema export
- provider registry schema
- equivalence registry schema
- quality flag registry
- free-only validation
- schema compatibility tests

No HTTP clients.
No storage engine.
No provider adapters.
No data download.

---

## 17. Out-of-scope

Bloc 1 must NOT implement:

- Kraken/Gate/Binance/etc API calls
- data lake writes
- DuckDB/Postgres storage
- historical downloads
- live websocket collectors
- mechanical features
- cross-venue aggregation
- research regressions
- strategy or execution

Those are later blocs.

---

## 18. Bloc 1 success condition

Bloc 1 is complete only when a future provider adapter can be written without inventing any new foundational concept for:

- provider identity
- instrument identity
- timestamps
- access/cost state
- provenance
- raw observation envelope
- canonical sensor family
- normalized/native values
- missingness
- quality
- semantic comparability
- versioning

If an adapter still needs ad-hoc foundational fields, Bloc 1 is incomplete and must be amended before provider implementation continues.
