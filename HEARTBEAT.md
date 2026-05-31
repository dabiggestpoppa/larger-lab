# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
Max 4000 chars.

## Current Status (2026-05-30 22:58 EDT)
- **MAD last interaction:** msg #5524 — directive: fix DMR deprecation in memory, update workspace org, run Nautilus cross-validation backtests
- **Nautilus backtest fix applied** — lot_size Decimal("0.01") → Decimal("1000") in run_cerebus_backtest.py
- **4 sub-agents running** full Nautilus backtests (fixed runner, 30min timeout each)

## Active Delegations
| Task | Agent | Status | Started |
|------|-------|--------|---------|
| ST/EURUSD Nautilus backtest | naut_st_eurusd_v2 | RUNNING | ~22:55 |
| ST/USDCHF Nautilus backtest | naut_st_usdchf_v2 | RUNNING | ~22:55 |
| P90/EURUSD Nautilus backtest | naut_p90_eurusd_v2 | RUNNING | ~22:55 |
| P90/USDCHF Nautilus backtest | naut_p90_usdchf_v2 | RUNNING | ~22:55 |

## Nautilus Cross-Validation — IN PROGRESS
- **Root cause fixed**: lot_size was Decimal("0.01") = 1 micro-unit in Nautilus v1.226 → orders filled at zero size
- **Fix**: Default lot_size now Decimal("1000") = 0.01 standard lots
- **Strategy-level stats**: Extracted directly from strategy object (works for all pairs)
- **Smoke test confirmed**: ST/EURUSD 5K bars: 48 trades, 77.1% WR, +175.3p ✅
- **Benchmarks to beat**: ST ~85-91% WR, P90 ~78.7% WR

## Memory & Workspace Updates (this session)
- MEMORY.md: Added Critical Memory Org Rules (DMR deprecated, Hermes role, 2-engine only)
- TOOLS.md: Added quant-lab structure (engines=strategies=backtests=reports)
- memory/2026-05-30-nautilus-fix.md: Full fix documentation

## DEPLOYED — CEREBUS FX v4.0
- **Symmetry Trap (B):** EURUSD.PRO | Magic 20260531 | Lot 0.03 | 2:00 AM EST
- **P90 CASCADE (A):** USDCHF.PRO | Magic 20260532 | Lot 0.01 | 9:00 AM EST

## DEPLOYED — Prop Firm Sniper Engine v1.0
- **13 Python modules** in `quant-lab/sniper/`
- Dashboard: `sniper-dashboard/` (Next.js 14, build OK)
- Phase 6 desktop app handoff ready (awaiting MAD signal)

## Active Cron Jobs
| Job | Time (EST) | Status |
|-----|------------|--------|
| ST Executor | 2:00 AM | OK |
| P90 CASCADE | 9:00 AM | OK |
| Overnight Report | 5:00 AM | OK |
| Mid-Day Monitor | 8/10/12PM | 1 error (watching) |
| STRUCT/PULSE/ECHO | 6-6:30 AM | Fleet OK |
| DRIFT | Sun/Wed/Sat 6:45AM | OK |

## Notes
- Do NOT waste time on DMR standalone (deprecated, integrated into P90)
- Hermes does NOT touch quant-lab engines (Nautilus backtesting only)
- Nautilus backtester must match CSV engine results (~5% tolerance)
- Awaiting sub-agent cross-validation results before next steps
