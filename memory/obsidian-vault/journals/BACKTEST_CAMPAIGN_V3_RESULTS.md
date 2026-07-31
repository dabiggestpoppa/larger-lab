# CEREBUS FX v4.0 — Backtest Campaign v3 Results

> **Date:** 2026-05-31 21:15 EDT | **Status:** ✅ COMPLETE
> **Framework:** ST via `symmetry_trap_backtest.py`, P90 via `p90_backtest.py`
> **Fix:** Lowercase column names in CSV loader, per-asset tier config injection

## Overall Summary

| Engine | Assets Tested | Assets w/ Trades | Total Trades | Avg WR | Total PnL |
|--------|--------------|------------------|-------------|--------|-----------|
| ST (Symmetry Trap) | 19 | 19 | 14,563 | 86.6% | +294,067 pips |
| P90 (Kinetic) | 18 | 18 | 23,448 | 83.0% | — |

## Per-Asset Results

| Symbol | ST Trades | ST WR | ST PnL (pips) | P90 Trades | P90 WR | P90 PF |
|--------|-----------|-------|----------------|------------|---------|--------|
| EURUSD | 1,163 | 85.0% | +5,048 | 1,471 | 79.9% | 3.26 |
| GBPUSD | 1,259 | 85.7% | +7,444 | 2,237 | 85.9% | 4.67 |
| USDCHF | 1,153 | 84.9% | +5,036 | 1,192 | 80.3% | 3.02 |
| USDJPY | 729 | 87.8% | +7,087 | 1,062 | 85.1% | 5.06 |
| AUDUSD | 828 | 89.3% | +3,990 | 618 | 72.3% | 2.62 |
| NZDUSD | 727 | 93.3% | +4,214 | 534 | 70.0% | 2.29 |
| GBPJPY | 830 | 86.3% | +8,656 | 1,717 | 91.5% | 8.23 |
| GBPCHF | 803 | 91.2% | +6,409 | 1,746 | 85.1% | 4.01 |
| GBPAUD | 715 | 88.4% | +7,912 | 1,299 | 87.5% | 5.89 |
| GBPNZD | 664 | 88.4% | +8,598 | 1,275 | 88.5% | 6.04 |
| CHFJPY | 751 | 86.3% | +7,167 | 1,662 | 90.5% | 7.57 |
| US500 | 372 | 91.7% | +3,415 | 548 | 79.6% | 3.35 |
| HK50 | 385 | 94.0% | +21,839 | 4 | 75.0% | 3.88 |
| XAUUSD | 604 | 84.4% | +7,188 | 673 | 92.1% | 9.19 |
| XAGUSD | 2 | 50.0% | +2 | 973 | 74.9% | 2.78 |
| BTCUSD | 801 | 92.6% | +152,304 | 0 | — | — |
| ETHUSD | 547 | 96.9% | +9,562 | 223 | 71.7% | 3.09 |
| FR40 | 1,085 | 87.0% | +9,730 | 3,141 | 90.0% | 5.13 |
| DE30 | 1,145 | 82.8% | +18,467 | 3,073 | 94.5% | 11.17 |

## P90 Per-Variant Breakdown

| Variant | Description | Typical WR |
|---------|-------------|-----------|
| INITIAL | Base P90 entry | 55-68% |
| CASCADE | Cascade续集 entry | 77-94% |
| EWS | Early Warning Signal (100% WR, 0 losses across ALL assets) | 100% |

## Key Findings

1. **EWS variant is PERFECT** — 100% WR across all assets (every single EWS trade is a win)
2. **CASCADE is dominant** — 80-94% WR, highest trade count, best overall edge
3. **DE30 is the P90 king** — 94.5% WR, 3,073 trades, PF 11.17
4. **BTCUSD P90 gap** — crypto is 24/7, needs different session handling
5. **XAGUSD ST issue** — only 2 trades, needs tier config adjustment
6. **Both engines agree** — ST and P90 both >80% WR on most assets

## Root Cause of Previous Failures

v1/v2 campaigns failed because:
1. **Wrong tier config** — used `DEFAULT_TIER_CONFIG` (ar_max=20/30/45) instead of per-asset tiers from `asset_configs.py`
2. **Wrong column names** — P90 loader expected `OPEN/HIGH/LOW/CLOSE` (uppercase), CSVs have lowercase
3. **Wrong session grouping** — didn't account for EST offset (UTC-5) for session boundaries
4. **Wrong engine API** — tried to call `run_backtest()` / `run_p90_backtest()` which don't exist as module functions

v3 uses the PROPER existing frameworks (`symmetry_trap_backtest.py`, `p90_backtest.py`) which handle all of this correctly.

## Files

- JSON result: `quant-lab/reports/full_backtest_campaign_v3.json`
- Campaign script: `quant-lab/reports/run_campaign_v3.py`
- ST framework: `quant-lab/engines/symmetry_trap_backtest.py`
- P90 framework: `quant-lab/engines/p90_backtest.py`
- Asset configs: `quant-lab/configs/asset_configs.py`

## Next Steps

- Track B crypto rebuild (4 files)
- NT8 import + backtest
- Deployment package
- DMR convergence mode backtest (dual-engine overlay)

---
*Logged: 2026-05-31 21:25 EDT*
