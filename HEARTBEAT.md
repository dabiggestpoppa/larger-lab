# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
Max 4000 chars.

## Current Status (2026-05-30 00:23 EDT)
- **Workspace:** owl-environment (isolated, OFF LIMITS: larger-lab belongs to CC)
- **MAD last interaction:** msg #5030 (P90 CASCADE on USDCHF.PRO verified)

## This Session — COMPLETE
### DMR — SCRAPPED (MAD directive)
- CSV sim produced 19% WR vs MT5 EA's 92% — root cause never found
- DMR cron jobs disabled. DMR executors killed.

### Symmetry Trap — DEPLOYMENT READY
- Engine: `quant-lab/engines/symmetry_trap.py` — Engine B, 4-state FSM
- Executor: `quant-lab/mt5/symmetry_trap_executor.py`
- Symbol: EURUSD.PRO | Magic: 20260531 | Lot: 0.03
- 4Y BT: 892 trades, 85.7% WR, PF 8.18, MaxDD 39.3p
- MC: 0% ruin, Kelly 74.9%, IACER 96/100
- Cron: 2AM EST daily start

### P90 CASCADE — DEPLOYMENT READY
- Engine: `quant-lab/engines/p90_engine.py` — Engine A, CASCADE ONLY
- Executor: `quant-lab/mt5/p90_cascade_executor.py`
- Symbol: **USDCHF.PRO** (MAD correction: was GBPUSD, changed to USDCHF "sniper")
- Magic: 20260532 | Lot: 0.01
- 3Y BT (MAD's data, Jan 2023–May 2026): 1,035 trades, 79.0% WR, PF 2.81, MaxDD 42.9p
- CASCADE variant: 484 trades, 83.1% WR, +1,292.3p
- DMR Convergence overlay: 85.8% WR on convergence trades
- INITIAL variant FILTERED in executor
- Engine persists across scans for CASCADE detection
- Cron: 2AM EST daily start (5min after ST)
- Data: `quant-lab/data/USDCHFPRO_M5_MAD.csv` (MAD's file, 253K bars)

### Active Cron Jobs
| Job | Time (EST) | ID |
|-----|------------|-----|
| ST Executor Start | 2:00 AM | 367d723e |
| P90 CASCADE Executor | 2:05 AM | 2669a448 |
| Mid-Day Monitor | 8/10/12PM | ebc75d0c |
| End-of-Day Report | 5:00 PM | cb63255b |

### Disabled Cron Jobs (DMR)
- DMR Forward Test Monitor (disabled)
- DMR Mid-Day Check (disabled)
- DMR Daily Report (disabled)

### Convergence Indicator
- `quant-lab/engines/convergence_indicator.py` — EXISTS, SYNTAX OK
- Standalone overlay (not baked into engines)

## Do NOT
- Touch larger-lab workspace (CC's domain)
- Re-enable DMR without MAD explicit directive
- Modify engine filters without backing up original
- Deploy INITIAL variant (63.6% WR, filtered out)
- Deploy on GBPUSD (MAD said "sloppy" — use USDCHF only)

*Updated: 2026-05-30 00:23 EDT — MAD corrected P90 symbol to USDCHF. Backtest verified on his full dataset. Build phase complete. Awaiting go-live confirmation.*
