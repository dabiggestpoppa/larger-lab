# ALT-DATA-0 — Perpetual Listing / Universe Audit

**Probe date:** 2026-08-24 (UTC). Evidence in `probes/raw/*`, hashes in
`ALT_DATA_0_PROVENANCE_MANIFEST.json`.

Goal: reconstruct `LIST_TIME / DELIST_TIME / ACTIVE_INTERVAL` per venue.

## 1. Binance USD-M Futures

| item | finding |
|---|---|
| live API access | **GEO-BLOCKED from this environment**: `fapi.binance.com/fapi/v1/*` → HTTP 451 *"Service unavailable from a restricted location"* (also `api.binance.com` spot). `data-api.binance.vision` (spot mirror) → 200. |
| exchangeInfo fields | `onboardDate`, `deliveryDate`, `status`, `contractType` documented; live fetch BLOCKED from env → `DOCUMENTED_NOT_LIVE` |
| official bulk archive | **`data.binance.vision` WORKS** (not geo-blocked): USD-M monthly `klines` and `fundingRate` zips |
| archive depth | monthly files verified **2020-01+** for BTCUSDT (2019-10/2019-12 and daily 2019-09-08 → 404; archive begins 2020-01) |
| delisted recovery | monthly klines retained for delisted symbols: **SRMUSDT 2022-10 (32 rows incl. final trading day)**, **FTTUSDT 2022-11 (31 rows; last candle zero-volume delisting tail)** |
| funding archive | `fundingRate` monthly files incl. delisted: BTCUSDT 2024-06 (200), **SRMUSDT 2022-10 (200)** |
| 1000x naming | archive confirms convention: `1000PEPEUSDT`, `1000SHIBUSDT`, `1000BONKUSDT` exist; `PEPEUSDT` → 404 |
| renamed contracts | `LUNA2USDT` (Terra 2.0) — 2022-07 file 404; rename logic must be handled via identity map |
| listing-time rule | live `onboardDate` = OFFICIAL (blocked here); archive first bar = `INFERRED_FIRST_DATA_TIMESTAMP` (2020-01+); **must not use first observed local bar when onboardDate is recoverable** |

**LIST_TIME feasibility:** PARTIAL from this env (archive-derived INFERRED
first-bar 2020-01+; official onboardDate requires non-blocked egress).
**DELIST_TIME feasibility:** PARTIAL (archive last-bar per symbol; verified
for SRMUSDT/FTTUSDT).

## 2. Bybit Linear Perpetuals

| item | finding |
|---|---|
| live API access | **GEO-BLOCKED**: `api.bybit.com/v5/*` → HTTP 403 *"CloudFront distribution is configured to block access from your country"* |
| instrument fields | `launchTime`, `deliveryTime`, `status`, `contractType`, `baseCoin`, `quoteCoin`, `settleCoin` — documented; live verification BLOCKED → `DOCUMENTED_NOT_LIVE` |
| Closed instruments queryable | documented as queryable with `status`; live proof blocked |
| delisting interval reconstruction | would be strong (launchTime + status=Closed); unverifiable from this env |
| symbol renames | handled at identity layer (documented) |

Bybit is a **strong candidate venue but unverifiable from this environment**
(US geo-block). Any DATA-1 dependency must run from a non-blocked egress or
use archives.

## 3. OKX SWAP

| item | finding |
|---|---|
| instruments | `GET /api/v5/public/instruments?instType=SWAP` → **200, 454 swaps** (453 `live`, 1 `preopen`) |
| listTime | present per instrument; earliest **2018-08-28** (BTC-USD-SWAP, inverse), 439 USDT + 15 USD quoted |
| listing reconstruction | **PRIMARY_VERIFIED** — official `listTime` for all current swaps |
| delisting | **NOT SUPPORTED**: delisted swaps silently omitted. `FTT-USDT-SWAP` and `SRM-USDT-SWAP` → **200 with empty data** (no error, no archive) |
| funding history | `funding-rate-history` → recent window only (before=2023 → returned 2026-05 rows; after=0 → empty). `PARTIAL` |
| candles | `history-candles` deep for some instruments (BTC-USDT-SWAP → 2020-09 rows verified) but retention is instrument-dependent (BTC-USD-SWAP 2018 window → empty). `PARTIAL` |
| announcements | OKX delisting announcements exist on the website (archive method); not API-accessible |

**LIST_TIME feasibility:** YES (live, official). **DELIST_TIME feasibility:**
NO via public API (archive/announcements required).

## 4. Hyperliquid

| item | finding |
|---|---|
| universe | `POST /info {"type":"meta"}` → **232 coins** (names, szDecimals, maxLeverage, `isDelisted` flags) |
| first existence | `{"type":"fundingHistory","coin":X,"startTime":0}` returns the OLDEST funding window → **first funding timestamp per coin**. Verified **232/232 coins**; earliest **2023-05-12T00:00:00Z** (BTC/ETH/ATOM/MATIC/DYDX/SOL/AVAX/BNB — HL launch day) |
| listing authority | no official list-time metadata in API → first funding = `INFERRED_FIRST_DATA_TIMESTAMP` (lower bound; funding starts at listing, hour 0) |
| delisting | `isDelisted` flags + `last_funding_ts`; **55 delisted coins recovered with full funding intervals** (FTT 2023-09-25→2023-10-16, JELLY 2025-01-30→2025-02-20, OM 2025-02-16→2025-03-09, MATIC/RNDR/MKR renames, ...) |
| purged coins | coins fully removed from the index → fundingHistory **HTTP 500** (LUNA2/LUNC/SRM/HOT/BTS) → NOT recoverable via public API |
| candle hazard | `candleSnapshot` backfills **zero-volume pre-listing candles** (BTC first candle 2020-08-18, v=0, n=0 — 3 years before first funding). **NEVER infer listing from candles on HL.** |
| renames | meta keeps legacy names as `isDelisted` (MATIC→POL, RNDR→RENDER, MKR→SKY) — identity-layer handling required |

**LIST_TIME feasibility:** YES (INFERRED first-funding, 2023-05-12+).
**DELIST_TIME feasibility:** YES for coins retained in meta (INFERRED
last-funding); NO for purged coins.

## 5. Cross-venue listing anchors (verified)

| venue | anchor | earliest verified |
|---|---|---|
| OKX | official `listTime` | 2018-08-28 |
| Binance archive | first monthly kline/funding file | 2020-01 |
| Hyperliquid | first funding ts | 2023-05-12 |
| Bybit | `launchTime` (documented, live-blocked) | — |
