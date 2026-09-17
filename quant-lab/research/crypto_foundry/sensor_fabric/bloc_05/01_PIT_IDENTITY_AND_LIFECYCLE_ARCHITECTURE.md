# BLOC 5 — PIT IDENTITY & INSTRUMENT LIFECYCLE ARCHITECTURE

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent:** Bloc 4 immutable T0 evidence lake  
**Purpose:** define point-in-time instrument identity so provider-native market observations can become canonical T1 observations without erasing venue, contract, settlement, or lifecycle truth.

---

## 1. Objective

Bloc 5 converts **provider-native evidence** into **canonical PIT observations**.

This document freezes the identity side of that transformation.

The central problem is not symbol spelling. It is economic identity across time.

Examples such as:

```text
BTCUSDT
BTC-USDT-SWAP
PI_XBTUSD
BTC-PERPETUAL
BTC_USDT
```

may all reference Bitcoin derivatives, but they are **not interchangeable records**. They can differ by:

- venue;
- contract family;
- linear vs inverse payoff;
- quote asset;
- settlement asset;
- contract multiplier;
- margin asset;
- listing epoch;
- delivery/perpetual structure;
- provider-specific symbol reuse;
- tick/lot terms;
- underlying index;
- data publication semantics.

Hard rule:

> Canonical asset identity may unify economic underlyings, but it must never erase the contract instance that produced an observation.

---

## 2. Identity layers

The implementation should separate at least five identity levels.

### 2.1 `CanonicalAsset`

Represents the economic asset itself.

Examples:

```text
BTC
ETH
SOL
USDT
USDC
USD
```

Fields:

```text
asset_id
symbol_canonical
asset_type
chain_or_issuer_context optional
valid_from optional
valid_to optional
metadata_version
```

This object is **not** sufficient to identify a derivative contract.

### 2.2 `Venue`

Represents the actual market venue / exchange family.

```text
KRAKEN_FUTURES
GATE_FUTURES
BINANCE_USDM
BYBIT_LINEAR
OKX
DERIBIT
BITFINEX
```

Provider and venue remain separate because an aggregator can report a venue it does not operate.

### 2.3 `VenueInstrument`

The provider/venue-native instrument identity.

Fields:

```text
provider
venue
native_symbol
provider_instrument_id optional
instrument_type
native_metadata_hash
first_seen_at
last_seen_at
```

This is what raw payloads refer to.

### 2.4 `EconomicContract`

Stable economic grouping when multiple native symbols are economically comparable.

Fields:

```text
economic_contract_id
underlying_asset_id
quote_asset_id
settlement_asset_id
margin_asset_id optional
instrument_type
perpetual_or_delivery
payoff_type
index_family optional
```

`EconomicContract` is useful for grouping, not for destructive replacement of contract-instance identity.

### 2.5 `ContractInstance`

The exact lifecycle-valid contract terms at a point in time.

Fields:

```text
contract_instance_id
provider
venue
native_symbol
economic_contract_id
valid_from
valid_to
known_from
known_to optional
contract_multiplier
multiplier_unit
price_unit
quantity_unit
settlement_asset_id
margin_asset_id
payoff_type
inverse_flag
quanto_flag
tick_size
lot_size
expiry optional
contract_terms_version
source_evidence_refs
```

Every T1 observation must resolve to a `contract_instance_id` or fail closed.

---

## 3. Payoff types

Initial canonical values:

```text
LINEAR
INVERSE
QUANTO
SPOT
UNKNOWN
```

For the first sensor-fabric build, derivatives work centers on linear and inverse futures/perpetuals.

`QUANTO` exists in the schema so the resolver does not incorrectly force an unfamiliar contract into linear/inverse semantics.

If payoff semantics are not verified:

```text
payoff_type = UNKNOWN
normalization_status = IDENTITY_BLOCKED
```

No guessed conversion.

---

## 4. Base / quote / settlement / margin identities

These are separate fields.

Example linear USDT perpetual:

```text
underlying = BTC
quote = USDT
settlement = USDT
margin = USDT
```

Example inverse USD contract:

```text
underlying = BTC
quote = USD
settlement = BTC
margin = BTC
```

No implementation may infer settlement or margin solely from symbol spelling unless the provider contract metadata explicitly guarantees the convention and that convention is versioned.

---

## 5. Point-in-time lifecycle model

Identity resolution is **temporal**.

A mapping must have two independent concepts:

```text
valid_time = when the mapping/contract terms were economically true
knowledge_time = when the system could justify knowing that mapping
```

Minimum fields:

```text
valid_from
valid_to
known_from
known_to optional
```

A backtest/replay resolving identity at time `t` may only use a mapping satisfying both:

```text
valid_from <= t < valid_to
known_from <= replay_knowledge_cutoff
```

No future symbol map may leak backward.

---

## 6. Listing / delisting / relisting

The lifecycle registry must explicitly represent:

```text
PRE_LISTING
ACTIVE
SUSPENDED
DELISTING_ANNOUNCED
DELISTED
RELISTED_NEW_INSTANCE
UNKNOWN
```

Rules:

1. A symbol observed before verified listing time is flagged.
2. A delisted symbol cannot silently remain active because a later metadata snapshot still contains an alias.
3. Relisting after a material lifecycle break creates a **new contract instance** unless evidence proves continuity.
4. Historical absence before listing is `NOT_YET_LISTED`, not missing market data.
5. Absence after delisting is `DELISTED`, not zero activity.

---

## 7. Symbol reuse and contract migration

A venue may reuse a string symbol while terms change.

Therefore:

```text
native_symbol != durable contract identity
```

Material changes that force either a new `ContractInstance` or a new terms version include:

- payoff type change;
- settlement asset change;
- multiplier change;
- underlying index change;
- expiry reset / delivery series rollover;
- margin model change when it changes unit interpretation;
- native contract size change;
- provider semantic change that affects historical fields.

Minor tick/lot changes may remain the same contract instance with a new terms version if economic continuity remains intact.

---

## 8. Instrument aliases

`InstrumentAlias` object:

```text
alias_id
provider
venue
alias_text
alias_type
contract_instance_id
valid_from
valid_to
known_from
source_evidence_refs
confidence
```

Alias types:

```text
API_SYMBOL
ARCHIVE_SYMBOL
WEBSOCKET_SYMBOL
DISPLAY_SYMBOL
LEGACY_SYMBOL
PROVIDER_INTERNAL_ID
```

This avoids assuming one provider uses one symbol everywhere.

---

## 9. PIT resolver

Planned interface:

```python
resolve_instrument(
    provider,
    venue,
    native_symbol,
    event_time,
    knowledge_cutoff,
    optional_provider_instrument_id=None,
) -> IdentityResolution
```

`IdentityResolution` returns:

```text
status
contract_instance_id
canonical_asset_id
economic_contract_id
matched_alias_id
terms_version
confidence
quality_flags
source_evidence_refs
```

Statuses:

```text
RESOLVED_EXACT
RESOLVED_ALIAS
RESOLVED_WITH_WARNING
AMBIGUOUS
NOT_YET_LISTED
DELISTED
UNKNOWN_SYMBOL
TERMS_UNVERIFIED
PIT_KNOWLEDGE_BLOCKED
```

`AMBIGUOUS`, `UNKNOWN_SYMBOL`, `TERMS_UNVERIFIED`, and `PIT_KNOWLEDGE_BLOCKED` block T1 economic normalization.

---

## 10. Identity matching order

The resolver must prefer evidence in this order:

1. provider instrument ID valid at event time;
2. exact native symbol + venue + lifecycle interval;
3. documented alias valid at event time;
4. curated manual mapping backed by evidence;
5. no result.

Prohibited:

- fuzzy string match as final truth;
- symbol prefix matching;
- assuming `BTC` and `XBT` are interchangeable without a registered alias;
- assuming any `USDT` contract is equivalent to a USD-settled contract;
- current exchange metadata applied backward without lifecycle evidence.

Fuzzy matching may generate review candidates only.

---

## 11. PIT universe membership

Universe membership is a derived registry object, not a current-symbol list projected backward.

`UniverseMembership`:

```text
universe_version
contract_instance_id
membership_tier
valid_from
valid_to
selection_basis
known_from
```

Initial tiers inherit the sensor-fabric roadmap:

```text
U0 MECHANISM CORE
U1 BROAD RESEARCH
U2 LONG TAIL
```

No future volume/rank information may determine historical membership unless the research explicitly declares retrospective-universe analysis.

---

## 12. Stablecoin and fiat identities

`USD`, `USDT`, `USDC`, and other quote/settlement assets remain distinct canonical assets.

Hard rule:

> Stablecoin-denominated notional is not silently equal to USD notional.

T1 preserves native quote notional.

Optional USD conversion requires a PIT-safe conversion observation and methodology reference defined later in this bloc.

A stablecoin depeg is therefore observable rather than erased by normalization.

---

## 13. Provider vs venue vs aggregator

Keep these separate:

```text
provider = who supplied the payload
venue = where the market event occurred
```

Examples:

```text
provider=COINALYZE
venue=BINANCE_USDM
```

if the aggregator exposes venue-specific Binance data.

An aggregated multi-venue value must not be assigned to a fake single venue.

It instead carries a scope such as:

```text
venue_scope = MULTI_VENUE_AGGREGATE
constituent_venues = [...]
```

if constituent evidence is documented.

---

## 14. Identity quality flags

Minimum identity flags:

```text
IDENTITY_ALIAS_USED
IDENTITY_AMBIGUOUS
IDENTITY_TERMS_UNVERIFIED
IDENTITY_LIFECYCLE_BOUNDARY
IDENTITY_SYMBOL_REUSED
IDENTITY_RELISTED
IDENTITY_CURRENT_METADATA_BACKCAST_RISK
IDENTITY_PROVIDER_ID_MISSING
IDENTITY_MANUAL_OVERRIDE
IDENTITY_STABLECOIN_DISTINCT
```

Manual override is allowed only with evidence and a versioned registry change.

---

## 15. Identity registry versioning

The identity registry is versioned independently from normalization code.

Every T1 row records:

```text
identity_registry_version
contract_terms_version
```

Rebuilding old T1 data under a newer identity registry creates a new T1 generation. It does not rewrite prior T1 evidence silently.

---

## 16. Required implementation modules

Planned tree:

```text
quant-lab/src/crypto_sensor_fabric/normalization/
  identity/
    models.py
    enums.py
    registry.py
    resolver.py
    lifecycle.py
    aliases.py
    terms.py
    universe.py
    evidence.py
```

Config/evidence:

```text
quant-lab/config/crypto_sensor_fabric/
  identity_registry.yaml
  venue_registry.yaml
  asset_registry.yaml
```

Large machine-generated lifecycle catalogs should live outside Git when necessary, with manifests/checksums committed.

---

## 17. Identity invariants

Implementation must enforce:

1. every economically normalized row resolves to one contract instance;
2. contract instance validity contains event/effective time;
3. no overlapping active terms for the same provider instrument without explicit ambiguity state;
4. quote, settlement, and margin assets are not conflated;
5. native symbol is preserved;
6. provider identity is preserved;
7. lifecycle absence is not converted to zero;
8. future mappings cannot leak backward;
9. manual overrides are auditable;
10. contract-term changes are versioned.

---

## 18. Out of scope

This bloc does not:

- merge venue observations into cross-venue sensors;
- compute trading signals;
- infer synthetic continuous futures prices;
- hide stablecoin basis;
- create asset rank states;
- decide provider quality/failover;
- perform historical backfill orchestration.

Those belong to later blocs.

---

## 19. Handoff

The next Bloc 5 document defines **timestamp, availability, and revision truth**.

Identity tells us **what contract an observation belongs to**.

Timestamp truth tells us **when that observation was economically true and when it could legitimately be known**.
