# Api Execution Architecture 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# API Execution Architecture — 2026-05-31 21:45 EDT

## MAD Directive
"Pull data via API like MT5, circumvent NT8 GUI entirely — ensure same execution on live"

## Research Findings

### NT8 REST API (Official)
- URL: developer.ninjatrader.com/products/api
- REST API with Swagger spec → Python client generation
- Headless: submit/modify/cancel orders, stream quotes, account data
- Requires API credentials from NT8
- Does NOT require NT8 Desktop GUI

### IBKR Native Python API (ibapi) — RECOMMENDED
- Direct Python → Interactive Brokers (TWS/Gateway)
- Single socket connection for: data + execution + account
- Free with IBKR account
- Supports: historical data pull, live orders, portfolio monitoring
- No middleman platform needed

### Proposed Architecture
```
CEREBUS Python Engines (ST + P90)
        ↓ signals
IBKR TWS API (Python ibapi)
   ├── Historical data pull (OHLCV for any asset)
   ├── Live order submission
   └── Account/position monitoring
```

### NautilusTrader Crypto Results
- EURUSD forex: 112 tr, 77.7% WR — runner validated ✅
- BTCUSD: 3 tr, scale bug ($3600 move ÷ 0.01 pip = meaningless)
- ETHUSD: 0 trades — crypto needs separate calibration
- Fix: define crypto-specific pip sizes ($1/pip BTC, $0.10/pip ETH)

## Pending Questions for MAD
1. What broker for live trading? (IBKR? NT8? Both?)
2. If IBKR → build entire pipeline Python → ibapi
3. If NT8 → use NT8 REST API with similar architecture

## NT8 .cs Files Status
- 7/7 written (ST, P90, BacktestHarness, DeployConfig, TradeCopier, AssetPresets, CryptoAssetScanner)
- Can be imported via NT8 REST API instead of GUI

---
*Logged: 2026-05-31 21:45 EDT*

LINKS:
[[Architecture]]
[[System Architecture]]
[[V3 Architecture]]
[[V3 Cognitive Field]]
[[Api Reference]]
[[Cg 4 Execution Intelligence]]
[[Operator Rules]]
[[Topological Cognition Architecture]]
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
[[Api Endpoints]]
[[Api Evaluation]]
[[Cal]]
[[Core Api]]
[[Github Api Cheatsheet]]
[[Python Api]]
[[Rest Api]]
[[Memory]]
[[Execution Boundary]]
