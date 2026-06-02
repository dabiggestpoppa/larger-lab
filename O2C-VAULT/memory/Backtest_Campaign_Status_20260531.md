# Backtest Campaign Status 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Backtest Campaign Status — 2026-05-31 20:51 EDT

## Problem Diagnosed

The backtest campaign (`run_full_backtest_campaign.py`) returns 0 trades for ALL assets because:

1. **ST Engine**: `SymmetryTrapEngine.__init__()` doesn't accept `kwarg 'pip_value'` — campaign is passing wrong constructor args
2. **P90 Engine**: 
   - Campaign calls `run_p90_backtest()` from `p90_backtest` module — BUT the module function is actually `run_backtest()`
   - Also passes `pip_value` kwarg to `P90Engine.__init__()` which doesn't accept it

### Fix Required:
- Campaign script needs to be corrected to use actual engine APIs
- ST: Instantiate `SymmetryTrapEngine` with correct args, call `process_bar()` per bar
- P90: Import `run_backtest` from `p90_backtest` (not `run_p90_backtest`)
- Both engines have their own constructors — campaign wrapper must match

## Available Data (24 CSV files)
EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, XAUUSD, XAGUSD, BTCUSD, ETHUSD, US500, HK50, GBPJPY, GBPCHF, GBPAUD, GBPNZD, CHFJPY, FR40, DE30

## Previous Results (ST multi-asset, different runner):
- 19 assets, 14,563 trades, 82.8% avg WR
- Top: ETHUSD 96.9% | HK50 94.0% | NZDUSD 93.3% | BTCUSD 92.6%
- Output: `quant-lab/reports/st_multi_asset_results.json`

## Nautilus Backtest Reports (quant-lab/reports/):
Multiple small JSON files (258-441 bytes) suggesting failed/incomplete Nautilus runs
- NAUTILUS_SYMMETRY_TRAP_EURUSD.PRO_*.json (6 files)
- NAUTILUS_P90_EURUSD.PRO_*.json (2 files)
- NAUTILUS_P90_USDCHF.PRO_*.json (10 files)

## NT8 Track A Files (need import + compilation):
All in `tradovate/`:
1. CEREBUS_ST_NT8.cs (22.5KB)
2. CEREBUS_P90_NT8.cs (26KB)
3. CEREBUS_BacktestHarness.cs (12.7KB)
4. CEREBUS_DeployConfig.json (3.2KB)
5. CEREBUS_TradeCopier.cs (7.2KB)
6. CEREBUS_AssetPresets.cs (10.3KB)
7. CryptoAssetScanner.py (separate, in crypto/)

_Last updated: 2026-05-31 20:51 EDT_

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[Operator Rules]]
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
[[Cal]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run Top5 Backtest Mc]]
[[Symmetry Trap Backtest]]
[[Memory]]
