# PO Field Investigation — OC2 Bridge Zero Signals
**Date:** 2026-06-06 | **Investigator:** PO (Primary Observer)

---

## 🔴 Problem
OC2 Demo Bridge connected since ~10:13 EST, scanning 4 symbols (BTCUSD.DEMO, ETHUSD.DEMO, EURNZD.DEMO, GBPNZD.DEMO) every 60 seconds. **Zero signals, zero trades, zero PnL.** Equity flat at $80.07, 0 open positions.

## 🔍 Root Cause: `initialize_session()` Never Called

Traced the full signal chain in `quant-lab/mt5/demo_bridge.py` (418 lines) and `quant-lab/engines/symmetry_trap.py` (725 lines):

```
DemoBridge.run()
  └─ while self.running:
       ├─ self.check_daily_reset()
       ├─ self.check_positions()
       ├─ bars_data = self.scan_bars()       ← pulls M5 bars ✅
       ├─ self.process_signals(bars_data)     ← calls engine.process_bar() ✅
       └─ ...
```

**The gap:** `DemoBridge.initialize()` (line ~140) creates `SymmetryTrapEngine` instances for all 8 symbols. But it **never calls `engine.initialize_session(asian_high, asian_low)`**.

### What `initialize_session()` does (symmetry_trap.py line ~299):
- Sets `self.session_active = True` (gate check via `classify_tier_by_ar()`)
- Sets `self.asian_high` / `self.asian_low` / `self.asian_range_pips`
- Resets state machine to `EngineState.SEARCH`
- Resets all trade variables (swing_origin, impulse_direction, kill_switch, etc.)
- Logs: `"Session initialized: tier=?, AU=Xp, AR=Yp, loop=1"`

### What happens WITHOUT it:
- `session_active = False` (default from `__init__`)
- `tier_name = "PENDING"` forever
- `au_pips = 0.0`, `trigger_pips = 0.0`
- Engine receives bars but **silently discards them** — `process_bar()` exits early when session isn't active
- Result: **zero signals forever**

### Evidence in demo_bridge.log:
```
00:19:06 - Demo Bridge initialized with 4 symbols
00:19:11 - Scan | Open positions: 0 | Daily: W0 L0 PnL: $0.00
00:20:11 - Scan | Open positions: 0 | Daily: W0 L0 PnL: $0.00
...repeats every 60s, no session init log, no impulse, no tier classification
```

## 🛠️ Fix

**One-line change in `demo_bridge.py`** — add `initialize_session()` call after engine creation, before the scan loop:

```python
# In DemoBridge.run(), after self.initialize() and before the while scan loop:
for symbol, engine in self.engines.items():
    engine.initialize_session(asian_high=asian_high, asian_low=asian_low)
```

This activates the session, classifies the tier, sets AU/AR thresholds, and resets the FSM to `EngineState.SEARCH`. After this, bars will be processed through the full state machine and signals will generate.

## 📋 Impact

| Before Fix | After Fix |
|------------|-----------|
| `session_active = False` | `session_active = True` |
| `tier_name = "PENDING"` | `tier_name = "LOW"/"MED"/"HIGH"` |
| Bars silently discarded | Bars processed through FSM |
| Zero signals | Signals generated per symmetry logic |
| Zero trades | Trades execute via OrderManager |
| PnL = $0.00 forever | PnL flows from real trade outcomes |

## 📌 Additional Notes

- The bridge connects to MT5 and pulls M5 bars correctly — the data pipeline is fine
- `scan_bars()` returns data, `process_signals()` is called — the issue is purely the missing session init
- SL_HIT events are profit-lock exits, NOT losses — confirmed in signals.jsonl analysis
- PnL tracking fields `exit_pnl_pips` and `exit_pnl_usd` added to signals.jsonl logging
- Equivalent live bridge (`cerebus_live_bridge.py`) likely has the same bug — needs verification

---
*Investigation complete. Fix is a one-line code change in demo_bridge.py run() method.*