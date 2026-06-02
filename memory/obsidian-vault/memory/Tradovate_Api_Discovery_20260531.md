# Tradovate Api Discovery 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# 22:33 EDT — TRADOVATE API DISCOVERY

## MAD's Message
Sent Tradovate API docs link: https://api.tradovate.com/#section/Getting-Started-With-the-Tradovate-API

## Research: Tradovate API Capabilities
- REST API: auth, accounts, order placement (market/limit), positions, contracts
- WebSocket: market data streaming, fill events, order strategy commands
- **Orders-only mode:** "allow sending orders with no Market data subscriptions" — use our own MT5 CSV data
- Multi-bracket strategies via WebSocket: entry + TP + SL in one call
- API access: free with Tradovate account (enable API key in settings)
- CME data subscription NOT needed if using external data feed

## New Proposed Architecture
```
CEREBUS Python Engines (ST + P90)
    ↓ signals
tradovate_api.py + tradovate_ws.py + tradovate_executor.py
    ↓ HTTPS / WSS
TRADOVATE API
    ↓
Prop firm execution
```

NT8 .cs files become FALLBACK, not primary path.

## MAD's Feedback on Previous Work
- Reiterated: don't research IBKR, don't use CLI-Anything, stop drifting
- Tradovate API is THE answer for bypassing GUI

## Pending
- MAD to provide: Tradovate email + API key
- MAD to confirm: Tradovate API replaces NT8 as primary execution path?
- Build: tradovate_api.py, tradovate_ws.py, tradovate_executor.py (2-3 files)

---
*Logged: 2026-05-31 22:33 EDT*

LINKS:
[[Architecture]]
[[System Architecture]]
[[V3 Cognitive Field]]
[[Api Reference]]
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
[[Vault Distillation 20260531 0245]]
[[Welcome]]
[[Api Endpoints]]
[[Api Evaluation]]
[[Cal]]
[[Core Api]]
[[External Data]]
[[Github Api Cheatsheet]]
[[Hub Discovery]]
[[Python Api]]
[[Rest Api]]
[[Memory]]
