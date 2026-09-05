# QUANT BOX — London Strategic Edge Integration Plan

**Checkpoint:** `INFRA-LSE-0`
**Branch:** `agent/crypto-quant-foundry`
**Purpose:** Add London Strategic Edge (LSE) as a lightweight external data/reference layer for QUANT BOX without changing canonical execution or strategy logic.

## Why this branch

Use `agent/crypto-quant-foundry` for the first integration pass because:

- the branch is already exercising external data-provider governance,
- it has the strongest current provenance / manifest / quality-gate discipline,
- LSE can immediately serve as a secondary reference for BTC/ETH and later expand to FX, futures, indices, macro, and options,
- this keeps the first build isolated from `main`, execution runtime, capital routing, and the canonical CEREBUS engines.

This is a staging location only. If the adapter proves useful across multiple labs, promote the interface into shared infrastructure later through a separate reviewed checkpoint.

---

# Objective

Build a small, provider-neutral LSE adapter and reality audit that answers one question:

> Can London Strategic Edge become a trusted, low-cost external data and replication layer for QUANT BOX?

Do not turn this into a large platform rewrite.

The first pass should prove:

1. authentication works,
2. historical REST access works,
3. live WebSocket access works,
4. symbol / asset-class coverage matches our practical needs,
5. returned timestamps / prices / fields are stable enough to normalize,
6. a small set of LSE observations can be compared against existing trusted sources,
7. free-vs-paid capability is documented from observed behavior and official LSE documentation,
8. the adapter is reusable without making LSE a hard dependency.

---

# Role inside QUANT BOX

LSE is **not** the canonical execution source.

It should initially serve four roles:

## 1. External historical data source

Candidate use:

- FX
- equities
- futures
- commodities
- indices
- crypto reference data
- bond yields
- macro series
- COT
- economic calendar
- options / Greeks where exposed

All LSE data enters as an external source with explicit provenance.

## 2. Live reference / parity feed

Use live LSE data to compare against:

- broker FX / CFD feeds,
- Hyperliquid crypto state,
- exchange-native sources,
- other canonical market feeds.

LSE divergence should trigger investigation, not automatic source replacement.

## 3. Cross-asset / macro state input

Potential later use for:

- rates state,
- DXY / FX complex,
- equity / volatility regime,
- crude / commodity context,
- COT positioning,
- macro-event context,
- options-volatility state.

No macro strategy logic is added during `INFRA-LSE-0`.

## 4. Independent research / backtest referee

Where practical, use LSE's own research/backtest environment as an independent reproduction check for selected strategies or mechanisms.

QUANT BOX remains canonical for research decisions.

---

# Scope — keep it small

Create a provider adapter plus a compact audit.

Suggested structure:

```text
quant-lab/research/infrastructure/lse/
├── LSE_INTEGRATION_PLAN.md
├── LSE_CAPABILITY_AUDIT.md
├── LSE_FREE_VS_PAID_MATRIX.csv
├── LSE_SOURCE_REGISTRY.json
├── LSE_PARITY_AUDIT.csv
├── adapter/
│   ├── lse_client.py
│   ├── schemas.py
│   └── normalize.py
└── tests/
    └── test_lse_adapter.py
```

Do not create a giant framework.

---

# First-pass symbols / datasets

Test a deliberately small representative basket.

## FX

- EURUSD
- USDCHF

## Futures / index / volatility

- ES or equivalent S&P futures
- crude oil / CL or best documented equivalent
- VIX or equivalent supported volatility series

## Crypto

- BTC
- ETH

## Macro / rates

- US 2Y yield
- US 10Y yield
- one economic-calendar endpoint / dataset
- one COT dataset if available

## Options

- one liquid U.S. underlying, preferably SPY or SPX if supported
- retrieve one chain / Greeks sample if the free API exposes it

The purpose is coverage testing, not exhaustive ingestion.

---

# Free vs paid reality audit

Do not rely only on marketing language.

For every tested capability record:

- `FREE_CONFIRMED`
- `FREE_LIMITED`
- `PAID_REQUIRED`
- `ENTERPRISE_ONLY`
- `NOT_AVAILABLE`
- `UNVERIFIED`

Audit at minimum:

- historical REST access,
- maximum historical depth,
- max rows / request,
- rate limits,
- symbol concurrency,
- live WebSocket prices,
- tick frequency,
- WebSocket reconnect behavior,
- Level 1,
- Level 2,
- Level 3,
- options chains,
- options Greeks,
- macro series,
- bond yields,
- COT,
- economic calendar,
- backtest API / jobs,
- export formats,
- strategy / Brue access if exposed,
- broker / account / order endpoints.

Do not infer that a capability is free simply because it appears in documentation.

---

# Adapter contract

The initial client should expose a very small provider-neutral interface.

Example conceptual methods:

```python
get_historical_bars(symbol, timeframe, start, end)
get_latest_quote(symbol)
stream_quotes(symbols)
get_macro_series(series_id, start, end)
get_options_snapshot(symbol)
```

Only implement methods the API actually supports.

No fake placeholders marked as working.

---

# Normalization rules

Normalize to QUANT BOX conventions:

- UTC timestamps,
- explicit venue / provider,
- explicit symbol / instrument identifier,
- source timestamp vs ingest timestamp,
- OHLCV where relevant,
- bid / ask separated from last,
- options fields preserved rather than flattened,
- macro frequency / revision metadata preserved where available.

Every record must retain enough source metadata to reproduce the fetch.

---

# Provenance

Every collected test dataset should record:

- provider = London Strategic Edge,
- endpoint,
- request parameters,
- symbol,
- requested range,
- returned range,
- row count,
- first timestamp,
- last timestamp,
- collector version,
- schema version,
- SHA256 if persisted,
- access class (`FREE`, `PAID`, etc.),
- known limitations.

No anonymous external files.

---

# Parity audit

Use LSE as an independent reference against existing trusted sources.

Minimum comparisons:

## Crypto

BTC / ETH:

- LSE vs Hyperliquid or frozen crypto reference data

## FX

EURUSD / USDCHF:

- LSE vs available broker / canonical research data

## Futures / index

One S&P-related series or crude series against an existing source if readily available.

Report:

- aligned rows,
- median difference,
- p95 absolute difference,
- correlation,
- missing timestamps,
- obvious stale periods,
- symbol-definition mismatch.

Do not call price differences "bad" until contract differences are ruled out.

---

# Live WebSocket audit

Run a bounded live test only.

Suggested duration:

- 10–30 minutes

Observe:

- connection success,
- authentication,
- symbols accepted,
- message schema,
- timestamp quality,
- update frequency,
- reconnect behavior,
- stale periods,
- duplicate messages,
- documented vs observed symbol limit.

No 24/7 collector required yet.

---

# Backtest / research audit

If LSE exposes a free backtest endpoint or web/API workflow:

run one trivial deterministic strategy only to test reproducibility.

Example:

- fixed moving-average crossover or buy-and-hold control,
- one instrument,
- fixed range,
- no optimization.

Purpose:

- verify the engine works,
- inspect costs / fills / timestamps / data assumptions,
- determine whether results can serve as independent replication evidence later.

Do not evaluate alpha in this checkpoint.

---

# Hard boundaries

`INFRA-LSE-0` must NOT:

- replace canonical feeds,
- alter CEREBUS rules,
- modify trading strategies,
- authorize execution,
- route capital,
- create live orders,
- build ML models,
- optimize strategies,
- import LSE performance claims as QUANT BOX truth,
- assume free access where not directly verified.

---

# Pass criteria

`PASS_LSE_INTEGRATION_FOUNDATION` requires:

1. LSE authentication works.
2. At least one historical price request works.
3. At least one live WebSocket symbol works, if free live access is currently available.
4. At least three different asset/data families are successfully queried.
5. Returned data can be normalized into QUANT BOX schema.
6. Provenance is persisted.
7. Free-vs-paid matrix is evidence-based.
8. At least one parity comparison is completed.
9. No canonical source is silently replaced.
10. Tests pass.

Otherwise use:

- `PARTIAL_LSE_INTEGRATION_FOUNDATION`
- `FAIL_LSE_INTEGRATION_FOUNDATION`

---

# Suggested implementation sequence

Keep this to one short agent checkpoint:

### Step 1 — API reality audit

Read official LSE API / WebSocket / data documentation and record endpoints, authentication, limits, and access classes.

### Step 2 — Small adapter

Implement only the endpoints required for the representative basket.

### Step 3 — Historical samples

Fetch representative FX, crypto, futures/index, macro/rates, and options samples where supported.

### Step 4 — Live test

Run bounded WebSocket test.

### Step 5 — Normalize + provenance

Persist small samples and manifests.

### Step 6 — Parity

Compare a few overlapping instruments against existing trusted data.

### Step 7 — Decision

Produce capability matrix + final decision.

Then STOP for review.

---

# Required final artifacts

At minimum:

- `LSE_CAPABILITY_AUDIT.md`
- `LSE_FREE_VS_PAID_MATRIX.csv`
- `LSE_SOURCE_REGISTRY.json`
- `LSE_PARITY_AUDIT.csv`
- small provider adapter
- adapter tests
- `LSE_INTEGRATION_DECISION.json`

---

# Future promotion if successful

If `INFRA-LSE-0` passes, later checkpoints may use LSE for:

- shared historical data access,
- cross-asset macro/regime inputs,
- live reference/parity monitoring,
- independent backtest replication,
- options / volatility research,
- BSC / Solana / crypto cross-market context where LSE coverage is useful,
- Strategy Foundry source diversification.

Do not move the adapter into shared production infrastructure until at least two separate research lanes demonstrate actual use.

---

# Recommended next checkpoint

`INFRA-LSE-0-LONDON-STRATEGIC-EDGE-REALITY-AUDIT-AND-ADAPTER`

Use this plan as the build contract.

Commit only after the audit / adapter checkpoint completes, then stop for human review before any cross-branch promotion.
