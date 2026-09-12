# ALT-DATA-0.1 — Historical Liquidity Path

**Checkpoint:** `CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR`
**Purpose:** separate *contract existence / maturity / data* from *historical
liquidity verification*, and document what DATA-1 can and cannot use.

## 1. Truth separation (Repair 4)

The DATA-0 report previously stated "mature, **liquid** perpetual contract
actually available" while historical liquidity was not verified. Corrected:

| dimension | definition | status in DATA-0.1 |
|---|---|---|
| CONTRACT_EXISTENCE_ELIGIBLE | contract existed at t | computed per venue (HL/OKX); Binance/Bybit unverifiable from env |
| CONTRACT_MATURITY_ELIGIBLE | existed at t and age >= 30d | computed |
| HISTORICAL_DATA_ELIGIBLE | historical price + funding + volume available at t | HL YES; OKX PARTIAL; Binance YES_ARCHIVE (listing unverified); Bybit BLOCKED |
| HISTORICAL_LIQUIDITY_VERIFIED | historical liquidity actually verified under a frozen rule | **NOT VERIFIED for any venue in DATA-0/0.1** |

Terminal status is **ELIGIBLE_EX_LIQUIDITY** (never `FULLY_ELIGIBLE`).
`FULLY_ELIGIBLE` is not used anywhere.

## 2. Per-venue historical liquidity sources

| venue | historical volume? | depth period | price? | funding? | OI? | bid/ask? | DEX liquidity? |
|---|---|---|---|---|---|---|---|
| Binance (archive) | **YES** — klines quote/taker volume, 2020-01+ incl. delisted symbols | 2020-01 → present, monthly zips | YES (klines) | YES (fundingRate monthly files) | **NO** — OI history not verified (metrics files 404 in probe) | NO — no historical L2 | n/a (CEX) |
| Hyperliquid | **YES** — candle volume after valid listing (v>0 filter; zero-volume backfill before first funding must be excluded) | listing (2023-05-12+) → present | YES | YES (hourly fundingHistory) | **NO** — openInterest is current snapshot only | NO | n/a (CEX-like) |
| OKX | **PARTIAL** — history-candles retention is instrument-dependent (BTC-USDT-SWAP back to 2020-09 verified; BTC-USD-SWAP 2018 window empty) | partial | PARTIAL | PARTIAL (funding recent window only) | NO | NO | n/a |
| Bybit | **BLOCKED from this environment** (403 CloudFront) | — | BLOCKED | BLOCKED | BLOCKED | NO | n/a |
| DexPaprika (DEX) | **CURRENT_ONLY** — 24h/7d/30d windows; no deep history | current only | current | n/a | n/a | n/a | **YES current** (liquidity_usd per pool) |
| DexScreener (DEX) | unreachable from env (timeouts) | — | — | — | — | — | current only (documented) |

## 3. What DATA-1 can use (frozen intent, not yet built)

1. **Contract existence/maturity ledger** — HL first/last funding, OKX
   listTime, Binance archive first/last bar (INFERRED). Already prototyped.
2. **Historical volume proxy** — Binance archive quote volume (2020-01+) and
   HL candle volume (post-listing, v>0). These are *volume data*, usable as a
   liquidity *proxy*, NOT verified liquidity (no order book, no spread).
3. **Funding state** — Binance archive fundingRate + HL fundingHistory.
4. **DEX-side market age** — DexPaprika pool `created_at` (verified) as a
   market-maturity referee; current liquidity only.
5. **Explicitly NOT available historically (free stack):** L2 order books,
   bid/ask spread, realized slippage, historical open interest (HL/OKX),
   historical DEX liquidity depth.

## 4. DATA-1 rule (preregistered)

- Any eligibility claim that includes liquidity MUST be labeled
  `liquidity_proxy=historical_volume` (or `unverified`) — never "verified
  liquidity".
- `HISTORICAL_LIQUIDITY_VERIFIED` stays FALSE until a frozen rule
  (e.g., min historical volume percentile AND min maturity) is applied to
  actual historical volume data and the rule is preregistered.
- Do NOT invent L2 historical liquidity. There is no free L2 history in the
  audited stack.
