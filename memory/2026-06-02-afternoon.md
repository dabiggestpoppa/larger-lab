# 2026-06-02 Afternoon Notes (15:00-20:00 EDT)

## VS Team Build — CEREBUS ML Engine

### Completed
- Full 5-phase ML pipeline built under `quant-lab/ml/`
- 80/80 tests passing
- 18 assets trained (all with Parquet data)
- Tier configs fixed (Asian session grouping bug — was 2x too high)
- XGBoost regime classifier: avg 81% train / 80.7% test accuracy
- Entry scorer trained
- Optuna optimizer coded
- Phase 4 integration (friction filters, close-only guard, parity validator)
- Phase 5 hardening (drift detector, shadow mode, Grafana)
- Commit: `d0944e104` — "CEREBUS ML Engine complete — 80/80 tests passing"

### Architecture
- Layer 1: XGBoost regime classifier (4 classes: CONFIRMED/CAUTION/FAILED/NO-GO)
- Layer 2: Entry quality scorer (0-1 continuous)
- Layer 3: Optuna Bayesian parameter optimizer
- Close-only SL invalidation (manual Close[0] check, NOT SetStopLoss)
- Gear Shift modifies TARGET only
- Shadow mode 7 days before promotion

### Tier Values (Post-Fix)
| Asset | T1 AU | T2 AU | T3 AU |
|-------|-------|-------|-------|
| EURUSD | 9.0p | 21.9p | ~53p |
| GBPUSD | 12.7p | 34.6p | ~90p |
| GBPJPY | ~38p | ~87p | ~200p |
| CHFJPY | ~34p | ~71p | ~159p |

## Live Trading
- ST first post-fix trade at 18:03 — CHFJPY BUY @ 203.200, SL 202.98 (22p), TP 203.33 (13.2p), RR 0.60
- Balance ended $71.89 (from $74.95 morning)
- Today: 39 closed trades, W8 L31, WR 20.5%, Net -$3.06
- All losing trades from pre-fix signals (GBPAUD/GBPJPY)
- 4/4 processes alive: guardian, bridge, P90, ST

## Infrastructure
- OCE backend running (:8000), frontend (:3000)
- OpenClaw gateway (:18790)
- Telegram gateway (both PO and OC2)
- PM2 monitor daemon auto-committing workspace changes
- Workspace monitor cron set (every 5 min)

## Key Bug Fixes Deployed Today
1. ST SL at impulse extreme → OCC extreme (was placing SL in profit territory)
2. P90 SL at 80% body → candle extreme + spread buffer (was 3-5p, too tight)
3. Bridge clamping (50pt buffer) → only clamp when SL/TP on wrong side
4. Asian session grouping → bars 00:00-03:00 belong to previous day's session
5. Executor validation tolerance → 1-point tolerance added
6. Duplicate executor kill → only bridge + guardian should run
