# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
> Max 4000 chars.

## Current Status (2026-05-29 12:20 EDT)
- **Workspace:** owl-environment (isolated, OFF LIMITS: larger-lab belongs to CC)
- **DMR Live Executor:** DUAL DEPLOY — EURUSD (PID 18036) + USDCHF (PID 7728) | Account: 650898 LIVE | Balance: $85.26

## Active Work
### DMR DUAL LIVE — EUR/USD + USD/CHF (MAD directive 12:02)
- **EURUSD.PRO:** Magic 20260528 | 0.01 lots | per-hour P90 | entry=deep_state
- **USDCHF.PRO:** Magic 20260529 | 0.01 lots | per-hour P90 | entry=deep_state
- **Account:** 650898 LIVE | Balance: $85.26 | AutoTrading: ON
- **Lot cap:** 0.02 (both at 0.01)
- **Entry window:** 2AM-11AM EST | Hard exit: 5PM
- **Monitor:** `python quant-lab/mt5/dmr_monitor.py`
- **Logs:** executor.log + executor_usdchf.log
- **MAD goal:** grow this account together — first real deployed task

### USD/CHF DMR — Backtest Complete (entry fix applied)
- **Status:** Backtest complete (fixed entry bug — entry at deep_state not bar close)
- 804 trades | **91.9% WR** | **+8,915p** | PF 131.9 | Sharpe 22.1 | Max DD 0.01%
- Avg Win: +12.2p | Avg Loss: -1.0p | R:R = 12.2:1 | Kelly 0.912
- Per-hour P90 calibrated: 3.7-6.3p range (overall 4.8p)
- Reports: quant-lab/reports/dmr_usdchf.json, dmr_usdchf_trades.json
- **AWAITING MAD green light for live deployment**

## Do NOT
- Touch larger-lab workspace (CC's domain)
- Poll subagents in a loop
- Send heartbeat messages to Telegram
- Run continuous background processes from heartbeat
- Accumulate history in this file - archive to logs/heartbeat-history/
- Run on autopilot

---
*Updated: 2026-05-29 11:45 EDT*
*USD/CHF DMR fixed and validated. Entry at deep_state (limit order) not bar close. Massive improvement: 91.9% WR, +8915p, PF 131.9, DD 0.01%.*
