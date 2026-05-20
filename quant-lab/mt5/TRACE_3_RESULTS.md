# THE 3 DIFFERENT DMR RESULTS — ROOT CAUSE ANALYSIS

## Result 1: Nautilus/Optimizer v2 (GOOD — 91.8-94.8% WR)
**Source:** `optimizer_v2.py` → `dmr_mt5_WORKING.py`
**WR:** 91.8% (optimizer) / 92.7-94.8% (MT5 WORKING)
**Logic:**
1. Asian Range: 7PM-3AM EST (19:00-03:00)
2. P90 candle: body ≥ threshold in 2-11 AM EST
3. Deep State: P90 close + 200% of P90 body (in P90 direction)
4. Wait for price to touch Deep State
5. Enter mean reversion AGAINST P90 direction
6. SL at 220% (kill switch), TP at P90 close (activation = 0%)
7. Hard exit 5PM EST

## Result 2: MT5 Strategy Tester via Python data load (GOOD — 92.7% WR)
**Source:** `dmr_mt5_working_trades_20260519_144233.csv` → `eurusd_analysis.py`
**WR:** 92.7% (915 trades)
**Logic:** Same as Result 1 — this is the trade-level export from the WORKING backtest
**Data:** MT5 EUR/USD M5, 2022-01-04 → 2026-04-30

## Result 3: Sub-agent dmr_full_analysis_v2.py (BAD — 4.6% WR)
**Source:** `dmr_full_analysis_v2.py` → `DMR_FULL_ANALYSIS.json`
**WR:** 4.6% (941 trades)
**Logic — CRITICAL DIFFERENCES:**
1. Asian Range: 2-8 AM EST (DIFFERENT — uses post-Asian bars, not pre-Asian)
2. NO P90 candle detection — uses price move from Asian range boundaries
3. Entry: When price moves beyond P90 threshold from Asian range high/low
4. SL: 220% of AR (not P90 body) — much wider
5. TP: Asian range boundary (not P90 close)
6. NO Deep State concept — enters immediately on P90 touch
7. NO mean reversion against P90 — enters IN the direction of the move

## ROOT CAUSE

**Result 3 is a COMPLETELY DIFFERENT STRATEGY.** It's not DMR at all.

The key differences:
- **DMR (Results 1&2):** Finds P90 candle → calculates Deep State extension → waits for touch → trades AGAINST P90 direction back to P90 close
- **Result 3 (broken):** Finds Asian range → when price moves beyond P90 threshold → trades IN THAT DIRECTION back to Asian range boundary

Result 3 is essentially "buy the breakout, sell at the mean" — which is the OPPOSITE of mean reversion. It's trend following with a wide SL, which produces many small wins and occasional large losses.

## WHY THE SUB-AGENT FAILED

The sub-agent wrote `dmr_full_analysis_v2.py` from scratch instead of using the WORKING code. It:
1. Used wrong Asian range definition (2-8 AM instead of 7PM-3AM)
2. Replaced P90 body-based Deep State with simple AR-based P90 threshold
3. Entered in the wrong direction (with the move instead of against it)
4. Used AR-based SL instead of P90 body-based SL

## WHAT'S VALID

**Results 1 and 2 are the SAME strategy producing the SAME results.** The 915-trade CSV is the trade-level detail from the WORKING backtest. Both show 92-95% WR.

**Result 3 is INVALID and should be discarded.**

## ACTION ITEMS

1. Delete or archive `DMR_FULL_ANALYSIS.json` (the bad one)
2. Use `EURUSD_DEEP_ANALYSIS.json` + `dmr_multi_asset_v2.json` as the canonical data
3. The report `DMR_FULL_REPORT.md` needs to be rewritten with correct data
4. For multi-asset trade-level analysis, use `dmr_multi_asset_v2.py` logic (the WORKING version) not `dmr_full_analysis_v2.py`
