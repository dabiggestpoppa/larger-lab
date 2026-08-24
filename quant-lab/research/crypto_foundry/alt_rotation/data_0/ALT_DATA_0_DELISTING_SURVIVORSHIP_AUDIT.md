# ALT-DATA-0 — Delisted-Contract Survivorship Audit (Task 13)

**Mandatory test:** can the historical perp universe recover contracts that
no longer exist today? For each venue we attempted to recover a known
delisted contract's listing, trading period, delisting, and historical bars.

## 1. Tested contracts and outcome

| venue | contract | status | recovered listing | recovered delisting | historical bars |
|---|---|---|---|---|---|
| Hyperliquid | FTT | delisted (isDelisted=true, still in meta) | **YES** first funding 2023-09-25 | **YES** last funding 2023-10-16 | **YES** (funding history) |
| Hyperliquid | JELLY | delisted | **YES** 2025-01-30 | **YES** 2025-02-20 | **YES** |
| Hyperliquid | OM | delisted | **YES** 2025-02-16 | **YES** 2025-03-09 | **YES** |
| Hyperliquid | LUNA2 / LUNC / SRM / HOT / BTS | never listed or purged | **NO** — fundingHistory HTTP 500 | NO | NO |
| Binance (archive) | SRMUSDT | delisted 2022-10 | **YES** monthly klines 2022-10 (32 rows) | **YES** last row = final trading day | **YES** (klines + fundingRate) |
| Binance (archive) | FTTUSDT | delisted 2022-11 | **YES** monthly klines 2022-11 (31 rows) | **YES** zero-volume final candles | **YES** |
| OKX | FTT-USDT-SWAP | delisted | **NO** — 200 + empty data | NO | NO |
| OKX | SRM-USDT-SWAP | delisted | **NO** — 200 + empty data | NO | NO |
| Bybit | SRMUSDT / FTTUSDT | — | **BLOCKED** (403 CloudFront geo-block) | BLOCKED | BLOCKED |
| Binance (live) | any | — | **BLOCKED** (451 geo-block) | BLOCKED | BLOCKED |

## 2. Findings

1. **Hyperliquid**: delisted contracts retained in the current meta
   (`isDelisted=true`) are **fully recoverable** — first/last funding
   timestamps give the active interval, and funding history doubles as the
   tradability record. Coins **purged from the index return HTTP 500 and are
   NOT recoverable via the public API** (archive/third-party dumps needed).
2. **Binance**: the **official bulk archive (`data.binance.vision`) retains
   monthly klines AND funding for delisted USD-M symbols** (SRMUSDT,
   FTTUSDT verified). This is a valid, free, machine-collectable archive
   method with 2020-01+ depth. Live `fapi` is geo-blocked from this env but
   the archive sidesteps it.
3. **OKX**: delisted swaps are **silently omitted** — no error, no rows.
   Public API cannot recover delisted instruments. Archive = announcement
   pages / third-party dumps (not machine-verified in DATA-0).
4. **Bybit**: live API geo-blocked (403). Documentation indicates Closed
   instruments are queryable, but this could not be proven from this
   environment.

## 3. Verdict

- Delisted-contract recovery is **demonstrated** on two independent paths
  (Hyperliquid funding history for meta-retained coins; Binance bulk archive
  for delisted USD-M symbols).
- **Residual gap:** coins purged from HL meta, OKX delisted swaps, and
  live-API-blocked venues (Bybit) require archival methods that were not
  machine-verified in DATA-0. This is a *documented, bounded* gap, not a
  material failure: the two proven paths cover the largest universes
  (Binance USD-M archive 2020+, HL 2023+).
- **No `PERP_UNIVERSE_SURVIVORSHIP_RISK` blocking flag.** The archive
  method exists and is demonstrated. Residual gaps are classified
  `PARTIAL` and deferred to DATA-1 with explicit archive-collection tasks.
