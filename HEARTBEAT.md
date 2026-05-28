# HEARTBEAT.md - OWL Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/.
> Max 4000 chars.

## Current Status (2026-05-28 11:00 EDT)
- **Quant Lab Reboot:** DMR backtest LIVE — 89.5% WR, +9,313p (869 trades, EUR/USD)
- **MT5:** Connected to OxSecurities-Demo (login 1114712, balance $289.17)
- **Auto-start:** `quant-lab/mt5/auto_start_mt5.py` — launches MT5 without user
- **OANDA:** NOT available as Nautilus adapter (no pip extra). Using sandbox venue instead.
- **IACER:** Manual-only (cron removed per MAD 5/28 directive)

## Active Work
### O-7 Persistent Field Mode — Ready to Build
- O-6 complete (52/52 tests, 16 routes)
- O-7 spec ready at `plans/observer-core/O-7-PERSISTENT-FIELD-DOC.md`
- 12 backend + 9 frontend + 8 tests to build

### Quant Lab (shared-conversations/lab-room.md)
- DMR Python backtest running (89.5% WR, need to tune to 94.8%)
- MT5 CLI auto-start working
- Pipeline: Nautilus backtest → MT5 EA generator → Demo/live

## Do NOT
- Poll subagents in a loop
- Send heartbeat messages to Telegram
- Run continuous background processes from heartbeat
- Accumulate history in this file - archive to logs/heartbeat-history/
- Run on autopilot. IACER checks are manual, not cron-driven.

---
*Updated: 2026-05-28 10:28 EDT*
