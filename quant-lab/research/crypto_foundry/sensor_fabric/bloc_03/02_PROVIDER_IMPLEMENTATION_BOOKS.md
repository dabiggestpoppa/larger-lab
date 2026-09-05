# BLOC 3 — PROVIDER IMPLEMENTATION BOOKS

**Purpose:** convert Bloc 2 verified capability evidence into provider-specific implementation contracts without allowing provider semantics to leak above the adapter boundary.

## 1. General rule

Every provider implementation must follow the common Bloc 3 interface, but each provider retains native acquisition mechanics. Do not force providers into identical endpoint patterns.

Each implementation book must contain:

```text
provider role
verified sensors
verified historical modes
verified live modes
native instrument naming
native timestamp semantics
native unit semantics
pagination/archive semantics
rate-limit behavior
auth mode
geo/access caveats
schema signatures
raw evidence preservation plan
provider-specific failures
fixtures required
adapter acceptance tests
```

Capability claims come from Bloc 2 evidence, not this plan.

---

# 2. Kraken Futures book

## Intended role

High-value multi-sensor mechanical source, especially where one provider can expose coordinated analytics around:

- liquidation volume
- open interest
- aggressor differential / CVD
- orderbook / spread / liquidity / slippage
- funding
- basis / supporting context

## Architecture

Use a Kraken package split between:

```text
analytics requests
instrument discovery
archive/history paging if separately required
live/public market paths where verified
```

Do not treat Kraken-calculated analytics as identical to reconstructed trade-level metrics from Binance/OKX.

Semantic mappings should often begin as `NORMALIZABLE_COMPARABLE`, not `EXACT_EQUIVALENT`.

## Required fixtures

At least:

```text
valid multi-row historical response
empty-but-valid historical response
unsupported symbol
unsupported interval
rate-limit/error payload
schema-additive payload
malformed payload
boundary date response
```

## Special QA

- prove whether timestamps describe interval open, close, or publication;
- preserve Kraken's native analytic naming;
- verify liquidation-volume sign/side semantics;
- verify CVD/aggressor convention;
- do not silently equate Kraken liquidity/slippage analytics with book reconstruction methodology.

---

# 3. Gate Futures book

## Intended role

Primary/secondary source for:

- long/short liquidation statistics
- OI
- long/short taker flow
- funding
- positioning ratios where verified

## Architecture

Gate adapter should retain whether a record comes from:

```text
contract_stats
funding endpoint
trade endpoint
websocket statistics
other verified public endpoint
```

The adapter must preserve contract-settlement context and Gate-native size units.

## Special QA

- long_liq vs short_liq orientation;
- size vs USD fields;
- contract multiplier effects;
- from/to history semantics;
- limits and pagination;
- USDT vs BTC-settled futures separation;
- historical granularity availability.

No single Gate `contract_stats` record may be promoted directly into a canonical cross-venue liquidation state.

---

# 4. Binance USD-M book

## Intended role

Historical backbone for:

- trades / aggTrades
- aggressor-flow reconstruction
- funding
- historical OI/metrics where verified
- bookDepth/archive data as secondary liquidity evidence

Historical liquidation support is NOT assumed.

## Archive architecture

Binance may use bulk ZIP/CSV archives rather than only REST. Adapter needs archive-manifest capability:

```text
object key
date partition
content length
checksum when provided
retrieval timestamp
archive version/path
```

Archive download should be resumable and checksum-validated.

## Aggressor-side QA

`isBuyerMaker` mapping must have fixture-backed interpretation before generating signed aggressor direction.

The adapter itself should preserve the native field. Any derived buy/sell aggressor interpretation should be a parser annotation with methodology ID, not research CVD yet.

## Known concerns to encode

- missing archive dates;
- historical liquidation removal/unavailability;
- metrics holes;
- bookDepth sampling rather than event-level full reconstruction;
- archive format changes.

Missing Binance liquidations must be `HISTORY_NOT_AVAILABLE`, not zero.

---

# 5. Bybit Linear book

## Intended role

High-value historical source for:

- open interest
- funding
- public trades / archived trades where verified
- later live market data

## Special architecture

Bybit OI history is cursor/range sensitive. Preserve native cursor and interval in resume state.

## Special QA

- symbol launch date vs requested history;
- OI unit differences by contract;
- linear/inverse separation;
- cursor exhaustion;
- duplicate edge rows across pages;
- funding interval differences by symbol/era;
- historical trade archive coverage.

Do not infer pre-launch missing observations as market zero.

---

# 6. OKX Swap book

## Intended role

Primary/secondary source for:

- historical trades
- funding
- historical order books / depth where verified
- potentially current OI/context

## Historical orderbook architecture

Because OKX may expose downloadable historical market-data modules, adapter must support asynchronous/download-link style acquisition when applicable:

```text
request export
poll export status if required
receive signed/temporary URL
archive raw file
validate file
record export request metadata
```

A temporary URL is transport evidence, not canonical provenance. Provenance remains OKX + request metadata.

## Depth QA

Preserve native depth level count and sampling frequency. Later book metrics must derive economically comparable bps-depth measures.

Never compare raw 50-level and 5000-level depth totals directly without normalization.

---

# 7. Deribit book

## Intended role

Mechanism microscope for BTC/ETH-heavy validation:

- trade history
- aggressor direction
- liquidation-tagged trades
- funding
- selected derivatives context

## Liquidation semantics

Preserve native liquidation flag exactly, including maker/taker distinctions.

Canonical parser may expose native roles such as:

```text
MAKER_LIQUIDATED
TAKER_LIQUIDATED
BOTH
NONE/ABSENT
```

but the raw flag must remain available.

## Special QA

- sequence-ID vs timestamp history;
- overlap across pagination boundaries;
- instrument expiry/perpetual distinction;
- liquidation flag availability by instrument/history;
- inverse contract unit conversion deferred to normalization layer.

---

# 8. Coinalyze book

## Intended role

Aggregator/corroboration source, not primary venue truth.

Potential sensors:

- OI
- funding
- liquidations
- long/short ratios
- OHLC context

## Evidence rule

All Coinalyze records carry evidence class appropriate to third-party aggregation. They may corroborate venue-native data but cannot silently replace venue identity.

## History QA

Encode granular-history retention limits explicitly. `earliest_verified_history` must vary by interval/sensor.

Never extrapolate current documented retention backward.

## Auth

A free API key is acceptable only if Bloc 2 verifies zero-dollar access and no payment method/stake requirement.

---

# 9. Bitfinex community liquidation archive book

## Intended role

Independent historical corroboration / replication dataset for liquidations.

## Evidence class

Community archive / third-party reconstruction. Never label as first-party Bitfinex canonical exchange archive unless source provenance proves otherwise.

## Adapter mode

Likely `THIRD_PARTY_ARCHIVE` / bulk-file reader rather than live REST provider.

Required metadata:

```text
upstream project repo/version
file URL/object identity
publication timestamp
archive coverage
checksum
license
methodology reference
```

## Special QA

- duplicate rows;
- source methodology changes;
- missing dates;
- symbol normalization deferred;
- spot/margin vs derivatives classification;
- archive cutoff.

---

# 10. Provider ranking is role-specific

Do NOT make a global ranking such as Kraken > Gate > Binance.

Rank by sensor/use case:

```text
liquidation interval aggregates
liquidation trade microscope
OI history
funding history
aggressor flow
book depth
spread/liquidity analytics
corroboration
```

The same provider may be Tier A for one sensor and unsupported for another.

---

# 11. Provider-specific methodology IDs

Examples of planned IDs:

```text
KRAKEN_ANALYTICS_NATIVE_V1
GATE_CONTRACT_STATS_NATIVE_V1
BINANCE_AGGTRADE_NATIVE_V1
BINANCE_AGGRESSOR_ANNOTATION_V1
BYBIT_OI_NATIVE_V1
OKX_HIST_BOOK_NATIVE_V1
DERIBIT_LIQ_ROLE_NATIVE_V1
COINALYZE_AGG_NATIVE_V1
BITFINEX_COMMUNITY_LIQ_ARCHIVE_V1
```

These identify parser/acquisition semantics, not derived market features.

---

# 12. Provider README requirement

Every provider implementation must ship a README containing:

1. role in sensor fabric;
2. verified capabilities/evidence refs;
3. unsupported sensors;
4. access class;
5. auth mode;
6. history limitations;
7. timestamp semantics;
8. unit semantics;
9. pagination/archive rules;
10. known quality issues;
11. fixture inventory;
12. example raw fetch invocation;
13. explicit non-goals.

---

# 13. Provider implementation order

Recommended execution order after Bloc 2 runtime evidence exists:

```text
B3-P0 base adapter framework
B3-P1 Kraken
B3-P2 Gate
B3-P3 Binance
B3-P4 Bybit
B3-P5 OKX
B3-P6 Deribit
B3-P7 Coinalyze
B3-P8 Bitfinex community archive
```

Why:

Kraken/Gate expose many missing mechanics; Binance provides historical flow backbone; Bybit adds OI/funding depth; OKX adds book history; Deribit provides liquidation anatomy; last two are corroboration layers.

No provider may block the entire fabric if another provider covers the sensor family.

`human_review_required = TRUE`
