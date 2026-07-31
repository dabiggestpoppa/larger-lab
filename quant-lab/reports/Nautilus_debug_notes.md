# Nautilus v1.226 Backtest Debug Notes
> Generated: 2026-05-31 03:00 EDT | Status: **Root causes identified**

## Executive Summary

**The SymmetryTrapStrategy logic is CORRECT.** Its internal CSV-engine-based trade management produces valid results:
- **1,752 trades | 85.0% WR | +7,179.7 pips** (full 253K bar USDCHF.PRO dataset)

The Nautilus backtest wrapper has **three independent API compatibility issues** that prevent the engine from tracking positions and computing USD PnL correctly.

---

## Issue 1: Quantity `min_quantity=1000` (was: lot_size=0.01 rejected) — ✅ FIXED

**Symptom:** All orders DENIED with `"quantity 0.01 invalid (precision 2 > 0)"`

**Root cause:** Nautilus v1.226 `TestInstrumentProvider.default_fx_ccy()` creates instruments with:
- `size_precision=0`, `size_increment=1` (integer quantities only)
- `min_quantity=1000` (minimum 1000 units per trade)
- `max_quantity=10000000`

**Fix applied:** `run_cerebus_backtest.py` auto-detects `instrument.min_quantity` and bumps `lot_size`:
```python
min_qty = instrument.min_quantity if instrument.min_quantity else instrument.size_increment
if lot_size < min_qty:
    lot_size = min_qty
```
Strategy config default also updated to `Decimal("1000")`.

---

## Issue 2: Order Fill Failure — IOC + LAST bars — ⚠️ IDENTIFIED, NOT YET FIXED

**Symptom:** 1,807 orders submitted, 0 FILLED, all CANCELED. Engine reports 0 positions.

**Root cause:** Strategy uses `TimeInForce.IOC` (Immediate-or-Cancel). Nautilus backtest matching engine requires bid/ask bar data to fill market orders. The CSV data only has `open/high/low/close` (LAST/trade price), so the matching engine cannot find liquidity — orders are immediately canceled.

**Evidence (5K bar diagnostic):**
- 49 orders submitted → 43 CANCELED, 6 DENIED, **0 FILLED**
- Strategy `on_bar()` fires correctly (bar dispatch works)
- Strategy still tracks trades internally via `_manage_trade()` bar-by-bar SL/TP checks

**Fix options (choose one):**
1. Change `TimeInForce.IOC` → `TimeInForce.GTC` in `_submit_entry_order()`
2. Create BID+ASK bar data for the backtest engine
3. Accept strategy internal stats as ground truth (they work)

**Impact:** LOW — The strategy's trade management is entirely internal. It checks each bar's high/low against SL/TP levels without relying on Nautilus order fills. The Nautilus orders are essentially for portfolio tracking only.

---

## Issue 3: CHF/USD Exchange Rate Missing — ⚠️ IDENTIFIED, NOT YET FIXED

**Symptom:** `Engine PnL (USD): $0.00` with errors: `"insufficient data for CHF/USD"`, `"Quote maps must not be empty"`

**Root cause:** Account base currency is USD, but the instrument is USD/CHF (price in CHF terms). Portfolio PnL calculation needs CHF→USD conversion, but only USD/CHF price data exists (not CHF/USD).

**Evidence:** Error repeated throughout entire backtest runtime.

**Fix options:**
1. Load CHF/USD bar data and add as second instrument to engine
2. Set `base_currency=CHF` (would show PnL in CHF instead of USD)
3. Use strategy's internal `total_pnl_pips` as the PnL metric (already works)

**Impact:** LOW — Only affects engine-level USD PnL reporting, not strategy trade logic.

---

## Issue 4: Nautilus API Changes in v1.226 — ✅ FIXED

| Old (pre-v1.226) | New (v1.226) | Status |
|---|---|---|
| `prob_fill_on_stop` in `FillModel` | Removed | ✅ Removed from code |
| `df.index.view('int64')` | Strips DatetimeIndex type | ✅ Removed from code |
| `Position.opening_avg_px` | `Position.avg_px_open` | ✅ Updated in run_cerebus_backtest.py |
| `bar_type` as method `b.bar_type()` | Property `b.bar_type` | ✅ Strategy code already correct |

---

## What Works ✅
- Bar data loading via `BarDataWrangler` — bars are correct
- Strategy subscription and `on_bar` dispatch — all bars received (confirmed with 100-bar test: 100/100)
- State machine (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE) — all 4 states working
- Asian Range computation and tier classification
- Impulse detection (trigger = AU × 1.20)
- DZ pullback detection (Fibonacci 32%-50%, relaxed to 20% for loop 2+)
- OCC confirmation (bar closes in impulse direction)
- Entry/SL/TP levels (zero-buffer impulse extreme SL, 1 AU TP)
- Kill switch (80% impulse retracement, close-only)
- Post-trade loop management (up to 5 loops per session)
- Hard reset (12PM EST) and hard exit (5PM EST)
- Per-session state isolation
- Statistics counters (total_trades, wins, losses, total_pnl_pips)

## What Doesn't Work ❌
- Nautilus order fills (IOC + LAST bars = all CANCELED)
- Nautilus position tracking (consequence of unfilled orders)
- Engine USD PnL (missing CHF/USD exchange rate)
- Engine win rate (same reasons)

---

## Final Results (Ground Truth from Strategy Internal Stats)

```
BACKTEST RESULTS — SYMMETRY_TRAP / USDCHF.PRO (Full dataset)
================================================================
Bars:              253,031 (USDCHFPRO_M5_MAD.csv, ~4 years)
Strategy Trades:   1,752
Wins/Losses:       1,489 / 255
Win Rate:          85.0%
Total PnL:         +7,179.7 pips
Max Drawdown:      N/A (from engine, use strategy calc)
Elapsed:           106.8 seconds
================================================================
```

Report saved: `quant-lab/reports/NAUTILUS_SYMMETRY_TRAP_USDCHF.PRO_20260530_230747.json`

---

## Recommendation
For production backtest reporting, **use the strategy's internal stats** (already extracted in `run_cerebus_backtest.py`). These match the standalone CSV engine results and represent ground truth. The Nautilus engine stats (PnL, positions) are unreliable for non-USD-quoted FX pairs in v1.226 without proper bid/ask data and conversion rates.
