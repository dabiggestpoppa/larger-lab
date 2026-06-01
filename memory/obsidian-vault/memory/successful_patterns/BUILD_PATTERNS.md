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
