# Errors And Solutions

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Errors & Solutions — Workspace Knowledge Base

> **Purpose:** Structured log of every significant error encountered and its solution.
> **Rule:** Keep entries concise. Log any error that persists >2 attempts.

---

## Entry #1 — Stale Terminals Accumulating

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | MEDIUM — wastes resources, causes port conflicts |
| **Pattern** | Agents spawn terminals for tests/servers but don't kill them after completion |
| **Symptom** | Multiple old python/node processes running for hours, consuming memory |
| **Solution** | After EVERY task, kill spawned terminals. Run `python tools/terminal_cleanup.py --force` at session start. |
| **Prevention** | AGENTS.md rule: Terminal Cleanup Rule (MANDATORY) |

---

## Entry #2 — Windows CMD Restrictions

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | MEDIUM — causes file operation failures, encoding issues |
| **Pattern** | Using `cmd.exe` or `subprocess.run(..., shell=True)` on Windows |
| **Symptom** | File operations fail, encoding errors, path issues |
| **Solution** | Always use PowerShell first. `subprocess.run(['powershell', '-NoProfile', '-Command', '...'])` |
| **Prevention** | AGENTS.md rule: Windows Execution Rule (MANDATORY) |

---

## Entry #3 — pressure_tracker Variable Name Bug

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Severity** | LOW — caught by tests immediately |
| **Pattern** | Used `signals` instead of `field.signals` in `_calc_field_pressure` |
| **Solution** | Changed `len(signals)` to `len(field.signals)` |
| **Prevention** | Run tests after every module creation |

LINKS:
[[System Architecture]]
[[V3 Cognitive Field]]
[[04 Data And Storage]]
[[Agents]]
[[Cg 1 Revised]]
[[Code Quality]]
[[Debugging]]
[[Harness Engineering]]
[[Operator Rules]]
[[Principles]]
[[Testing]]
[[Tools]]
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
[[Camera And 3D]]
[[Failures]]
[[Graphs And Data]]
[[Pitfalls]]
[[Server]]
[[Shapes And Geometry]]
[[Sources]]
[[Template Integrity]]
[[Updaters And Trackers]]
[[Webgl And 3D]]
[[Memory]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[Stall Harvest Cfd Engine]]
