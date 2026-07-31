# Option A Confirmed 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# 22:40 EDT — MAD: Option A Confirmed (Tradovate REST API for Track A)

## MAD's Directive (#5884)
"Please do option a for track a use the rest api again look at the file if u have question if you still need clarity after ask me but please refer to the file gang"

**Option A = Tradovate REST API** (bypass NT8 GUI entirely)

## Architecture Confirmed
- Python CEREBUS engines (ST + P90) → truth source, unchanged
- New layer: Tradovate REST API client (orders) + WebSocket client (market data)
- Risk gate embedded at API layer: daily loss 0.40%, correlation cap, position sizing, 12PM hard exit
- Per-asset configs from asset_configs.py, no hardcoded forex values

## Items to Build (once credentials received)
1. `tradovate/rest_client.py` — REST client (auth, accounts, contracts, orders)
2. `tradovate/ws_client.py` — WebSocket client (market data, fills, order strategies)
3. `tradovate/executor.py` — bridges CEREBUS signals → Tradovate orders with risk gate

## Blocking Item
Need from MAD:
1. Tradovate email/login
2. API key (from account settings → API access)
3. Account ID (for order routing)

## Build Estimate
Once credentials received: 2-3 hours to build + test with paper trading

---
*Logged: 2026-05-31 22:40 EDT — Awaiting Tradovate API credentials from MAD*

LINKS:
[[Architecture]]
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
[[Bridge]]
[[Rest Api]]
[[Asset Configs]]
[[Memory]]
[[Diag Option B]]
[[Symmetry Trap Option B]]
