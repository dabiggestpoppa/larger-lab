# QUANT BOX — Alt Rotation / BTC-ETH Lead-Lag Terrain Idea

**Status:** IDEA PRESERVATION / DATA-REALITY PLANNING ONLY
**Branch:** `agent/crypto-quant-foundry`
**Do not disturb:** current ALPHA-2 experiment
**Future lane:** `CRYPTO-ALT-ROTATION-1`

---

## Core idea

Build a crypto capital-routing model that treats the alt universe as a changing ranked field instead of a list of named coins.

The research question is not:

> Which coin pumps next?

It is:

> When BTC / ETH and dominance enter a particular state, where does capital migrate through the ranked altcoin universe, how persistent is that migration, and which liquid perpetual contracts best express the move?

Two broad execution concepts:

### A. Channel the wave

Use relative-value / rotation logic.

Study where capital migrates across rank bands and sectors, then trade the relative dislocation rather than outright market direction where appropriate.

Examples:

- long stronger alt / short BTC
- long ETH / short BTC
- long a strong rank-band basket / short a weaker benchmark basket
- pair or basket trades based on lead-lag and relative resistance

### B. Move with the stream

Use directional trend-following logic after the terrain identifies where money is flowing.

Potential expression:

- long/short liquid perpetual
- ATR-normalized stop
- ATR target / trailing logic
- multi-hour to multi-day holding period

The terrain provides the alpha hypothesis. ATR is execution geometry, not the alpha source.

---

# Research philosophy

Strip names and narratives where possible.

Track:

- rank position
- rank-band migration
- market-cap share
- volume rank
- relative return vs BTC
- relative return vs ETH
- beta to BTC / ETH
- correlation
- lead / lag
- sector membership
- sector breadth
- age / trading-history eligibility
- perpetual availability
- liquidity / turnover

The objective is to discover repeatable market mechanisms such as:

> assets ranked 200–275 collectively gain ranking positions after a BTC impulse, then a neighboring rank band receives follow-through.

or:

> ETH-relative strength becomes the bridge between BTC-led expansion and broad alt expansion.

or:

> a sector resists BTC weakness, then becomes the next capital destination when BTC stabilizes.

Do not follow individual coin anecdotes.

---

# Point-in-time universe is mandatory

The largest scientific risk is survivorship / look-ahead bias.

Never use today's top 500 to test an old date.

For each historical timestamp `t`, reconstruct the universe that was actually eligible at `t`.

A coin may only enter the research universe if, at `t`:

1. it was inside the historical top-N ranking under the selected ranking source,
2. it had existed / traded for the minimum required age,
3. the intended perpetual contract was actually listed and tradable,
4. the contract had been live long enough to satisfy the minimum listing-age rule,
5. required historical data exists,
6. liquidity filters are met using information available at `t`.

Recommended initial listing-age rule:

> perpetual contract live for at least 30 calendar days before eligibility

This is a preregistration candidate, not a final rule until the data audit confirms what is practical.

---

# Historical rank reconstruction

## Best immediate free source discovered: CoinMarketCap Historical Snapshots

CoinMarketCap exposes point-in-time historical ranking pages, for example:

- https://coinmarketcap.com/historical/20260701/
- historical snapshot pages contain rank, name, symbol, market cap, price, circulating supply, 24h volume and returns.

This is the cleanest current lead for reconstructing historical top-500 membership without using today's survivors.

Research task:

1. determine historical depth,
2. determine whether snapshots are daily across the period we want,
3. determine how many ranks are exposed per snapshot,
4. build a collector that stores the full point-in-time ranking table,
5. hash every raw snapshot,
6. preserve CoinMarketCap ID / symbol mapping where possible,
7. test missing / duplicated / renamed assets.

Do not assume symbol text alone is a unique asset key.

---

# CoinGecko role

CoinGecko should be a secondary market-cap / metadata / historical-series source rather than the primary point-in-time ranking source unless a historical ranking endpoint is verified.

Current official API documentation supports:

- `/coins/markets` for current market-cap rankings,
- `/coins/{id}/history` for a coin snapshot on a specific date,
- `/coins/{id}/market_chart` and `/range` for historical price, market cap and volume,
- `/coins/{id}/tickers` for exchange / market mapping,
- category endpoints for sector-style classifications.

References:

- https://docs.coingecko.com/reference/endpoint-overview
- https://docs.coingecko.com/reference/coins-markets
- https://docs.coingecko.com/reference/coins-id-market-chart
- https://docs.coingecko.com/reference/coins-id-market-chart-range

Important limitation:

reconstructing the complete historical top 500 from per-coin history alone can become expensive and can itself introduce universe bias if the historical candidate list is derived from today's assets.

Therefore preferred order:

1. point-in-time CoinMarketCap snapshot universe,
2. CoinGecko ID / market-cap / sector / metadata enrichment,
3. exchange perpetual-listing intersection.

---

# Exchange-listing truth

Spot listing is not sufficient for this lane.

The preferred execution universe is perpetual / derivative contracts because the strategy is intended to support leverage-efficient long and short expressions.

A coin is not testable for this strategy simply because price data exists.

We need a historical contract-availability ledger.

## Bybit

Official V5 instrument metadata is unusually useful because `Get Instruments Info` exposes:

- contract type,
- status,
- `launchTime`,
- `deliveryTime` / perpetual delisting time,
- base / quote / settle asset,
- leverage and lot filters.

Official documentation:

https://bybit-exchange.github.io/docs/v5/market/instrument

This means current and returned historical/closed instrument metadata can potentially support point-in-time availability testing.

Need to verify how complete `Closed` / delisted contract retrieval is in practice.

## OKX

OKX public instrument metadata includes `listTime`, and the official API documentation states listing events update the instruments feed around the listing announcement.

Official docs:

https://www.okx.com/docs-v5

Useful fields / concepts:

- `instType=SWAP`
- `listTime`
- instrument `state`
- current live / preopen state

Need a delisting-history solution because current instrument endpoints may not retain every old contract.

## Binance Futures

Binance USD-M Futures exposes current symbol metadata through:

`GET /fapi/v1/exchangeInfo`

Official connector / endpoint reference:

https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information

Research task:

- inspect whether current symbol metadata includes a usable onboarding / listing timestamp in the current API response,
- combine current metadata with historical listing / delisting announcements or archived snapshots for contracts no longer live,
- never infer listing date from first price bar without labeling it as a fallback estimate.

## Hyperliquid

Hyperliquid remains important for native perp research, but historical universe membership / listing timestamps require a separate audit.

Possible sources:

- first confirmed market metadata appearance,
- first native historical candle / funding observation,
- listing announcements,
- archived universe metadata if obtainable.

Do not equate first local data timestamp with official listing time without independent evidence.

---

# Candidate exchange universe

Initial venue set for point-in-time perp eligibility audit:

1. Binance USD-M Futures
2. Bybit Linear Perpetuals
3. OKX SWAP
4. Hyperliquid

Possible later additions:

- Coinbase International perpetuals where relevant
- Derive / Deribit / options venues for payoff research, not the initial alt-rotation universe

No venue is accepted just because a current ticker exists.

---

# Historical eligibility table

Build a canonical table similar to:

```text
asset_id
symbol
rank_source
rank_date
historical_rank
market_cap_usd
market_cap_band
sector
coin_first_seen_date
coin_age_days
venue
contract_id
contract_type
contract_list_time
contract_delist_time
contract_age_days
was_tradable_at_t
quote_asset
settle_asset
volume_24h
liquidity_bucket
eligible_at_t
exclusion_reason
```

Primary key should not rely on ticker alone.

Use stable provider IDs / contract addresses / venue instrument IDs where available.

---

# Rank-band research

Initial bands to study descriptively:

- 1–10
- 11–25
- 26–50
- 51–100
- 101–200
- 201–300
- 301–500

Also allow fixed-width bands for sensitivity research after the base specification is frozen.

Do not tune bands using PnL.

Measure:

- median return,
- breadth,
- rank change,
- market-cap share change,
- volume share change,
- beta to BTC,
- beta to ETH,
- lagged correlation,
- realized volatility,
- dispersion,
- percentage entering / leaving band,
- sector composition,
- persistence of migration.

---

# Rank migration as a market state

Potential features:

```text
rank_t
rank_change_1d
rank_change_3d
rank_change_7d
rank_velocity
rank_acceleration
rank_band_t
band_entry
band_exit
band_persistence
mcap_share_change
volume_rank_change
relative_return_vs_BTC
relative_return_vs_ETH
```

Study placements rather than named coins.

Example question:

> When the 201–300 band gains an average of X positions over Y days after BTC's impulse, what happens next to that band and the adjacent bands?

The exact X and Y must be discovered / preregistered scientifically, not invented around PnL.

---

# BTC / ETH / dominance terrain

Do not reduce BTC dominance to a simple buy/sell signal.

Treat it as one capital-routing state dimension.

Candidate terrain variables:

- BTC return / trend state
- ETH return / trend state
- ETH/BTC relative trend
- BTC market-cap dominance
- stablecoin market-cap share / dominance where valid
- total market cap ex BTC
- total market cap ex BTC/ETH
- alt breadth
- alt dispersion
- rank-band migration
- sector breadth
- funding state
- broad perp OI state if historical data later supports it

Candidate descriptive states:

- BTC_LED_EXPANSION
- BTC_CONCENTRATION
- ETH_BRIDGE_ROTATION
- BROAD_ALT_EXPANSION
- MID_CAP_ROTATION
- LOW_CAP_ROTATION
- SECTOR_ROTATION
- RISK_OFF_RECONCENTRATION
- DISPERSED / NO_CLEAR_ROUTE

Do not force these labels before data inspection.

---

# Long / short relative-resistance logic

One major hypothesis family:

### Relative resistance

When BTC sells off, identify coins / sectors that fall materially less than their historically expected BTC beta.

Possible interpretation:

- local accumulation,
- sector-specific demand,
- capital rotation,
- relative sentiment strength.

### Relative weakness

When BTC rallies, identify coins / sectors that materially underperform their historically expected BTC beta.

Possible short candidate after appropriate confirmation.

Key point:

Use residual / relative moves, not raw percentage return alone.

Candidate variable:

```text
residual_return = actual_alt_return - expected_return_given_BTC_ETH_state
```

Then test whether residual strength / weakness persists or mean-reverts depending on regime.

---

# Lead-lag research

Study BTC → ETH → alt-band → sector → instrument transmission.

Candidate horizons:

- 4h
- 8h
- 12h
- 1d
- 3d
- 7d
- 15d

This broad range intentionally covers both intermediate trend and accumulation / pullback style behavior.

Do not choose a winning horizon after the fact.

Use a frozen horizon family and report all results.

---

# Topology / network idea

Topology is an experimental representation layer, not a required source of complexity.

Start simple.

Represent the market as a time-varying graph:

- nodes = eligible coins / rank bands / sectors,
- edges = correlation, lagged correlation, beta, relative flow or liquidity relationship,
- node attributes = rank, market cap, volume, volatility, sector, perp availability.

First test ordinary graph / network structure:

- community detection,
- hub / centrality migration,
- cluster formation / dissolution,
- BTC / ETH hub strength,
- sector clustering,
- graph connectivity change,
- isolated relative-strength nodes.

Only if ordinary network methods reveal meaningful persistent structure should the lane test more advanced topology such as:

- persistent homology,
- Mapper graphs,
- manifold embeddings,
- topological data analysis of correlation / distance surfaces.

Hard rule:

> topology must add information beyond ordinary correlation, rank migration and simple clustering.

If not, demote it.

---

# Data sources — preliminary map

## Historical ranking / market cap

**Primary candidate:**

- CoinMarketCap Historical Snapshots

**Secondary / enrichment:**

- CoinGecko historical coin data
- CoinGecko categories / market metadata

## DEX / on-chain context

Candidate:

- DexScreener
- CoinGecko on-chain endpoints
- native chain / DEX sources already used by QUANT BOX

DEX data is contextual state / liquidity information unless a specific DEX execution contract is later approved.

## Perpetual availability / metadata

- Binance Futures
- Bybit
- OKX
- Hyperliquid

## Perpetual price / funding

Prefer exchange-native data where possible.

Do not use a market-cap aggregator's price as canonical execution history when native perp history exists.

---

# Point-in-time intersection

The actual tradable universe at time `t` should conceptually be:

```text
Historical Top-500 at t
∩
Minimum coin age at t
∩
Perpetual contract existed at t
∩
Contract age >= minimum listing age
∩
Historical data available at t
∩
Liquidity requirement at t
```

Only this intersection may enter a perp strategy backtest.

This is the central truth rule of the lane.

---

# Delisting problem

Current exchange instrument APIs can create survivorship bias because delisted contracts may disappear from current listings.

Therefore the data audit must explicitly search for:

- closed / delisted instrument query support,
- listing announcement archives,
- delisting announcement archives,
- archived exchange metadata,
- first / last native trade timestamp,
- third-party historical derivatives metadata only as a cross-check.

A current-only symbol list is insufficient for historical universe construction.

---

# Stable identity problem

Ticker reuse / renames / migrations are dangerous.

Examples of issues to guard against:

- token rebrand,
- ticker reuse,
- chain migration,
- contract-address migration,
- wrapped vs native assets,
- 1000-token multiplier perpetuals,
- exchange-specific renamed symbols.

Canonical identity should use a mapping layer such as:

```text
internal_asset_id
CoinMarketCap ID
CoinGecko ID
chain + contract address where applicable
venue + instrument ID
symbol aliases
valid_from
valid_to
```

No symbol-only joins.

---

# Sector mapping

Sector analysis is desirable but taxonomy is unstable.

Store:

- provider sector / category,
- effective date if possible,
- source,
- confidence / mapping method.

Do not silently apply today's sector label to historical dates if the classification changed materially.

Initial broad categories may be more stable than ultra-specific categories.

---

# Execution concept after mechanism discovery

If a terrain state survives mechanism research, the future trend-following expression may use:

- perpetual only,
- next-bar causal entry,
- ATR-normalized invalidation,
- ATR target or trailing exit,
- maximum holding period,
- liquidity / spread constraint,
- funding-aware cost accounting.

ATR may be computed on the contract itself and normalized so nominal token price does not matter.

Potential horizon family:

- 4h
- 12h
- 1d
- 3d
- 7d
- 15d

No fixed ATR multiple should be chosen until a later preregistered strategy-generation checkpoint.

---

# Research stages

## ALT-DATA-0 — point-in-time universe reality audit

Answer:

- Can we reconstruct historical top-500 membership?
- How deep is the snapshot history?
- Can we reconstruct historical perpetual listing intervals?
- How complete are delisted contracts?
- Can identities be mapped safely across providers?

No alpha research.

## ALT-DATA-1 — canonical historical universe

Produce daily / weekly point-in-time eligibility ledger.

No strategy PnL.

## ALT-MECH-1 — rank migration / lead-lag anatomy

Study:

- BTC / ETH lead-lag,
- dominance / market-cap routing,
- rank-band migration,
- breadth,
- relative resistance / weakness,
- sector flow,
- state persistence.

No strategy PnL.

## ALT-MECH-2 — terrain / network topology

Build graph state and test whether topology adds information beyond simple baselines.

Advanced TDA only if justified.

## ALT-ALPHA-1 — strategy generation

Generate:

- channel-the-wave relative-value strategies,
- move-with-stream directional trend strategies,
- long / short relative-resistance strategies,
- ATR execution contracts.

Freeze before PnL.

## ALT-ALPHA-2 — falsification

Run frozen strategies against point-in-time eligible perp universe.

---

# Recommended immediate next action for this lane

Do NOT start the full model while current core ALPHA-2 is running.

The next safe independent checkpoint should be:

`CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`

Its job is only to prove we can build the historical universe without survivorship or listing look-ahead.

The most important deliverable is not a strategy.

It is a trustworthy table answering:

> On date t, which top-ranked altcoins actually existed and had a sufficiently mature perpetual contract available to trade?

If this table cannot be built truthfully, do not backtest the strategy family.

---

# Source links captured during idea preservation

CoinMarketCap historical snapshots:

https://coinmarketcap.com/historical/

Example:

https://coinmarketcap.com/historical/20260701/

CoinGecko API endpoint overview:

https://docs.coingecko.com/reference/endpoint-overview

CoinGecko current markets / ranking:

https://docs.coingecko.com/reference/coins-markets

CoinGecko historical market chart:

https://docs.coingecko.com/reference/coins-id-market-chart

CoinGecko historical range:

https://docs.coingecko.com/reference/coins-id-market-chart-range

Bybit instrument metadata:

https://bybit-exchange.github.io/docs/v5/market/instrument

OKX API / instrument listing metadata:

https://www.okx.com/docs-v5

Binance USD-M Futures exchange information:

https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information

---

# Governing rule

**Names are observations. Flow is the mechanism. Rank is state. Venue availability is a constraint. Execution must be real.**

The lane should follow the market's changing structure, not today's survivor list.
