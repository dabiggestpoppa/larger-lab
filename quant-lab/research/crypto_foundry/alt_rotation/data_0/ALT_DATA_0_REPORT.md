# ALT-DATA-0 — Point-in-Time Ranking & Perp Universe Reality Audit — REPORT

**Checkpoint:** `CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`
**Branch:** `agent/crypto-quant-foundry`
**Base SHA (commit parent):** `47c9d09f077e387b99740b0d7236f1e7fb3818cf`
**Base SHA note:** at session start the local branch was `5a6a4407` and
`47c9d09f` was absent locally; mid-session the worktree fast-forwarded via
`git pull origin agent/crypto-quant-foundry` to `47c9d09f` — the brief's
stated branch head, which contains the original alt-rotation planning docs
(`058a2d69` + `47c9d09f`). All work in this checkpoint sits on top of
`47c9d09f`.
**Run date:** 2026-08-24 (UTC)
**Decision:** `PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`

> Data reality only. No alpha, no PnL, no optimization, no execution, no ML,
> no trading rules were produced in this checkpoint.

---

## 0. Core question — answered

> For any historical date t: which assets were actually in the historical
> top-500 at t, which sector did they belong to at t (where verifiable), and
> which had a mature, liquid perpetual contract actually available at t?

**Answer: YES, this is answerable.** The historical top-500 is recoverable
as a dated snapshot from CMC's web data-api (verified for 5 dates,
500-deep, PIT by construction, no current-universe dependence). Historical
perp availability is recoverable from OKX `listTime`, Hyperliquid
funding-history first timestamps (232/232 coins), and the Binance bulk
archive (2020-01+, incl. delisted symbols). Delisted-contract recovery is
demonstrated on two independent paths. Sector classification is
`HISTORICAL_APPROXIMATION` at best (no free provider offers true PIT
sectors) and is labeled as such everywhere.

---

## 1. What was probed (89 persisted raw samples)

| layer | sources | live status from this environment |
|---|---|---|
| rank/mcap | CoinMarketCap (web data-api + Pro API probe + web page), CoinPaprika, CoinGecko | CMC data-api WORKS (keyless, web-only); CoinPaprika free = 1yr window; CoinGecko free = 365d cap, unstable no-key |
| DEX | DexScreener, DexPaprika | DexScreener UNREACHABLE (timeouts); DexPaprika WORKS |
| perp | Binance (live + archive), Bybit, OKX, Hyperliquid | Binance live 451 geo-block, archive WORKS; Bybit 403 geo-block; OKX WORKS; Hyperliquid WORKS |

## 2. Headline findings

1. **CMC internal data-api returns true PIT ranked snapshots** —
   `data-api/v3/cryptocurrency/listings/historical?date=YYYY-MM-DD` —
   keyless, 500-deep, plain JSON. BTC at 2024-06-01: $67,706.94, mcap
   $1.334T (matches history). Fallen coins appear at true PIT ranks
   (LUNC #115, FTT #138, HOT #163 on 2024-06-01). **This is the PIT rank
   primary source.**
2. **CMC official Pro API is paid** (401 without key); the web page is
   JS-rendered (no embedded table); the internal data-api is the
   machine-collectable path (web-use TOS applies).
3. **CoinPaprika free plan = 1-year rolling daily window, no rank field,
   deep history paid** (HTTP 402). Rank history requires the paid tier.
4. **CoinGecko public = 365-day history cap** (error 10012) and unstable
   without a key → enrichment only, `SURVIVORSHIP_RISK` if used as
   universe source.
5. **OKX**: official `listTime` for 454 current swaps (earliest
   2018-08-28) — PRIMARY listing source. Delisted swaps silently omitted
   (200 + empty) — delisting NOT recoverable via public API.
6. **Hyperliquid**: no official list-time metadata; **first-funding
   timestamp** per coin (232/232 recovered, earliest 2023-05-12) is the
   honest `INFERRED_FIRST_DATA_TIMESTAMP`. `isDelisted` flags + funding
   intervals recover 55 delisted contracts (FTT, JELLY, OM, ...). Purged
   coins → HTTP 500 (unrecoverable via API).
7. **Binance live fapi is geo-blocked (451) from this environment**, but
   the official bulk archive `data.binance.vision` WORKS: monthly klines
   AND fundingRate, **2020-01+, including delisted symbols** (SRMUSDT
   2022-10, FTTUSDT 2022-11 verified). 1000x naming convention verified
   (`1000PEPEUSDT` exists, `PEPEUSDT` doesn't).
8. **Bybit is geo-blocked (403 CloudFront)**; `launchTime`/`status=Closed`
   documented but unverifiable from here.
9. **Hyperliquid candles are backfilled with zero-volume pre-listing
   candles** (BTC first candle 2020-08-18, v=0 — 3 years before first
   funding). **Never infer listing from HL candles.**
10. **Sector tags on CMC snapshots are date-varying** (BTC: 30 tags in
    2024 vs 37 in 2026) → `HISTORICAL_APPROXIMATION`, not CURRENT_ONLY.

## 3. Prototype results (Tasks 11, 12, 16)

PIT top-500 reconstructed for 5 dates; perp eligibility computed per
asset × date × venue (HL and OKX live-verified; Binance/Bybit rows marked
`UNVERIFIABLE_FROM_ENV`).

| date | top-500 | any perp (HL∪OKX) | mature ≥30d | fully eligible (HL∪OKX) |
|---|---|---|---|---|
| 2024-06-01 | 500 | 189 | 143 | 143 |
| 2025-01-01 | 500 | 212 | 164 | 164 |
| 2025-06-01 | 500 | 223 | 188 | 188 |
| 2026-01-01 | 500 | 215 | 194 | 194 |
| 2026-08-20 | 500 | 209 | 203 | 203 |

- Counts are **lower bounds**: Binance (largest perp universe) and Bybit
  are geo-blocked live; their archive methods are documented and would add
  coverage in DATA-1.
- **Maturity verdict: `30D_FEASIBLE`.** The 30-day rule removes a modest
  share (e.g., 2024-06-01: 189→143; 2026-08-20: 209→203). The binding
  constraint is venue coverage, not the maturity rule. Not tuned against
  returns (preregistered).

## 4. Coverage by rank band (aggregate, all dates)

| band | n | any perp (HL∪OKX) | mature30 (HL∪OKX) | fully eligible |
|---|---|---|---|---|
| 1-10 | 200 | 45 | 44 | 44 |
| 11-25 | 300 | 60 | 54 | 54 |
| 26-50 | 500 | 104 | 93 | 93 |
| 51-100 | 1000 | 189 | 169 | 169 |
| 101-200 | 2000 | 298 | 268 | 268 |
| 201-300 | 2000 | 89 | 72 | 72 |
| 301-500 | 4000 | 263 | 192 | 192 |

Top-100 bands are well covered (≈65-80% perp-eligible on HL/OKX). The
lower half (201-500) is sparse — and diagnosis shows why: CMC ranks
201-500 are dominated by wrapped/LST/stablecoin assets (stETH, WBETH,
WBTC, WETH, USDS, USDY, sUSDe, ...) that legitimately have no perps, plus
genuinely small altcoins with thin perp coverage. Binance/Bybit would lift
the lower bands, but the honest free-stack answer is:
**the lower half of top-500 is only partially perp-tradable, and much of
the 201-500 band is structurally non-tradable (wrapped/stable proxies).**

## 5. Identity mapping (Task 9)

- 949 canonical identities (`identity/canonical_identity_map.csv`),
  anchored on `CMC:<id>`; 915 joined to CoinGecko, 924 to CoinPaprika.
- **608 symbols flagged for ticker reuse** — never silently joined.
- Rules for renames (MATIC→POL, RNDR→RENDER, MKR→SKY), wrapped vs native
  (distinct assets), chain migration, 1000x perp aliases (venue symbol,
  not asset rename) — spec in `ALT_DATA_0_IDENTITY_MAPPING_SPEC.md`.

## 6. Sector mapping (Task 10)

- CMC dated tags = `HISTORICAL_APPROXIMATION` (date-varying, taxonomy
  drift unverified); CoinGecko categories = `CURRENT_ONLY`; everything
  else = `UNMAPPED`. No true PIT sector source in the free stack.
- No current-only sector was presented as historical (fail-closed rule
  respected).

## 7. Survivorship tests (Tasks 13-14)

- **Delisted contracts:** Hyperliquid funding history recovers 55 delisted
  contracts (FTT/JELLY/OM with full intervals); Binance archive retains
  delisted monthly klines+funding (SRMUSDT, FTTUSDT verified). OKX omits
  delisted swaps; purged HL coins → 500. Gap documented; archive method
  exists → **no blocking flag**.
- **Rank:** dated snapshots contain fallen/dead coins at true PIT ranks
  (LUNC/FTT/HOT/XEM/DGB...) that are absent from today's top-250 →
  **no current-universe dependence** → no `RANK_UNIVERSE_SURVIVORSHIP_RISK`.
- **Cross-provider consistency (2026-08-20):** BTC −2.4%, ETH −1.9%,
  HOT −2.1% vs CoinPaprika; LUNC +19.7% and FTT −60.3% flagged as
  provider disagreements (supply-definition differences) — recorded, not
  silently resolved.

## 8. Free vs paid (Task 17)

All probes used free access; **nothing was purchased.** Classes:
FREE_CONFIRMED (DexPaprika, Binance archive, OKX, Hyperliquid), FREE_LIMITED
(CMC data-api web-only + Pro paid; CoinPaprika 1yr window; CoinGecko 365d
cap), PAID_REQUIRED (CMC Pro API historical listings, CoinPaprika deep
history, CoinGecko full history). Full matrix:
`ALT_DATA_0_FREE_VS_PAID_MATRIX.csv`.

## 9. Multi-horizon readiness (Task 18)

- CMC snapshots support 1D-90D for mcap/price/volume/rank (per-date
  snapshot calls; batch ~90 calls per asset panel).
- Binance archive supports perp price/volume/funding 1D-90D (2020-01+).
- HL supports perp price/volume/funding since listing (2023-05-12+) with
  the zero-volume backfill filter.
- OKX perp candles/funding PARTIAL (retention limits); Bybit
  NOT_SUPPORTED from env; DEX liquidity historical NOT_SUPPORTED (free).
- Details: `ALT_DATA_0_MULTI_HORIZON_READINESS.csv`.

## 10. Topology readiness (Task 20)

`TOPOLOGY_DATA_READY` for rank, sector (approx), mcap, volume, price
returns, BTC/ETH beta, perp availability. **GAP:** historical liquidity
(perp + DEX) is current-only in the free stack (documented).

## 11. Fail-closed rules — status

| rule | status |
|---|---|
| historical ranking from today's survivor universe | NOT VIOLATED (dated snapshots) |
| perp availability from today's symbol list only | NOT VIOLATED (list/delist intervals; current-only rows labeled) |
| delisted contracts unrecoverable | NOT VIOLATED (two proven recovery paths) |
| symbol-only identity joins | NOT VIOLATED (canonical CMC id anchor; symbol joins flagged) |
| current-only sectors presented as historical | NOT VIOLATED (HISTORICAL_APPROXIMATION vs CURRENT_ONLY labeled) |
| missing provenance | NOT VIOLATED (89 probes, SHA256, manifest) |

## 12. Blockers

**None blocking.** Residual, documented limitations (all handled in DATA-1):

1. Binance/Bybit live APIs geo-blocked from this environment → DATA-1
   ledger must use archives (Binance verified) or a non-blocked egress.
2. Free-tier cross-check gap for dates before 2025-08 (single-provider
   CMC for old dates; paid CoinPaprika/CMC Pro closes it).
3. HL purged coins and OKX delisted swaps unrecoverable via public API →
   archive collection task.
4. Historical liquidity (perp/DEX) current-only in free stack.

## 13. Artifacts

See `ALT_DATA_0_PREREGISTRATION.md` for the fixed list. All 17 required
artifacts produced; raw probes under `probes/raw/` (89 samples + 232 HL
funding files); scripts under `scripts/`; tests under `tests/`.

## 14. Next checkpoint

`CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL`
— NOT started in this run.
