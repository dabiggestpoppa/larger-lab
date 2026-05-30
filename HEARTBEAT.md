# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
Max 4000 chars.

## Current Status (2026-05-30 12:45 EDT)
- **Workspace:** owl-environment (isolated, OFF LIMITS: larger-lab belongs to CC)
- **MAD last interaction:** msg #5230 — Prop Firm Sniper Engine build + $100K deployment test delivered
- **Self-Heal fleet deployed** — 4 jobs replacing 1 monolithic cron
- **Prop Firm Sniper Engine — COMPLETE (12:23 EDT)**

## DEPLOYED — CEREBUS FX v4.0

### Symmetry Trap (Engine B) — LIVE
- Executor: `quant-lab/mt5/symmetry_trap_executor.py`
- Symbol: EURUSD.PRO | Magic: 20260531 | Lot: 0.03
- 4Y BT: 892 trades, 85.7% WR, PF 8.18, IACER 96/100
- Cron start: 2:00 AM EST daily

### P90 CASCADE (Engine A) — LIVE
- Executor: `quant-lab/mt5/p90_cascade_executor.py`
- Symbol: USDCHF.PRO | Magic: 20260532 | Lot: 0.01
- 3.5Y BT: 1,035 total trades, CASCADE 83.1% WR
- INITIAL variant FILTERED in executor
- Cron start: 9:00 AM EST daily

## DEPLOYED — Prop Firm Sniper Engine v1.0

### 7 Modules (ALL compile OK, end-to-end verified)
| Module | File | Purpose |
|--------|------|---------|
| PES Calculator | `quant-lab/sniper/pes_calculator.py` | Ω, α, Vc, EL, crossover, survival |
| Database | `quant-lab/sniper/database.py` | SQLite — 3 tables: prop_firms, deployments, pes_snapshots |
| F&F Protocol | `quant-lab/sniper/ff_protocol.py` | Promo verification, patch signals, cost basis |
| Config Generator | `quant-lab/sniper/config_generator.py` | YAML/JSON config output |
| Scope | `quant-lab/sniper/scope.py` | SCAN→VERIFY→CALCULATE→RANK→OUTPUT |
| Firm Scanner | `quant-lab/sniper/firm_scanner.py` | PropFirmMatch scrape + change detection |
| Init | `quant-lab/sniper/__init__.py` | Package init, public API |

### $100K Deployment Test Results
- **BEST: My Funded Futures $100K** — PES 0.0430, Omega 139,755, EL 19.5x, Cost $225, 7-day payout cycle
- Runner-up: Topstep $100K [F&F] — PES 0.0318, Cost $220, 10-day cycle
- Crossover threshold: ~$4,629 (far below $100K — prop advantage confirmed)

### Active Cron Jobs
| Job | Time (EST) | ID | Status |
|-----|------------|-----|--------|
| ST Executor Start | 2:00 AM | 367d723e | ✅ Running |
| P90 CASCADE Executor | 9:00 AM | 2669a448 | ✅ Running |
| Overnight Report | 5:00 AM | 89279994 | ✅ Delivered |
| Mid-Day Monitor | 8/10/12PM | ebc75d0c | ⚠️ 1 error (timeout, not yetAlerting) |
| End-of-Day Report | 5:00 PM | cb63255b | Not yet |
| STRUCT (Hygiene) | 6:00 AM daily | 921d31d0 | ✅ Fleet |
| PULSE (Fleet Health) | 6:15 AM daily | 10a579a2 | ✅ Fleet |
| ECHO (Trail Maintenance) | 6:30 AM daily | 2b40b8da | ✅ Fleet |
| DRIFT (Architecture) | 6:45 AM Sun/Wed/Sat | 2cb0fe0e | ✅ Fleet |

### Disabled Cron Jobs
- Self-Heal Daily Review (old monolithic) — disabled, replaced by fleet
- DMR Forward Test Monitor / Mid-Day Check / Daily Report — disabled
- Workspace Monitor — disabled (16-strike timeout history)

## Notes
- Weekend: both executors expected down (markets closed)
- Mid-Day Monitor errored once (consecutiveErrors=1, threshold=2) — watching

*Updated: 2026-05-30 12:45 EDT — Sniper engine complete, HEARTBEAT synced to latest state*
