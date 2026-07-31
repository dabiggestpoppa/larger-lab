# 2026 05 30 Nautilus Fix

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Nautilus Backtest Fix — 2026-05-30 22:55 EDT

## Root Cause
- `lot_size` passed as `Decimal("0.01")` (lot-based) instead of `Decimal("1000")` (unit-based) in Nautilus v1.226
- Symptom: Orders submitted (900-1800) but 0 positions filled (micro-unit sizing = effectively zero)
- Discovery: Sub-agents independently confirmed that `lot_size=1000` produced 173 positions, 82.4% WR on ST/EURUSD

## Fix Applied
- `run_cerebus_backtest.py`: Default `lot_size` changed from `Decimal("0.01")` to `Decimal("1000")`
- Added strategy-level stat extraction (`strategy.total_trades/wins/losses/pnl`) as ground truth
- Works for all pairs including USDCHF (which has Nautilus CHF/USD conversion issue for engine-level PnL)

## Smoke Test Result
- ST/EURUSD 5K bars: 48 trades, 77.1% WR, +175.3 pips (confirmed fix works)

## Full Backtest Status
- 4 sub-agents spawned at 22:55 EDT with fixed runner (30-min timeout each)
  1. naut_st_eurusd_v2 — Symmetry Trap / EURUSD
  2. naut_st_usdchf_v2 — Symmetry Trap / USDCHF
  3. naut_p90_eurusd_v2 — P90 / EURUSD
  4. naut_p90_usdchf_v2 — P90 / USDCHF

## Benchmarks (from CSV engines)
- P90 EURUSD: 1,038 trades, 78.7% WR, PF 3.09, +4,814p
- Symmetry Trap EURUSD: 574-892 trades, 85-91% WR, PF 8-23
- USDCHF both strategies: should be in similar_WR range (cross-validation)

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[Agents]]
[[Master Plan 2026 05 18]]
[[Operator Rules]]
[[2026 05 17]]
[[2026 05 18]]
[[2026 05 20]]
[[2026 05 21]]
[[2026 05 30]]
[[2026 05 30 Evening]]
[[2026 05 31]]
[[2026 06 01]]
[[Active Strategies Performance]]
[[Agent Topology]]
[[Api Execution Architecture 20260531]]
[[Api Reference Summary]]
[[Api Test Note]]
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
[[Build Patterns]]
[[Build Progress 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Daily Runtime 20260531]]
[[Dashboard Build Complete]]
[[Doctor Prescription]]
[[Errors And Solutions]]
[[Executor Crash 20260531]]
[[Failure Index Oc2]]
[[Foundational Principles]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Keyerror Data Validation 20260531 0245]]
[[Live Deployment Status]]
[[Master Plan Assessment 20260531]]
[[Module Guide Summary]]
[[O2C Pipeline]]
[[Observer Core O1 O7]]
[[Obsidian Vault Connection Info]]
[[Oc2 Gateway Failures]]
[[Oc2 Identity]]
[[Oc2 Vault Access Guide]]
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Option A Confirmed 20260531]]
[[Pm2 Test Note]]
[[Progress]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Quantlab Bible]]
[[Sage Audit 20260531 Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit Environment Utilization]]
[[Self Heal Report]]
[[Session 20260531 2200]]
[[Session Testagent 20260531 0245]]
[[Session Testagent 20260531 0245 Full]]
[[Srra Oph]]
[[Task Flow]]
[[Team Phase01 Status]]
[[Team Roster]]
[[Test Note]]
[[Test Pattern]]
[[Track A Build Complete 20260531]]
[[Track A Build Status]]
[[Track A Ninjascript Build 20260531]]
[[Tradovate Api Discovery 20260531]]
[[Vault Distillation 20260531 0245]]
[[Welcome]]
[[Action]]
[[Symmetry Trap]]
[[Memory]]
[[Team Chat Archive 2026 05]]
[[Team Chat Archive 2026 05 22]]
