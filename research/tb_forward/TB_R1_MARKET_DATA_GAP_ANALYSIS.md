# TB-R1 — MARKET-DATA SYNCHRONIZATION GAP ANALYSIS

## What exists (`engines/mt5_triangular_data_feed.py`)

- `SYMBOL_MAP` = explicit `GBPAUD→GBPAUD.PRO`, `GBPNZD→GBPNZD.PRO`, `AUDNZD→AUDNZD.PRO`
  (**hardcoded**, not runtime-verified).
- `TriangularDataFeed.fetch_latest_snapshot()` fetches M5 bars (`copy_rates_from_pos`, 500)
  per symbol and builds a `TriangularSnapshot` where all three legs share the same closed M5
  timestamp (rejects the forming bar, walks back up to 5 bars for a common timestamp).

## Gap vs the R2 contract

| R2 requirement | Prior stack | Verdict |
|---|---|---|
| tick-level TriangleSnapshot (bid/ask/mid/age_ms/spread) | bar-level snapshot (OHLC close only) | ❌ missing |
| max_quote_age_ms rejection (stale quote) | none — no age check | ❌ missing |
| max_cross_leg_skew_ms rejection | loose (up to 5 M5 bars ≈ 25 min tolerated) | ⚠️ weak |
| bid/ask inversion, bid<=0, ask<bid checks | none (bars, not ticks) | ❌ missing |
| all_symbols_tradeable / symbol metadata unavailable | none | ❌ missing |
| runtime symbol resolution (no silent substitution) | hardcoded map | ❌ hardcoded |
| closed-bar discipline | yes (skips forming bar) | ✅ present |

## Consequence for TB

The basis is computed from **closed M5 bars** (correct for the rolling-200 z), but the feed
cannot detect a stale leg (a symbol that stopped producing bars would be silently paired at an
old timestamp), has no bid/ask or spread view (needed for executable-entry prices and the
10.2-pip cost model), and assumes the `.PRO` suffix. **A stale leg against two fresh legs is
exactly the failure the R0 contract forbids.**

## Classification

**market_data_layer = ADOPT_WITH_MECHANICAL_REPAIR** for the bar-sync path, but the R2
tick-level fail-closed `TriangleSnapshot` is **greenfield** (`greenfield_r2_needed = true`).
