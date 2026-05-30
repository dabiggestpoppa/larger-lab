# DMR LIVE MONITOR — Status Report

> **Generated:** 2026-05-28 23:49 EDT
> **Monitor:** OWL Subagent (dmr-monitor)
> **Mode:** READ-ONLY — no trades placed

---

## ✅ Executor Status: RUNNING

| Field | Value |
|-------|-------|
| **PID** | 19436 |
| **Command** | `python dmr_executor.py --loop --interval 30` |
| **Started** | 2026-05-28 23:47:29 EDT |
| **Uptime** | ~2 minutes (as of this check) |

---

## 📋 Last Log Entries (`live_logs/executor.log`)

```
[2026-05-28 23:47:31] DMR LIVE EXECUTOR v3 — 84% WR Strategy with REAL SL/TP
[2026-05-28 23:47:31] Symbol: EURUSD.PRO | Lots: 0.01 | Magic: 20260528
[2026-05-28 23:47:31] DeepMult: 2.0 | KillMult: 2.2
[2026-05-28 23:47:31] Account: 1114712 | Balance: $289.17 | Server: OxSecurities-Demo
[2026-05-28 23:47:31] Spread: 0.1 pips
[2026-05-28 23:47:31] Scanning every 30s | Entry window: 2AM-11AM EST | Hard exit: 5PM
[2026-05-28 23:47:31] SL/TP set on BROKER — not just simulated
```

**No trade entries logged yet** — executor just restarted at 23:47.

---

## 📊 Account / Config

| Field | Value |
|-------|-------|
| **Account** | 1114712 |
| **Balance** | $289.17 |
| **Server** | OxSecurities-Demo |
| **Symbol** | EURUSD.PRO |
| **Lot Size** | 0.01 |
| **Spread** | 0.1 pips |

---

## 🕐 Entry Window

| Window | Time (EST) |
|--------|------------|
| **Active Entry** | 2:00 AM – 11:00 AM |
| **Hard Exit** | 5:00 PM |
| **Current Time** | 23:49 EDT (May 28) |

**Status:** ⏸️ Outside entry window. Executor is scanning but will NOT enter trades until 2:00 AM EST (May 29).

**Next entry window opens:** 2026-05-29 02:00 EDT (~2 hours 11 minutes from now)
**Next entry window closes:** 2026-05-29 11:00 EDT

---

## 🔍 Strategy Reconstruction Tracker (DMR)

From `quant-lab/strategy_reconstruction_tracker.md`:

| Field | Value |
|-------|-------|
| **Strategy** | DMR (Deep Mean Reversion) |
| **Manual WR** | 74–84% |
| **M5 WR** | **84.2%** — MATCHES manual ✅ |
| **Verdict** | **LIVE — only strategy matching manual claims** |
| **Edge** | Mean reversion from Deep State gives better R:R on any fill model |

DMR is the **primary production strategy** — all other 15 strategies are either queued, have gaps, or are debug-needed.

---

## 🐍 Other Python Processes

| PID | Script | Notes |
|-----|--------|-------|
| 19436 | `dmr_executor.py --loop --interval 30` | ✅ DMR Live Executor |
| 16300 | `symmetry_trap_v6_exact.py` | Symmetry Trap backtest running |
| 11772 | `oce.backend.main` | OCE backend (FastAPI) |

---

## ⚠️ Errors Detected

**None.** Executor started cleanly. No error entries in log. All systems nominal.

---

## Summary

- ✅ DMR executor is running (PID 19436), restarted at 23:47 EDT
- 🟢 Zero errors in live log
- ⏸️ Currently outside entry window (opens 2:00 AM EST)
- 📈 Balance: $289.17 on OxSecurities-Demo
- 🎯 DMR is the only strategy matching manual WR — approved for live trading
- 🔄 Executor will begin scanning for entries at 2:00 AM EDT

---

*Next check recommended: 2026-05-29 02:00 EDT (when entry window opens)*
*Report written by OWL dmr-monitor subagent — READ-ONLY, no modifications made*
