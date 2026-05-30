# CEREBUS FX v4.0 — DEPLOYMENT CHECKPOINT
## MAD Directive 2026-05-29 | Build Phase Complete → Live Deployment

---

## DEPLOYMENT STATUS

### ✅ Symmetry Trap (Engine B) — DEPLOY
| Item | Status |
|------|--------|
| Engine syntax | ✅ `symmetry_trap.py` |
| Engine isolation | ✅ Engine B only, no P90 cross-contamination |
| Backtest | ✅ 892 trades, 85.7% WR, PF 8.18, MaxDD 39.3p |
| Monte Carlo | ✅ 0% ruin, Kelly 74.9%, median +3,731p |
| IACER | ✅ 96/100 (A+) |
| Executor syntax | ✅ `symmetry_trap_executor.py` |
| Lot size | ✅ 0.03 |
| Symbol | ✅ EURUSD.PRO |
| Magic | ✅ 20260531 |
| SL | ✅ Zero-Buffer Impulse Extreme |
| TP | ✅ 1 AU single target |
| Entry window | ✅ 2AM-11AM EST |
| Hard exit | ✅ 5PM EST |
| Daily cap | ❌ NONE (engine loops freely, up to 5/session) |
| Cron start | ✅ 2AM EST daily |
| Monitor | ✅ cerebus_monitor.py |

### ✅ P0 CASCADE (Engine A) — DEPLOY
| Item | Status |
|------|--------|
| Engine syntax | ✅ `p90_engine.py` (CASCADE variant) |
| Engine isolation | ✅ Engine A only, no ST cross-contamination |
| Backtest | ✅ 439 trades, 85.4% WR, PF ~4+ (CASCADE-only) |
| Monte Carlo | ✅ Positive expected value at 0.01 lots |
| Executor syntax | ✅ `p90_cascade_executor.py` |
| Lot size | ✅ 0.01 |
| Symbol | ✅ GBPUSD.PRO (separate from ST) |
| Magic | ✅ 20260532 |
| SL | ✅ 168% body (CASCADE rule) |
| TP | ✅ -25/-50% AR |
| Entry window | ✅ 2AM-11AM EST |
| Hard exit | ✅ 5PM EST |
| Engine persistence | ✅ Maintained across scans for CASCADE detection |
| INITIAL filter | ✅ Skipped — CASCADE only |
| Cron start | ✅ 2AM EST daily (5min after ST) |
| Monitor | ✅ cerebus_monitor.py |

### 🚫 DMR — SCRAPPED (MAD Directive)
| Item | Status |
|------|--------|
| Decision | 🚫 DO NOT DEPLOY |
| Reason | CSV simulation doesn't match MT5 EA (19% vs 92% WR) |
| DMR cron jobs | ✅ DISABLED |
| Old DMR monitor | ✅ DISABLED |

---

## ACTIVE CRON JOBS

| Job | Time (EST) | Purpose |
|-----|------------|---------|
| ST Executor Start | 2:00 AM | Start symmetry_trap_executor.py |
| P90 CASCADE Executor Start | 2:05 AM | Start p90_cascade_executor.py |
| Mid-Day Monitor | 8AM, 10AM, 12PM | Run cerebus_monitor.py + report |
| End-of-Day Report | 5:00 PM | Daily summary of all trades + PnL |

### DISABLED (DMR — no longer needed)
- DMR Forward Test Monitor (was 2AM)
- DMR Mid-Day Trade Check (was 8/10/12/2/4PM)
- DMR Daily Report (was 10PM)

---

## RUNNING EXECUTORS

| Executor | Symbol | Magic | Lot |_SCAN_INTERVAL |
|----------|--------|-------|-----|---------------|
| symmetry_trap_executor.py | EURUSD.PRO | 20260531 | 0.03 | 30s |
| p90_cascade_executor.py | GBPUSD.PRO | 20260532 | 0.01 | 30s |

---

## MONITORING

- Script: `cerebus_monitor.py`
- Checks: process alive, positions, SL/TP quality, PnL, log errors, new trades
- State file: `live_logs/cerebus_monitor_state.json`
- Log files:
  - `live_logs/symmetry_trap_executor.log`
  - `live_logs/p90_cascade_executor.log`
  - `live_logs/symmetry_trap_signals.jsonl`
  - `live_logs/p90_cascade_signals.jsonl`

---

## 4Y BACKTEST RESULTS SUMMARY

### Symmetry Trap (2023-07 to 2026-05)
| Metric | Value |
|--------|-------|
| Trades | 892 |
| Win Rate | 85.7% |
| PF | 8.18 |
| Max DD | 39.3p |
| MC Median | +3,731p |
| MC Ruin | 0.0% |
| Kelly | 74.9% |
| IACER | 96/100 |

### P90 CASCADE (2023-07 to 2026-05)
| Metric | Value |
|--------|-------|
| Trades | 439 |
| Win Rate | 85.4% |
| PF | ~4+ |
| AvgR | 0.53R |
| Best Hour | 03:00 EST (96.4% WR) |

---

## FILES

### Engines
- `quant-lab/engines/symmetry_trap.py` — Engine B, 4-state FSM
- `quant-lab/engines/p90_engine.py` — Engine A, 3 variants

### Executors
- `quant-lab/mt5/symmetry_trap_executor.py` — Live ST execution
- `quant-lab/mt5/p90_cascade_executor.py` — Live P90 CASCADE execution

### Monitoring
- `quant-lab/mt5/cerebus_monitor.py` — Unified monitor

### Reports
- `quant-lab/reports/SYMMETRY_TRAP_FINAL_COMPOSITE_REPORT.md`
- `quant-lab/reports/P90_FINAL_COMPOSITE_REPORT.md`
- `quant-lab/reports/DMR_FINAL_COMPOSITE_REPORT.md` (scrapped)
- `quant-lab/reports/CEREBUS_DEPLOYMENT_CHECKPOINT.md` (this file)

---

## PRE-TRADE CHECKLIST (for tomorrow)

- [ ] MT5 terminal open and logged in
- [ ] AutoTrading enabled in MT5
- [ ] Both EURUSD.PRO and GBPUSD.PRO visible in Market Watch
- [ ] Account balance confirmed
- [ ] Cron jobs active (2AM trigger)
- [ ] Monitor script tested
- [ ] Log directory exists and writable
- [ ] No stale python processes running

---

*Checkpoint created: 2026-05-29 23:30 EDT*
*MAD Directive: Build phase complete. Deploy ST + P90 CASCADE. DMR scrapped.*
