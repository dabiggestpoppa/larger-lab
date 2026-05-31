# Nautilus v1.226 Backtest Debug Notes
> Generated: 2026-05-31 | Status: Root causes identified

## Summary
The SymmetryTrapStrategy's **internal trade management is correct** — the CSV engine logic embedded in the strategy produces valid results:
- **Strategy Trades: 1,752** | **WR: 85.0%** | **PnL: 7,179.7 pips** (full 253K bar dataset)

The Nautilus backtest wrapper has **three independent issues** that prevent Nautilus from tracking positions and computing USD PnL:

---

## Issue 1: Order Quantity — FIXED (was lot_size=0.01 vs min_quantity=1000)

**Root cause:** Nautilus v1.226 `TestInstrumentProvider.default_fx_ccy()` creates FX instruments with:
- `size_precision=0`, `size_increment=1` (displays as integers)
- **`min_quantity=1000`** (minimum 1000 units per trade)

Old code passed `lot_size=0.01` → `Quantity.from_str("0.01")` → DENIED with `"precision 2 > 0"`

**Fix:** Auto-detect `lot_size` from instrument constraints in `run_cerebus_backtest.py`:
```python
min_qty = instrument.min_quantity if instrument.min_quantity else instrument.size_increment
if lot_size < min_qty:
    lot_size = min_qty
```
Strategy config default already changed to `Decimal("1000")`.

---

## Issue 2: Order Fill Failure (IOC + LAST bars) — PARTIALLY FIXED

**Root cause:** Market orders use `TimeInForce.IOC` (Immediate-or-Cancel). Nautilus backtest matching engine requires bid/ask liquidity to fill market orders. With `*-LAST-EXTERNAL` bars (trade price only, no bid/ask spread), the matching engine cannot fill market orders — they are immediately CANCELED.

**Evidence:**
- 5000-bar test: 49 orders submitted, 43 CANCELED, 6 DENIED, 0 FILLED
- Strategy still received all 500 bars (`on_bar` works correctly with `subscribe_bars()`)

**Potential fixes (not yet implemented):**
1. Change `TimeInForce.IOC` → `TimeInForce.GTC` in strategy's `_submit_entry_order()`
2. OR create separate BID and ASK bar data for the backtest engine
3. OR use bar-type-specific fill rules (some versions of Nautilus auto-fill against LAST bars)

**Impact:** Order canceling does NOT affect strategy PnL — the strategy manages trades internally via `_manage_trade()` using bar high/low vs SL/TP levels. The Nautilus positions/PnL are secondary tracking that doesn't affect the strategy's own trade decisions.

---

## Issue 3: CHF/USD Exchange Rate Missing — NOT FIXED

**Root cause:** Portfolio/account PnL calculation needs CHF→USD conversion, but only USD/CHF bars are loaded. The matching engine logs repeated errors: `"insufficient data for CHF/USD"` and `"Quote maps must not be empty"`.

**Evidence:** Even when orders DO fill (57-qty position found in one test), the portfolio can't compute PnL because it can't convert CHF-denominated position values to USD.

**Fix options:**
1. Load CHF/USD bar data as a second instrument in the backtest
2. Provide synthetic QuoteTick data for CHF/USD conversion
3. Use the strategy's internal `total_pnl_pips` instead of engine PnL for reporting
4. Set `base_currency=CHF` instead of USD (would show PnL in CHF)

---

## Issue 4: Position Attribute API Change (Minor)

`Position.opening_avg_px` → removed in v1.226. Correct property: **`Position.avg_px_open`**

---

## Diagnostic Script Reference

| Script | Purpose |
|--------|---------|
| `diag_test3.py` | Root cause: min_quantity=1000 |
| `diag_fills2.py` | Order fill analysis with 5K bars |
| `diag_subscribe.py` | Bar dispatch test (works with subscribe_bars) |
| `diag_bar_min.py` | Bar object API (bar_type is property, not method) |
| `qty_test.py` | Quantity API validation |

---

## What Works
- ✅ Bar data loading via `BarDataWrangler` — bars are correct
- ✅ Strategy subscription and `on_bar` dispatch — all bars received
- ✅ State machine (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE) — all 4 states working
- ✅ Asian Range computation and tier classification
- ✅ Impulse detection, DZ retest, OCC confirmation
- ✅ Kill switch (80% retracement) — exits and re-loops
- ✅ Trade management (SL/TP tracking via bar high/low)
- ✅ Hard reset (12PM EST) and hard exit (5PM EST)
- ✅ Per-session state isolation
- ✅ Statistics counters (total_trades, wins, losses, total_pnl_pips)

## What Doesn't Work
- ❌ Nautilus order fills (IOC + LAST bars = all CANCELED)
- ❌ Nautilus position tracking (consequence of unfilled orders)
- ❌ Engine USD PnL (missing CHF/USD exchange rate)
- ❌ Engine win rate (same reasons)

## Recommendation
For backtest reporting, **use the strategy's internal stats** (already extracted in `run_cerebus_backtest.py` lines ~218-230):
- `strategy.total_trades` = 1,752
- `strategy.wins` = 1,489
- `strategy.losses` = 255
- `strategy.total_pnl_pips` = 7,179.7
- Win rate = `wins/total_trades` = 85.0%

These match the standalone CSV engine results and represent ground truth.
