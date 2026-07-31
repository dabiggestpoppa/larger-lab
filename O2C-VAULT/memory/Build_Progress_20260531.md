# Build Progress 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Build Progress — 2026-05-31 21:25 EDT

## Backtest Campaign v3 — COMPLETE ✅
- 19 assets tested with both ST + P90 engines
- ST: 14,563 trades, 86.6% avg WR, +294,067 pips
- P90: 23,448 trades, 83.0% avg WR
- EWS variant: 100% WR across ALL assets

## XAGUSD Tier Fix ✅
- Problem: All sessions classified NO_GO (tier thresholds too small)
- Pip size 0.01, AR range 8.2-182.4 pips → tiers needed recalibration
- Fixed: T1(au_max=50), T2(au_max=100), T3(au_max=200)
- Result: 651 trades, 92.0% WR, +8,303 pips, PF 21.4

## NautilusTrader Backtest — IN PROGRESS
- Subagent running crypto backtest (BTCUSD + ETHUSD)
- Infrastructure exists: p90_strategy.py, symmetry_trap_strategy.py, run_cerebus_backtest.py

## NT8 Track A Status
- 7/7 .cs files written
- BacktestHarness.cs has validation checklist — steps 4-8 require GUI import
- Cannot automate NT8 GUI interaction

## Files Modified Today
- quant-lab/engines/p90_backtest.py — added lowercase column support
- quant-lab/configs/asset_configs.py — fixed XAGUSD tiers
- quant-lab/reports/run_campaign_v3.py — correct campaign runner
- quant-lab/reports/run_full_backtest_campaign_v2.py — fixed API calls
- HEARTBEAT.md — updated status

## Root Cause of All Campaign Failures
1. DEFAULT_TIER_CONFIG too small for most assets → NO_GO on every session
2. P90 CSV loader expected uppercase OPEN/HIGH/LOW/CLOSE → got lowercase
3. Session grouping didn't account for EST offset
4. v1/v2 used wrong engine method names

---
*Logged: 2026-05-31 21:30 EDT*

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[Heartbeat]]
[[Operator Rules]]
[[Project Progress Clean]]
[[2026 05 17]]
[[2026 05 18]]
[[2026 05 20]]
[[2026 05 21]]
[[2026 05 30]]
[[2026 05 30 Evening]]
[[2026 05 30 Nautilus Fix]]
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
[[Cal]]
[[Failures]]
[[Interaction]]
[[P90 Engine]]
[[Memory]]
[[Loader]]
