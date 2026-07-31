# Build Patterns

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Build Patterns — Successful Operational Patterns

TYPE: pattern
SUMMARY: Recurring successful patterns extracted from the lab's build history.
CAUSE: Pattern crystallization requires a library of successful patterns to reference.
FUNCTION: Reference for proven approaches to common build tasks.

## Pattern 1: Duplicate Endpoint Detection
**Conditions:** FastAPI app has multiple route registrations
**Detection:** `python -c "from oce.backend.main import app; from collections import Counter; paths = [r.path for r in app.routes if hasattr(r, 'path')]; dupes = [p for p, c in Counter(paths).items() if c > 1]; print('DUPES:', dupes)"`
**Fix:** Remove the second registration, keep the first
**Result:** Clean route table, no shadowing

## Pattern 2: Phase Wiring
**Conditions:** New phase components need API endpoints
**Approach:** Add endpoints to existing register_* function in vault_api.py, import in main.py
**Key:** Each register_* function takes `app: FastAPI` as single argument
**Result:** Endpoints auto-register on app startup

## Pattern 3: Test-Driven Phase Verification
**Conditions:** Phase build claims completion
**Approach:** Run `python -m pytest core/obsidian/tests/ core/execution/tests/ core/skills/tests/ oce/tests/ --tb=short`
**Target:** 100% pass rate before certification
**Result:** Certified build with full test coverage

## Pattern 4: Vault Note Standardization
**Conditions:** Writing knowledge to Obsidian vault
**Approach:** Use VaultWriter with CAUSE/FIX/RESULT/LINKS content dict
**Key:** Always include TYPE, SUMMARY, STATUS, SOURCE fields
**Result:** Consistent, searchable, linkable knowledge base

## Pattern 5: Subagent Delegation
**Conditions:** Multi-step task with independent deliverables
**Approach:** Spawn one subagent per deliverable, each writes checkpoint to progress file
**Key:** Manager NEVER executes — only plans, spawns, monitors, aggregates
**Result:** Parallel execution with full traceability

RELATIONSHIPS: [[O2C Pipeline]] [[Foundational Principles]] [[Team Roster]]

STATUS: active
SOURCE: team-chat.md, build history

LINKS:
[[Note Standard]]
[[Vault]]
[[Memory]]
[[System]]
[[Standard]]
[[Skill]]
[[Server]]
[[Patterns]]
[[Network Patterns]]
[[Modules]]
[[Experiment Patterns]]
[[Api Endpoints]]
[[Welcome]]
[[Vault Distillation 20260531 0245]]
[[Tradovate Api Discovery 20260531]]
[[Track A Ninjascript Build 20260531]]
[[Track A Build Status]]
[[Track A Build Complete 20260531]]
[[Test Pattern]]
[[Test Note]]
[[Team Phase01 Status]]
[[Task Flow]]
[[Srra Oph]]
[[Session Testagent 20260531 0245 Full]]
[[Session Testagent 20260531 0245]]
[[Session 20260531 2200]]
[[Self Heal Report]]
[[Sage Audit Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit 20260531 Environment Utilization]]
[[Quantlab Bible]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Progress]]
[[Pm2 Test Note]]
[[Option A Confirmed 20260531]]
[[Operational State 20260531]]
[[Ontology Core Summary]]
[[Oc2 Vault Access Guide]]
[[Oc2 Identity]]
[[Oc2 Gateway Failures]]
[[Obsidian Vault Connection Info]]
[[Observer Core O1 O7]]
[[Module Guide Summary]]
[[Master Plan Assessment 20260531]]
[[Live Deployment Status]]
[[Keyerror Data Validation 20260531 0245]]
[[Journal 20260602T005953Z Task Update]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Graph]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Activation Note]]
[[Failure Index Oc2]]
[[Executor Crash 20260531]]
[[Errors And Solutions]]
[[Doctor Prescription]]
[[Dashboard Build Complete]]
[[Daily Runtime 20260531]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Build Progress 20260531]]
[[Backtest Phase Status]]
[[Backtest Campaign V3 Results]]
[[Backtest Campaign Status 20260531]]
[[Api Test Note]]
[[Api Reference Summary]]
[[Api Execution Architecture 20260531]]
[[Agent Topology]]
[[Active Strategies Performance]]
[[2026 06 01]]
[[2026 05 31]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 30 Evening]]
[[2026 05 30]]
[[2026 05 21]]
[[2026 05 20]]
[[2026 05 18]]
[[2026 05 17]]
[[Principles]]
[[Operator Rules]]
[[Module Guide]]
[[Api Reference]]
[[V3 Cognitive Field]]
[[System Architecture]]
[[Architecture]]
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[System Architecture — Complete Guide]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[CC Phase 01 Build Certification Report]]
[[KeyError — data_validation — 20260531_0245]]
[[Agent Topology — Relationship Map]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[O2C Pipeline — Cognitive Filesystem & Obsidian Mesh]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[API Reference — OCE Backend Endpoints]]
[[Module Guide — 78 Modules Reference]]
