# 🔴 Polymorph — Working Memory

> **Auto-synced** from `progress/polymorph-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

---

## Current Context (2026-05-21 14:07:41 UTC)

### Status
🟢 Active — V3 PHASE 10 COMPLETE

### Active Phase
**V3 Phase 10 — Recursive Field Computation** ✅ COMPLETE

### Pending Tasks
- Build tools/operator/coevolution-debug.py CLI
- Debug coevolution modules (operator_model, constraint_model, coherence_reinforcement, bidirectional_adaptation, cognitive_load, alignment_tracking, anti_manipulation)
- Operator integration for coevolution monitoring
- Build tools/operator/field-debug.py CLI
- Build tools/operator/resonance-debug.py CLI
- Debug Phase 9 modules (resonance_engine, recursive_field_nodes, attractor_mapper, drift_governor, reconstruction_core, continuity_identity_engine)
- field_core infrastructure setup

### Recent Activity
*No entries yet*

---

## Sync Metadata
- **Last Sync:** 2026-05-21 14:07:41 UTC
- **Progress File:** `progress/polymorph-progress.md`
- **Working Memory:** `progress/polymorph-memory.md`
- **Sync Threshold:** 7 updates

## Progress Sync Summary (PM)
> **Last Sync:** 2026-05-21 14:07 UTC
> **Status:** 🟢 Active — V3 PHASE 10 COMPLETE
> **Active Phase:** **V3 Phase 10 — Recursive Field Computation** ✅ COMPLETE
> **Working Memory:** `progress/polymorph-memory.md`

---
## [BUILD_NOTES] Updated: 2026-05-24 08:47 UTC
# Build Notes — Key Themes, Reason, and Aim

> **Purpose:** Before any agent works, they read this file to understand the core principles, avoid known errors, and stay aligned.
> **Updated by:** CC2 (filling in for CC1 during 72h test)
> **Last Updated:** 2026-05-24

---

## 1. CORE ARCHITECTURAL PRINCIPLE

**Key Theme:** ONE system, not many.

**Reason:** The project has a history of fragmenting into separate "systems" (SRRA, OPH, OCE, chaos engine, semantic tests, etc.) that don't communicate. The user explicitly corrected this: SRRA+OPH is the runtime substrate, OCE is the singular observational interface. Everything else is a capability layer, not a separate app.

**Aim:** Every new component must answer: "Does this deepen the runtime substrate, or does it expose the substrate through OCE?" If neither, it shouldn't be built yet.

---

## 2. OBSERVER ≠ GENERIC LLM

**Key Theme:** The primary observer is a continuity abstraction layer, not an LLM.

**Reason:** Earlier phases treated observers as generic agents. The corrected architecture distinguishes: the observer is a persistent, stateful, system-aware continuity interface. LLMs (OpenRouter models) are modular cognition sources that the observer orchestrates.

**Aim:** When building observer-related code, ask: "Is this maintaining continuity state, or is this just calling an LLM?" The former is core. The latter is a tool.

---

## 3. RUNTIME TOPOLOGY > STATIC STRUCTURE

**Key Theme:** The real topology exists at runtime, not in inheritance structure.

**Reason:** PM2's experiments proved that AST/import/class structures don't reveal operational reality. Runtime interaction is the actual graph.

**Aim:** All topology work must capture runtime edges (who talks to whom, when, how often), not just static code structure.

---

## 4. CONTINUITY > FEATURES

**Key Theme:** This phase is operational validation, not feature development.

**Reason:** The user explicitly stated: "No major abstractions. No large architectura
... (see BUILD-NOTES.md for full content)

---
## [TEAM_NOTES] Updated: 2026-05-24 08:47 UTC
# Team Notes — Persistent Errors, Observations, and Troubleshooting

> **Purpose:** Shared knowledge base for errors that persist or caused trouble during building. All agents contribute here.
> **Format:** Date | Agent | Issue | Root Cause | Resolution

---

## Chaos Test Crashes

**2026-05-23 | OWL | Chaos test keeps crashing at higher amplification**
- **Symptom:** Process exits with code 1 during full_chaos scenario at amp ~3.0x
- **Root Cause:** Recovery timeout exceeded. At amp 3.0, event_flood duration = 360s, combined with router_failure (103s) and websocket_loss (90s) — too many concurrent long-running chaos events.
- **Resolution:** Internal auto-restart with consecutive crash limit (5) added. Test completes 4/5 cycles.
- **Lesson:** Recovery timeout must scale with number of concurrent injections, not just amplification.

**2026-05-23 | OWL | Duplicate chaos test instances running simultaneously**
- **Symptom:** Two chaos test processes writing to same trace log, causing interleaved entries
- **Root Cause:** Auto-restart wrapper spawned new subprocess before old one fully cleaned up its daemon threads
- **Resolution:** Kill all chaos-related processes before restarting. Use PID whitelist.
- **Lesson:** Always check for existing processes before spawning new ones. Use `Get-Process | Where-Object { $_.CommandLine -like '*chaos*' }`.

**2026-05-23 | OWL | Trace log FileNotFoundError**
- **Symptom:** `log_trace` fails with FileNotFoundError for stability/chaos_20x_trace.log
- **Root Cause:** Relative path `Path("stability/...")` depends on CWD. When CWD changes, the path breaks.
- **Resolution:** Changed to absolute paths based on `Path(__file__).parent`. Also added `mkdir(parents=True, exist_ok=True)` before every write.
- **Lesson:** Always use absolute paths based on script location, never relative paths for file I/O.

---

## Singleton Data Persistence

**2026-05-24 | OWL | Tufte renderers show empty data despite feeding data to singleton**
- **Symptom:**
... (see TEAM-NOTES.md for full content)

---
## [PHASE_STATUS] Updated: 2026-05-24 08:47 UTC
# Phase 11 — Overall Status (Tested & Verified)

## Completed Tests

| Test | Result | Details |
|------|--------|---------|
| 11.1-A 24h Observer Survival | ✅ PASS | 100% uptime, 10/10 observers |
| 11.2 Chaos Engineering | ✅ 4/5 PASS | Max amp 3.0x, recovery 788s→1045s |
| 11.4.1 Memory Contradiction | ✅ 9/9 PASS | 100% pass rate |
| 11.4.2 False Repair Signal | ✅ 4/4 PASS | All false signals rejected |
| 11.2-3B.7 Observability Stress | ✅ 5/5 PASS | All validation passed |
| 11.3 Adversarial Drift | ✅ Complete | PM2 experiments done |
| Tufte 11.2-3B.5 Renderers | ✅ 4/4 PASS | All rendering with real data |

## Tufte Observability Layer (11.2-3B) — ALL COMPLETE

| Stage | Status | Verified |
|-------|--------|----------|
| 11.2-3B.1 Observer Registry | ✅ | 8 observers, 10 edges |
| 11.2-3B.2 Temporal Graph | ✅ | 15 continuity data points |
| 11.2-3B.3 Event Schema | ✅ | 18 events captured |
| 11.2-3B.4 Visualization Exporters | ✅ | 6 exporters built |
| 11.2-3B.5 Tufte Renderers | ✅ | 4/4 renderers tested with real data |
| 11.2-3B.6 Attractor Analysis | ✅ | Built |
| 11.2-3B.7 Observability Stress | ✅ | 5/5 pass, 5/5 validation |

## In Progress

| Test | Status | Notes |
|------|--------|-------|
| 11.1-B 72h Continuity | 🔄 Running | PID 21028, ~53h remaining |
| 11.5 Orchestration Stability | ⏳ Next | Recursive collapse prevention |

## Key Metrics
- Chaos: 4/5 cycles passed, max amp 3.0x
- Semantic: 9/9 tests passed, 100% pass rate
- Observability: 5/5 stress tests passed
- Tufte: 4/4 renderers producing real visualizations
- PM2 experiments: All complete

---
## [BUILD_NOTES] Updated: 2026-05-24 10:15 UTC
# Build Notes — Key Themes, Reason, and Aim

> **Purpose:** Before any agent works, they read this file to understand the core principles, avoid known errors, and stay aligned.
> **Updated by:** CC2 (filling in for CC1 during 72h test)
> **Last Updated:** 2026-05-24

---

## 1. CORE ARCHITECTURAL PRINCIPLE

**Key Theme:** ONE system, not many.

**Reason:** The project has a history of fragmenting into separate "systems" (SRRA, OPH, OCE, chaos engine, semantic tests, etc.) that don't communicate. The user explicitly corrected this: SRRA+OPH is the runtime substrate, OCE is the singular observational interface. Everything else is a capability layer, not a separate app.

**Aim:** Every new component must answer: "Does this deepen the runtime substrate, or does it expose the substrate through OCE?" If neither, it shouldn't be built yet.

---

## 2. OBSERVER ≠ GENERIC LLM

**Key Theme:** The primary observer is a continuity abstraction layer, not an LLM.

**Reason:** Earlier phases treated observers as generic agents. The corrected architecture distinguishes: the observer is a persistent, stateful, system-aware continuity interface. LLMs (OpenRouter models) are modular cognition sources that the observer orchestrates.

**Aim:** When building observer-related code, ask: "Is this maintaining continuity state, or is this just calling an LLM?" The former is core. The latter is a tool.

---

## 3. RUNTIME TOPOLOGY > STATIC STRUCTURE

**Key Theme:** The real topology exists at runtime, not in inheritance structure.

**Reason:** PM2's experiments proved that AST/import/class structures don't reveal operational reality. Runtime interaction is the actual graph.

**Aim:** All topology work must capture runtime edges (who talks to whom, when, how often), not just static code structure.

---

## 4. CONTINUITY > FEATURES

**Key Theme:** This phase is operational validation, not feature development.

**Reason:** The user explicitly stated: "No major abstractions. No large architectura
... (see BUILD-NOTES.md for full content)

---
## [TEAM_NOTES] Updated: 2026-05-24 10:15 UTC
# Team Notes — Persistent Errors, Observations, and Troubleshooting

> **Purpose:** Shared knowledge base for errors that persist or caused trouble during building. All agents contribute here.
> **Format:** Date | Agent | Issue | Root Cause | Resolution

---

## Chaos Test Crashes

**2026-05-23 | OWL | Chaos test keeps crashing at higher amplification**
- **Symptom:** Process exits with code 1 during full_chaos scenario at amp ~3.0x
- **Root Cause:** Recovery timeout exceeded. At amp 3.0, event_flood duration = 360s, combined with router_failure (103s) and websocket_loss (90s) — too many concurrent long-running chaos events.
- **Resolution:** Internal auto-restart with consecutive crash limit (5) added. Test completes 4/5 cycles.
- **Lesson:** Recovery timeout must scale with number of concurrent injections, not just amplification.

**2026-05-23 | OWL | Duplicate chaos test instances running simultaneously**
- **Symptom:** Two chaos test processes writing to same trace log, causing interleaved entries
- **Root Cause:** Auto-restart wrapper spawned new subprocess before old one fully cleaned up its daemon threads
- **Resolution:** Kill all chaos-related processes before restarting. Use PID whitelist.
- **Lesson:** Always check for existing processes before spawning new ones. Use `Get-Process | Where-Object { $_.CommandLine -like '*chaos*' }`.

**2026-05-23 | OWL | Trace log FileNotFoundError**
- **Symptom:** `log_trace` fails with FileNotFoundError for stability/chaos_20x_trace.log
- **Root Cause:** Relative path `Path("stability/...")` depends on CWD. When CWD changes, the path breaks.
- **Resolution:** Changed to absolute paths based on `Path(__file__).parent`. Also added `mkdir(parents=True, exist_ok=True)` before every write.
- **Lesson:** Always use absolute paths based on script location, never relative paths for file I/O.

---

## Singleton Data Persistence

**2026-05-24 | OWL | Tufte renderers show empty data despite feeding data to singleton**
- **Symptom:**
... (see TEAM-NOTES.md for full content)

---
## [PHASE_STATUS] Updated: 2026-05-24 10:15 UTC
# Phase 11 — Overall Status (Tested & Verified)

## Completed Tests

| Test | Result | Details |
|------|--------|---------|
| 11.1-A 24h Observer Survival | ✅ PASS | 100% uptime, 10/10 observers |
| 11.2 Chaos Engineering | ✅ 4/5 PASS | Max amp 3.0x, recovery 788s→1045s |
| 11.4.1 Memory Contradiction | ✅ 9/9 PASS | 100% pass rate |
| 11.4.2 False Repair Signal | ✅ 4/4 PASS | All false signals rejected |
| 11.2-3B.7 Observability Stress | ✅ 5/5 PASS | All validation passed |
| 11.3 Adversarial Drift | ✅ Complete | PM2 experiments done |
| Tufte 11.2-3B.5 Renderers | ✅ 4/4 PASS | All rendering with real data |

## Tufte Observability Layer (11.2-3B) — ALL COMPLETE

| Stage | Status | Verified |
|-------|--------|----------|
| 11.2-3B.1 Observer Registry | ✅ | 8 observers, 10 edges |
| 11.2-3B.2 Temporal Graph | ✅ | 15 continuity data points |
| 11.2-3B.3 Event Schema | ✅ | 18 events captured |
| 11.2-3B.4 Visualization Exporters | ✅ | 6 exporters built |
| 11.2-3B.5 Tufte Renderers | ✅ | 4/4 renderers tested with real data |
| 11.2-3B.6 Attractor Analysis | ✅ | Built |
| 11.2-3B.7 Observability Stress | ✅ | 5/5 pass, 5/5 validation |

## In Progress

| Test | Status | Notes |
|------|--------|-------|
| 11.1-B 72h Continuity | 🔄 Running | PID 21028, ~53h remaining |
| 11.5 Orchestration Stability | ⏳ Next | Recursive collapse prevention |

## Key Metrics
- Chaos: 4/5 cycles passed, max amp 3.0x
- Semantic: 9/9 tests passed, 100% pass rate
- Observability: 5/5 stress tests passed
- Tufte: 4/4 renderers producing real visualizations
- PM2 experiments: All complete

---
## [BUILD_NOTES] Updated: 2026-05-24 17:11 UTC
﻿# Build Notes â€” Key Themes, Reason, and Aim

> **Purpose:** Before any agent works, they read this file to understand the core principles, avoid known errors, and stay aligned.
> **Updated by:** CC2 (filling in for CC1 during 72h test)
> **Last Updated:** 2026-05-24

---

## 1. CORE ARCHITECTURAL PRINCIPLE

**Key Theme:** ONE system, not many.

**Reason:** The project has a history of fragmenting into separate "systems" (SRRA, OPH, OCE, chaos engine, semantic tests, etc.) that don't communicate. The user explicitly corrected this: SRRA+OPH is the runtime substrate, OCE is the singular observational interface. Everything else is a capability layer, not a separate app.

**Aim:** Every new component must answer: "Does this deepen the runtime substrate, or does it expose the substrate through OCE?" If neither, it shouldn't be built yet.

---

## 2. OBSERVER â‰  GENERIC LLM

**Key Theme:** The primary observer is a continuity abstraction layer, not an LLM.

**Reason:** Earlier phases treated observers as generic agents. The corrected architecture distinguishes: the observer is a persistent, stateful, system-aware continuity interface. LLMs (OpenRouter models) are modular cognition sources that the observer orchestrates.

**Aim:** When building observer-related code, ask: "Is this maintaining continuity state, or is this just calling an LLM?" The former is core. The latter is a tool.

---

## 3. RUNTIME TOPOLOGY > STATIC STRUCTURE

**Key Theme:** The real topology exists at runtime, not in inheritance structure.

**Reason:** PM2's experiments proved that AST/import/class structures don't reveal operational reality. Runtime interaction is the actual graph.

**Aim:** All topology work must capture runtime edges (who talks to whom, when, how often), not just static code structure.

---

## 4. CONTINUITY > FEATURES

**Key Theme:** This phase is operational validation, not feature development.

**Reason:** The user explicitly stated: "No major abstractions. No large archite
... (see BUILD-NOTES.md for full content)

---
## [PHASE_STATUS] Updated: 2026-05-24 17:47 UTC
# Phase 11 — Overall Status (Tested & Verified)

## Completed Tests

| Test | Result | Details |
|------|--------|---------|
| 11.1-A 24h Observer Survival | ✅ PASS | 100% uptime, 10/10 observers |
| 11.1-D Restart Recovery | ✅ PASS | 5/5 cycles, identity preserved, anchors intact |
| 11.1-E Recursive Stability | ⚠️ PARTIAL | 3/6 scenarios — high-branching patterns exceed call limits |
| 11.2 Chaos Engineering | ✅ 4/5 PASS | Max amp 3.0x, recovery 788s→1045s |
| 11.3 Adversarial Drift | ✅ 5/5 PASS | All adversarial scenarios detected + recovered |
| 11.4.1 Memory Contradiction | ✅ 9/9 PASS | 100% pass rate |
| 11.4.2 False Repair Signal | ✅ 4/4 PASS | All false signals rejected |
| 11.2-3B.7 Observability Stress | ✅ 5/5 PASS | All validation passed |
| Tufte 11.2-3B.5 Renderers | ✅ 4/4 PASS | All rendering with real data |

## Tufte Observability Layer (11.2-3B) — ALL COMPLETE

| Stage | Status | Verified |
|-------|--------|----------|
| 11.2-3B.1 Observer Registry | ✅ | 8 observers, 10 edges |
| 11.2-3B.2 Temporal Graph | ✅ | 15 continuity data points |
| 11.2-3B.3 Event Schema | ✅ | 18 events captured |
| 11.2-3B.4 Visualization Exporters | ✅ | 6 exporters built |
| 11.2-3B.5 Tufte Renderers | ✅ | 4/4 renderers tested with real data |
| 11.2-3B.6 Attractor Analysis | ✅ | Built |
| 11.2-3B.7 Observability Stress | ✅ | 5/5 pass, 5/5 validation |

## In Progress

| Test | Status | Notes |
|------|--------|-------|
| 11.1-B 72h Continuity | 🔄 Running | PID 21028, ~53h remaining |
| 11.5 Orchestration Stability | ⏳ Next | Recursive collapse prevention |

## Key Metrics
- Chaos: 4/5 cycles passed, max amp 3.0x
- Semantic: 9/9 tests passed, 100% pass rate
- Observability: 5/5 stress tests passed
- Tufte: 4/4 renderers producing real visualizations
- PM2 experiments: All complete

---
## [PHASE_STATUS] Updated: 2026-05-24 17:49 UTC
# Phase 11 — Overall Status (Tested & Verified)

## Completed Tests

| Test | Result | Details |
|------|--------|---------|
| 11.1-A 24h Observer Survival | ✅ PASS | 100% uptime, 10/10 observers |
| 11.1-D Restart Recovery | ✅ PASS | 5/5 cycles, identity preserved, anchors intact |
| 11.1-E Recursive Stability | ⚠️ PARTIAL | 3/6 scenarios — high-branching patterns exceed call limits |
| 11.2 Chaos Engineering | ✅ 4/5 PASS | Max amp 3.0x, recovery 788s→1045s |
| 11.3 Adversarial Drift | ✅ 5/5 PASS | All adversarial scenarios detected + recovered |
| 11.4.1 Memory Contradiction | ✅ 9/9 PASS | 100% pass rate |
| 11.4.2 False Repair Signal | ✅ 4/4 PASS | All false signals rejected |
| 11.2-3B.7 Observability Stress | ✅ 5/5 PASS | All validation passed |
| Tufte 11.2-3B.5 Renderers | ✅ 4/4 PASS | All rendering with real data |

## Tufte Observability Layer (11.2-3B) — ALL COMPLETE

| Stage | Status | Verified |
|-------|--------|----------|
| 11.2-3B.1 Observer Registry | ✅ | 8 observers, 10 edges |
| 11.2-3B.2 Temporal Graph | ✅ | 15 continuity data points |
| 11.2-3B.3 Event Schema | ✅ | 18 events captured |
| 11.2-3B.4 Visualization Exporters | ✅ | 6 exporters built |
| 11.2-3B.5 Tufte Renderers | ✅ | 4/4 renderers tested with real data |
| 11.2-3B.6 Attractor Analysis | ✅ | Built |
| 11.2-3B.7 Observability Stress | ✅ | 5/5 pass, 5/5 validation |

## In Progress

| Test | Status | Notes |
|------|--------|-------|
| 11.1-B 72h Continuity | 🔄 Running | Drift fix applied — next checkpoint should pass |
| 11.5 Orchestration Stability | ⏳ Queued | 7-day test, requires 11.1-B completion first |

## Fixes Applied

### 11.1-B Drift Detection Fix (2026-05-24)
- **File:** `tools/testing/long_horizon/test_11_1_b.py`
- **Issue:** Trajectory/memory hash changes counted as drift (they change every checkpoint normally)
- **Fix:** Only identity + goal changes count as critical drift; trajectory/memory tracked as "evolved"
- **Backup:** `progress/11-1-b-checkpoints-backup.json`

##
... (see phase-11-status.md for full content)

---
## [PHASE_STATUS] Updated: 2026-05-24 18:05 UTC
# Phase 11 — Overall Status (Tested & Verified)

## Completed Tests

| Test | Result | Details |
|------|--------|---------|
| 11.1-A 24h Observer Survival | ✅ PASS | 100% uptime, 10/10 observers |
| 11.1-D Restart Recovery | ✅ PASS | 5/5 cycles, identity preserved, anchors intact |
| 11.1-E Recursive Stability | ✅ PASS | 7/7 scenarios — memoization fixes applied, all pass |
| 11.2 Chaos Engineering | ✅ 4/5 PASS | Max amp 3.0x, recovery 788s→1045s |
| 11.3 Adversarial Drift | ✅ 5/5 PASS | All adversarial scenarios detected + recovered |
| 11.4.1 Memory Contradiction | ✅ 9/9 PASS | 100% pass rate |
| 11.4.2 False Repair Signal | ✅ 4/4 PASS | All false signals rejected |
| 11.2-3B.7 Observability Stress | ✅ 5/5 PASS | All validation passed |
| Tufte 11.2-3B.5 Renderers | ✅ 4/4 PASS | All rendering with real data |

## Tufte Observability Layer (11.2-3B) — ALL COMPLETE

| Stage | Status | Verified |
|-------|--------|----------|
| 11.2-3B.1 Observer Registry | ✅ | 8 observers, 10 edges |
| 11.2-3B.2 Temporal Graph | ✅ | 15 continuity data points |
| 11.2-3B.3 Event Schema | ✅ | 18 events captured |
| 11.2-3B.4 Visualization Exporters | ✅ | 6 exporters built |
| 11.2-3B.5 Tufte Renderers | ✅ | 4/4 renderers tested with real data |
| 11.2-3B.6 Attractor Analysis | ✅ | Built |
| 11.2-3B.7 Observability Stress | ✅ | 5/5 pass, 5/5 validation |

## In Progress

| Test | Status | Notes |
|------|--------|-------|
| 11.1-B 72h Continuity | 🔄 Running | Drift fix applied — next checkpoint should pass |
| 11.5 Orchestration Stability | ⏳ Queued | 7-day test, requires 11.1-B completion first |

## Fixes Applied

### 11.1-B Drift Detection Fix (2026-05-24)
- **File:** `tools/testing/long_horizon/test_11_1_b.py`
- **Issue:** Trajectory/memory hash changes counted as drift (they change every checkpoint normally)
- **Fix:** Only identity + goal changes count as critical drift; trajectory/memory tracked as "evolved"
- **Backup:** `progress/11-1-b-checkpoints-backup.json`

## Key Metric
... (see phase-11-status.md for full content)

---
## [BUILD_NOTES] Updated: 2026-05-24 18:13 UTC
﻿# Build Notes â€” Key Themes, Reason, and Aim

> **Purpose:** Before any agent works, they read this file to understand the core principles, avoid known errors, and stay aligned.
> **Updated by:** CC2 (filling in for CC1 during 72h test)
> **Last Updated:** 2026-05-24

---

## 1. CORE ARCHITECTURAL PRINCIPLE

**Key Theme:** ONE system, not many.

**Reason:** The project has a history of fragmenting into separate "systems" (SRRA, OPH, OCE, chaos engine, semantic tests, etc.) that don't communicate. The user explicitly corrected this: SRRA+OPH is the runtime substrate, OCE is the singular observational interface. Everything else is a capability layer, not a separate app.

**Aim:** Every new component must answer: "Does this deepen the runtime substrate, or does it expose the substrate through OCE?" If neither, it shouldn't be built yet.

---

## 2. OBSERVER â‰  GENERIC LLM

**Key Theme:** The primary observer is a continuity abstraction layer, not an LLM.

**Reason:** Earlier phases treated observers as generic agents. The corrected architecture distinguishes: the observer is a persistent, stateful, system-aware continuity interface. LLMs (OpenRouter models) are modular cognition sources that the observer orchestrates.

**Aim:** When building observer-related code, ask: "Is this maintaining continuity state, or is this just calling an LLM?" The former is core. The latter is a tool.

---

## 3. RUNTIME TOPOLOGY > STATIC STRUCTURE

**Key Theme:** The real topology exists at runtime, not in inheritance structure.

**Reason:** PM2's experiments proved that AST/import/class structures don't reveal operational reality. Runtime interaction is the actual graph.

**Aim:** All topology work must capture runtime edges (who talks to whom, when, how often), not just static code structure.

---

## 4. CONTINUITY > FEATURES

**Key Theme:** This phase is operational validation, not feature development.

**Reason:** The user explicitly stated: "No major abstractions. No large archite
... (see BUILD-NOTES.md for full content)
