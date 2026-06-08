# CEREBUS BRIDGE BUG JOURNAL — 2026-06-08

## Issue: Bridge Scanning But Not Executing Orders

### Symptoms
- Bridge running, scanning every minute (scan #300+)
- Signals generating (Sig: 6 per scan)
- **Exec: 0** — no orders placed
- Equity flat at $66.66, no positions

### Root Cause
**MT5 AutoTrading was disabled in the terminal.** The bridge's `check_autotrading()` function checks `mt5.terminal_info().trade_allowed` before every order. When False, it logs "MT5 AutoTrading DISABLED" and returns False — order never sent.

### Timeline
| Time (EST) | Event |
|------------|-------|
| 09:03 | ST ENTRY GBPNZD → AutoTrading DISABLED |
| 10:57 | ST ENTRY GBPNZD → AutoTrading DISABLED |
| 11:39 | ST ENTRY GBPCAD → AutoTrading DISABLED |
| 11:53-12:37 | Bridge restarted, still Exec: 0 |
| ~12:45 | Operator enabled AutoTrading in MT5 terminal |
| 12:57 | Bridge restarted, AutoTrading confirmed ON via API |

### Fix
1. Operator enabled AutoTrading in MT5 terminal (GUI button)
2. Bridge restarted to pick up new state
3. API confirmed: `trade_allowed: True`, `trade_expert: True`

### Key Lesson
**The MT5 Python API can READ `trade_allowed` but cannot WRITE/toggle it.** AutoTrading is a GUI-only setting. The bridge correctly checks it before every order, but if it's off, orders are silently dropped with just a warning log.

### Prevention
- Bridge startup should log AutoTrading status prominently
- Consider adding a startup check that warns if AutoTrading is disabled
- The `check_autotrading()` function is in `cerebus_live_bridge.py` line 205

### Related Files
- `quant-lab/mt5/cerebus_live_bridge.py` — `check_autotrading()` line 205, `send_order()` line 218
- `quant-lab/mt5/live_logs/bridge.log` — shows "MT5 AutoTrading DISABLED" warnings

---

## Issue: Signal Bot Showing Wrong SL Type

### Symptoms
- Signal bot showed SL as regular stop loss instead of profit-lock
- First signals showed correct ST profit-lock SL
- Later signals showed OCC extreme SL (wrong)

### Root Cause
The signal bot (`scripts/signal_bot.py`) was formatting signals from `signals.jsonl` without distinguishing between the ST engine's profit-lock SL and a regular SL. The `format_signal()` function needed to check the engine type and label accordingly.

### Fix
Updated `format_signal()` to:
- Check `engine == "SymmetryTrap"` and `event == "SL_HIT"` → label as `[PROFIT-LOCK]`
- Show PnL on exit events when available
- Display `sl_type` field from signal data

### Related Files
- `scripts/signal_bot.py` — `format_signal()` function

---

## Issue: Duplicate Bridge Instances

### Symptoms
- Two bridge processes running simultaneously (PIDs 25584 and 19956)
- Both scanning same symbols
- Potential for duplicate signals

### Root Cause
The guardian (`cerebus_guardian.py`) restarted the bridge but the old process wasn't killed first. The guardian only monitors one PID file.

### Fix
- Killed both processes manually
- Restarted bridge cleanly
- Verified only one instance running

### Prevention
- Guardian should check for existing processes before restarting
- Use PID file locking (already implemented in `telegram_gateway.py`)

---

## Status: RESOLVED
- AutoTrading enabled ✅
- Bridge scanning ✅
- Signals generating ✅
- Orders: waiting for next signal to confirm execution
