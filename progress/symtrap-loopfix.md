# Symmetry Trap Loop Fix — Progress Report

**Date:** 2026-05-29 20:58 EDT
**Task:** Fix Symmetry Trap Engine Multi-Trade Loop Patches
**Status:** ✅ COMPLETE

## Changes Made

### `quant-lab/engines/symmetry_trap.py`

**4 KILL_SWITCH handlers patched** (2 in WAIT_RETRACE, 2 in WAIT_OCC):

- **Before:** All 4 handlers called `self._reset_state(bar.close)` which fully reset state INCLUDING loop tracking, then never incremented loop_count.
- **After:** All 4 handlers now call `self._reset_state_keep_loop(bar.close)`, save old loop_count, increment it, set loop_start_time, and gracefully end session if max_loops reached.

**Specific change pattern (applied 4x):**
```python
# OLD:
self._reset_state(bar.close)
sig = TradeSignal(..., loop_count=self.loop_count, ...)

# NEW:
_loop = self.loop_count
self._reset_state_keep_loop(bar.close)
self.loop_count = min(_loop + 1, self.max_loops)
self.loop_start_time = bar.timestamp
if self.loop_count >= self.max_loops:
    self.session_active = False
sig = TradeSignal(..., loop_count=_loop, ...)
```

**Lines modified:**
- ~346: WAIT_RETRACE LONG kill → `_reset_state_keep_loop`
- ~364: WAIT_RETRACE SHORT kill → `_reset_state_keep_loop`
- ~430: WAIT_OCC LONG kill → `_reset_state_keep_loop`
- ~448: WAIT_OCC SHORT kill → `_reset_state_keep_loop`

### `quant-lab/engines/symmetry_trap_backtest.py`

**NO changes needed.** Verified that the bar feeding loop (`for bar in day_bars`) continues feeding ALL bars regardless of trade state. After TP_HIT/SL_HIT, the engine resets to SEARCH via `_reset_state_keep_loop`, and the next bar still goes through `process_bar()` correctly. The only break condition is `bar_est_h >= 12 and engine.state == EngineState.SEARCH` which fires at noon — correct behavior.

## Verification Results

### 1. Syntax Check ✅
```
python -c "import ast; ast.parse(open('symmetry_trap.py').read()); print('PASSED')"
→ ast.parse PASSED
```

### 2. Import Check ✅
```
python -c "from symmetry_trap import SymmetryTrapEngine; e = SymmetryTrapEngine(); print(f'max_loops={e.max_loops}, loop_count={e.loop_count}')"
→ max_loops=5, loop_count=1
```

### 3. Loop Distribution ✅
Backtest run on EURUSDPRO_M5_2023_2025.csv (224K bars, 939 days):

| Loop | Trades | WR | PnL |
|------|--------|----|-----|
| 1 | 374 | 90.6% | +1797.8p |
| 2 | 234 | 82.9% | +941.0p |
| 3 | 161 | 84.5% | +519.4p |
| 4 | 96 | 78.1% | +340.7p |
| 5 | 96 | 83.3% | +429.6p |

- **Total trades: 961** (up from ~374 if only loop 1 fired)
- Distribution is NOT all loop=1 ✅
- All 5 loops are active ✅

### 4. Overall Stats
- Win Rate: 85.7%
- Profit Factor: 8.39
- Sharpe: 12.18
- Max DD: 38.6p (0.04%)

## Root Cause Summary

Before the fix, kill switch events called `_reset_state()` which wiped loop_count back to 1 and cleared loop tracking. This meant:
1. The engine could never advance past loop 1 after a kill switch
2. The same volatile conditions would trigger kill switch repeatedly within the same loop (infinite kill-switch-reset cycle)
3. `max_loops` cap was never engaged because `loop_count` was never incremented on kill

The fix ensures kill switch events increment the loop counter (using relaxed thresholds on subsequent loops) and naturally terminate the session when max_loops is reached.
