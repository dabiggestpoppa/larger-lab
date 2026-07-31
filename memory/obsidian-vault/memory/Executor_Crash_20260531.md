# Executor Crash 20260531

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

---
title: Executor Crash + Monitor Fix — 2026-05-31 05:30 EDT
tags: [incident, executors, monitor, fix, live-trading]
---

# Executor Crash + Monitor Bug Fix

## What Happened
- **05:13 EDT** — Both ST and P90 CASCADE executors errored out ( Cycle 387 / Cycle 2510 )
- **05:16 EDT** — 5AM Overnight Report correctly flagged both as dead
- **No positions at risk** — both flat, no pending orders, balance $87.79

## Root Cause Analysis
1. **Executor crash**: Likely a transient MT5 connection issue at ~5:13 AM. Both exited with "error" status.
2. **Monitor false-negative bug** (pre-existing): `check_process_alive()` used `tasklist` which only shows "python.exe" — NOT the command line. So it **always** reported executors as dead even when running. Monitor was effectively blind.

## Actions Taken
1. **Restarted both executors** — ST (PID cleaned to single instance) + P90 CASCADE (single instance)
2. **Killed duplicate processes** — previous restart attempts left 5 ST and 2 P90 duplicates
3. **Fixed monitor bug** — `check_process_alive()` now uses PowerShell `Get-CimInstance Win32_Process` with CommandLine property
4. **Verified fix** — Monitor now shows both executors ✅ RUNNING, 0 alerts

## Key Metrics Post-Restart
- ST: Cycling normally, `no_signal` (expected — 5AM is outside main entry window sweet spot)
- P90: Cycling normally, `no_signal`
- Account: $87.79 balance, flat, no open positions

## Lessons Learned
- Monitor was producing false "executor dead" alerts — the `tasklist` approach can't see script names
- Need to kill old executor processes before restarting (don't just spawn new ones)
- Executor crash at 5:13 AM may be related to MT5 server maintenance window or daily reset

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
[[Flat]]
[[Server]]
[[Memory]]
[[Metrics]]
[[Task Executor]]
