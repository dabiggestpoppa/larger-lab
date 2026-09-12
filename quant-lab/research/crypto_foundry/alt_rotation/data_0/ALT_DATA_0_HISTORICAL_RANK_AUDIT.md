# ALT-DATA-0 — Historical Rank / Market-Cap Source Audit

**Checkpoint:** `CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`
**Probe date:** 2026-08-24 (UTC). All claims backed by persisted raw probes
(`probes/raw/*`) with SHA256 in `ALT_DATA_0_PROVENANCE_MANIFEST.json`.

## 1. CoinMarketCap (primary)

### 1.1 Official Pro API — PAID_REQUIRED

`pro-api.coinmarketcap.com/v1/cryptocurrency/listings/historical` without a
key → **HTTP 401, error_code 1002 "API key missing"**. The official
historical-listings endpoint is paid.

### 1.2 Internal data-api (used by the website) — WEB_ONLY, keyless, verified

`https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?date=YYYY-MM-DD&start=1&limit=500&convertId=2781`

| property | finding | evidence |
|---|---|---|
| earliest snapshot date | any date (2024-06-01 verified; 2020+ expected; untested deeper) | `cmc_snapshot_20240601_top500.json` |
| latest snapshot date | any date up to present | `cmc_snapshot_20260820_top500.json` |
| snapshot frequency | on-demand per date (daily granularity; the API returns the dated snapshot) | same |
| ranked depth | **500 verified per snapshot** (limit honored) | row_count=500 × 5 dates |
| rank field | `cmcRank` | row 1 = BTC rank 1, row 500 = LTO/HASHAI/SOSO/OG/BARD |
| price / mcap / volume | `quotes[0].price / marketCap / volume24h` with `lastUpdated` = snapshot date | BTC 2024-06-01: price $67,706.94, mcap $1.334T — matches known history |
| circulating supply | `circulatingSupply`, plus `maxSupply`, `totalSupply` | present |
| identity | `id` (stable), `slug`, `name`, `symbol`, `dateAdded` (CMC listing date) | present |
| machine-collectable | YES — plain JSON, no auth, ~1 req/s safe; 5 dates × 500 rows collected without block | 5 × 200 responses |
| anti-bot / rate-limit | none observed at ~1 req/s; internal endpoint, TOS for web use applies | probe log |
| missing-date behavior | not tested for a gap date; snapshots are daily so gaps are data-absence, not API error | — |
| identity consistency through rebrands | CMC keeps `id`; symbol may change. LUNA (id 4172) and LUNC (id 6535) both present in snapshots with correct PIT ranks (LUNC 115 at 2024-06-01, LUNA 140) | snapshot files |

**Earliest verified snapshot:** 2024-06-01. **Latest verified:** 2026-08-20.
**Max verified depth:** 500 ranked rows. Deeper pagination (start>501) not
tested in DATA-0 — flagged for DATA-1.

**Caveat — per-coin historical quotes** (`data-api/v3/cryptocurrency/historical`):
returns `quotes` for a recent window (2026-08-20 verified) but **empty
quotes for 2024-06-01**. Per-coin deep history via the internal API is
PARTIAL; the ranked-snapshot endpoint is the reliable PIT source.

### 1.3 Web page

`coinmarketcap.com/historical/20240601/` → HTTP 200 HTML shell, **table data
is NOT embedded server-side** (0 symbol/rank tokens in HTML). The page is
JS-rendered and hydrates from the internal data-api. Scraping the page
directly is NOT the path; the data-api is.

## 2. CoinPaprika — PARTIAL (free tier)

| capability | finding |
|---|---|
| coin registry | **61,115 coins** incl. `is_active` flag and `type` (coin/token) — inactive assets covered |
| current tickers | `rank`, mcap, price, volume — free |
| historical daily | **1-year rolling window only on free plan.** `tickers/btc-bitcoin/historical?start=2024-05-25` → **HTTP 402**: *"Getting daily historical data before 2025-08-24 ... is not allowed in this plan"*. Same 402 for LUNC 2022 and FTT 2022. Recent window (2026-08-20) → 200. |
| historical **rank** field | **ABSENT** in free-plan historical rows (price/volume_24h/market_cap only). Rank history requires paid tier. |
| old asset IDs | slug IDs; rename handling visible: `luna-terra` now carries symbol **LUNC**; `luna-terra-v2` = LUNA |
| exchange/contract mapping | not probed in DATA-0 (endpoints exist; UNVERIFIED) |

**Can CoinPaprika independently reconstruct historical rank state?** On the
free plan: **NO** — deep history is paid-gated and the free historical rows
carry no rank. It *can* verify mcap/price for the 1-year window and provides
the best free registry of inactive assets. Rank reconstruction would require
the paid tier or a batched mcap-ranking job inside the 1-year window
(61k+ coins × 1 call — feasible as offline batch, ~34h at free-key limits).

## 3. CoinGecko — enrichment only (SURVIVORSHIP / depth limits)

| capability | finding |
|---|---|
| registry | 18,656 coins incl. `platforms` (contract addresses) and dead coins (e.g., `ftx-token`, `serum`, `terra-luna`) |
| current markets | `coins/markets` top-250 verified (never used as historical truth) |
| historical per-coin | `market_chart` capped at **365 days** on public tier (HTTP 401, error 10012: *"Public API users are limited to querying historical data within the past 365 days"*) |
| no-key stability | unstable — 401 (key missing) / 429 (rate limit) observed across calls |
| rank history | none |
| categories | current taxonomy only (`coins/categories/list`, 865 categories) — CURRENT_ONLY |
| historical top-500 reconstruction | **NOT possible from free tier**; requires beginning from today's list for candidate selection → `SURVIVORSHIP_RISK` if used as universe source |

**Role assigned:** enrichment / cross-check inside the 365-day window;
NOT a universe-construction source.

## 4. DEX sources (rank-relevant capabilities)

- **DexScreener**: no ranking. `api.dexscreener.com` was **unreachable from
  this environment** (read timeouts at 45s/60s). `pairCreatedAt` is a
  documented current-pair field (identity/maturity referee role only).
- **DexPaprika**: no ranking. Token `added_at` = first-indexed date (NOT
  contract creation — WETH shows 2026-05-31). Pool `created_at` +
  `created_at_block_number` verified (Uniswap V3 WETH pool = 2021-05-05,
  the true deployment date). See `ALT_DATA_0_SECTOR_MAPPING_AUDIT.md` /
  consensus matrix for the referee role.

## 5. Verdict

- **Historical top-500 reconstruction: FEASIBLE and DEMONSTRATED** for the
  5 prototype dates via CMC's internal data-api (web-only, keyless,
  machine-collectable, 500-deep, PIT by construction).
- **No current-universe dependence:** snapshots are dated CMC state; fallen
  coins (LUNC #115, FTT #138, HOT #163 on 2024-06-01) appear at their true
  PIT ranks. See `ALT_DATA_0_RANK_SURVIVORSHIP_AUDIT.md`.
- **Cross-check depth:** for dates inside the 1-year free window
  (2026-01-01, 2026-08-20) CoinPaprika provides an independent mcap check;
  for older dates the free stack has no independent second provider →
  **CROSSCHECK_GAP for pre-2025-08 dates on free tier** (paid CoinPaprika /
  CMC Pro closes it).
