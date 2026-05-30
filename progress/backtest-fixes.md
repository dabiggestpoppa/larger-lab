# Backtest Fixes — 2026-05-29

## Summary of all fixes applied to CEREBUS FX backtest system.

---

## FIX 1: Symmetry Trap CSV Loader — 0 bars loaded

**File:** `quant-lab/engines/symmetry_trap_backtest.py`
**Function:** `load_m5_csv()`

**Root cause:** The function detected headers (e.g. "open", "close") in the first row but still used positional parsing assuming MT5 format (Date col 0, Time col 1, OHLC col 2-5). For the `EURUSDPRO_M5_2023_2026.csv` file, column 0 is a unix integer timestamp like `1688342400`, which failed `datetime.strptime()` with every format in `ts_formats`. All rows silently skipped → 0 bars.

**Fix:** Rewrote `load_m5_csv()` with a header-first strategy:
1. Parse header row, build column-index map by lower-cased name.
2. If recognised headers found (`timestamp`, `date`, `time`, `open`, `high`, `low`, `close`, `datetime`):
   - If `timestamp` column exists → parse with `%Y-%m-%d %H:%M:%S`.
   - If separate `date` + `time` columns → concatenate and try MT5 datetime formats.
   - OHLC columns identified by name, not position.
3. If no recognised headers → fall back to original positional MT5 parser.

**Result:** 216,820 bars loaded (was 0).

---

## FIX 2 & 3: P90 Variant Breakdown — All variants showing "No trades"

**Files:** `quant-lab/engines/p90_engine.py` (root cause), `quant-lab/engines/p90_backtest.py` (no change needed)

### Bug A — `_reset_state()` called before signal creation (ROOT CAUSE)

**Root cause:** In all 7 exit signal paths (EWS_EXIT, LONG TP2, LONG TP1, LONG SL, SHORT TP2, SHORT TP1, SHORT SL), `_reset_state()` was called **before** constructing the `P90Signal`. Since `_reset_state()` sets `self.entry_price = None`, `self.sl_price = None`, `self.tp1_price = None`, etc., every completed signal had `entry_price=None`. The `_pnl_pips()` function returns `None` when `entry_price is None`, so 845 out of 1,041 completed signals produced no PnL value. Only the 196 EWS_EXIT signals had non-null entry_price (because they read `self.entry_price` *before* reset in the EWS path), creating the illusion that only 196 trades existed.

**Fix:** At each of the 7 exit points, save `entry_price`, `sl_price`, `tp1_price`, `tp2_price`, `active_variant`, and `direction` to local variables **before** calling `_reset_state()`, then use those locals when constructing `P90Signal`.

**Result after fix:**
- Total completed trades: 1,041 (was 196)
- Per-variant breakdown now populated:
  - INITIAL: 380 trades
  - CASCADE: 319 trades
  - STALL_HARVEST: 146 trades

### Bug B — `compute_stats()` variant key format (VERIFIED OK)

The `per_variant` dict uses `variant.value` as key (e.g. `"INITIAL"`, `"CASCADE"`, `"STALL_HARVEST"`). The comparison `s.variant == variant` works correctly with `P90Variant` enum values. No change needed in `compute_stats()`.

---

## Verification

```
> cd quant-lab/engines
> python -c "from symmetry_trap_backtest import load_m5_csv; bars, sym = load_m5_csv(r'...\EURUSDPRO_M5_2023_2026.csv'); print(f'Loaded {len(bars)} bars')"
Loaded 216820 bars

> python _test_fix.py (full backtest integration test)
Loaded 216820 bars
Sessions: 911
Total signals: 2097, entries: 1056
Stats total_trades: 1041
Per variant:
  INITIAL: trades=380 wins=227 pnl=523.1
  CASCADE: trades=319 wins=266 pnl=1121.5
  STALL_HARVEST: trades=146 wins=3 pnl=-4461.6
```

All syntax verified with `ast.parse()` on all modified files.
