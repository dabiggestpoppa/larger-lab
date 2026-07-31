# Master Plan Assessment 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# 22:35 EDT — MAD's Master Plan Document + Assessment

## Document: lab_expansion_two_parts_in_order.txt
MAD sent comprehensive 2-part master plan covering Track A (Tradovate/NT8) and Track B (Crypto) with detailed phases, mermaid diagrams, and code snippets.

## Key Findings from Master Plan

### Track A — NT8 Corrections Needed
1. **Tier thresholds**: Current .cs uses EURUSD-specific <20/30/45p. Plan requires per-asset thresholds via UserDefinedInput
2. **Gear shift logic**: Plan specifies T1→T2 at 50pts, T1/T2→T3 at 62pts (not trigger-based)
3. **Risk gate**: Completely missing from current .cs files. Need: daily loss 0.40%, correlation cap, position sizing
4. **12PM hard exit**: Must be API-level enforced, not just strategy-level

### Track B — Crypto Phase 6 Missing
- **Structural Validity Firewall**: Must validate assets BEFORE ingestion (age >30d, vol >$10M, book depth >0.5%, funding <0.1%)
- **Structural Decay Monitor**: Live monitoring with auto-blacklist when metrics degrade

## MAD's Questions/Directives Pending
1. Asset tier thresholds for ES/NQ/GC/CL for NT8
2. Tradovate API credentials for Python REST/WS client build

## Files Needing Updates
- `tradovate/CEREBUS_ST_NT8.cs` — add risk gate, gear shift, per-asset tiers
- `tradovate/CEREBUS_P90_NT8.cs` — add risk gate, session enforcement
- `tradovate/CEREBUS_AssetPresets.cs` — add futures asset presets
- `crypto/CryptoAssetScanner.py` — add structural validity firewall (Phase 6)

## What I Did NOT Do
- Did NOT start implementing any changes (awaiting MAD confirmation)
- Did NOT spawn any subagents
- Did NOT touch NT8 files without confirmation

---
*Logged: 2026-05-31 22:35 EDT — Awaiting MAD confirmation on asset thresholds and path forward*

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[Agents]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Oce Unified Frontend Plan]]
[[Operator Rules]]
[[O 6 Implementation Plan]]
[[User]]
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
[[Memory]]
[[Metrics]]
