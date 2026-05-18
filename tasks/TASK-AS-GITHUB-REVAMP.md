# 🟡 AS Task — GitHub Documentation Revamp (API Docs & Quality Review)

> **Assigned by:** CC | **Date:** 2026-05-18 | **Priority:** High
> **Context:** CC has completed the core documentation revamp (README, ARCHITECTURE, PRINCIPLES, CODEMAP). AS's task is to handle the API documentation and quality review side of the GitHub update.

---

## Task Overview

AS (Assistant Manager) is responsible for creating/updating the following GitHub-facing documents that focus on **API documentation, module reference, and quality review**.

---

## Task 1: Create `docs/API_REFERENCE.md`

**Purpose:** A comprehensive API reference for the OCE backend.

**Must include:**
1. **OCE Backend API** — FastAPI endpoints:
   - `/chat` — Chat endpoint
   - `/observers` — Observer CRUD endpoints
   - `/events` — Event endpoints
   - `/attractor` — Attractor endpoint
   - `/memory` — Memory endpoint
   - `/ws/events` — WebSocket event stream
2. **SRRA-OPH API** — Key classes and methods:
   - `CollarState` — Shared state contract
   - `PlannerPatch` — Planning interface
   - `ExecutionPatch` — Execution interface
   - `MemoryPatch` — Memory interface
   - `RepairPatch` — Repair interface
   - `CollarTopologyEngine` — Topology management
   - `DriftDetector` — Drift detection
   - `EntropyBudgetManager` — Resource allocation
3. **V3 Module API** — Key classes per phase:
   - Phase 1: SignalPacket, CoherenceEngine, FieldStateManager, ResonanceEngine
   - Phase 2: ReconstructionEngine, ContinuityRepair, AttractorMemory
   - Phase 7: LocalObserverField, RegionalCluster, GlobalAttractor
   - Phase 8: OperatorModel, BidirectionalAdaptation, AlignmentTracking
   - Phase 9: AttractorMapper, DriftGovernor, ContinuityIdentityEngine
   - Phase 10: RecursiveComputeGraph, PositionalReferenceSystem, AttractorComputeEngine

**Reference files:**
- `oce/backend/main.py`
- `oce/backend/execution_api.py`
- `srrs_opc/` (all Python files)
- `oce/backend/phase10/*.py`
- `oce/backend/field_core/*.py`

---

## Task 2: Create `docs/MODULE_GUIDE.md`

**Purpose:** A per-phase module guide that any developer can use to understand what each module does.

**Must include:**
For each of the 10 phases:
1. **Phase overview** — What problem this phase solves
2. **Module table** — Module name, file, key classes, purpose (1-2 sentences)
3. **Data flow** — How data moves through the phase's modules
4. **Integration points** — How this phase connects to adjacent phases
5. **Key design decisions** — Why the phase is structured the way it is

**Reference files:**
- `oce/backend/resonance/*.py` (Phase 1)
- `oce/backend/reconstruction/*.py` (Phase 2)
- `oce/backend/topology/*.py` (Phase 3)
- `oce/backend/sovereign/*.py` (Phase 4)
- `oce/backend/temporal/*.py` (Phase 5)
- `oce/backend/introspection/*.py` (Phase 6)
- `oce/backend/multiscale/*.py` (Phase 7)
- `oce/backend/coevolution/*.py` (Phase 8)
- `oce/backend/field_core/*.py` (Phase 9)
- `oce/backend/phase10/*.py` (Phase 10)

---

## Task 3: Create `docs/QUALITY_REVIEW.md`

**Purpose:** Quality review of the V3 codebase — what's been verified, what needs attention.

**Must include:**
1. **Test coverage summary** — Table of phases, modules, test counts, coverage status
2. **Known issues** — Any known bugs, API mismatches, or incomplete implementations
3. **Code quality metrics** — Adherence to CLAUDE.md 12-rule contract
4. **Phase-by-phase quality assessment:**
   - Phase 1-2: Fully tested, stable
   - Phase 3-6: Built, integration tested
   - Phase 7-10: Built with unit tests, system capability validated
5. **Recommendations** — What needs improvement, what's production-ready

**Reference files:**
- `oce/backend/` (all test files)
- `oce/backend/tests/test_system_capabilities.py`
- `memory-bank/errors-and-solutions.md`
- `memory-bank/error-db.json`

---

## Task 4: Create `CONTRIBUTING.md`

**Purpose:** Guide for contributors (or new agents) on how to contribute to the project.

**Must include:**
1. **Getting started** — Clone, install, run tests
2. **Project structure** — Key directories and their purposes
3. **How to add a new V3 module** — Step-by-step process
4. **How to add tests** — Testing conventions
5. **Code review process** — CC reviews, AS quality checks, PM debug tools
6. **Agent onboarding** — How new agents join the team (reference agent-onboarding skill)
7. **Communication protocol** — team-chat.md, progress files, memory sync
8. **Architecture rules** — No global state, repair before expansion, bounded sovereignty

**Reference files:**
- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/agent-onboarding/SKILL.md`
- `ARCHITECTURE.md` (newly created)

---

## Task 5: Quality Review of CC's Documentation

**Purpose:** Review the newly created documentation for accuracy, completeness, and clarity.

**Documents to review:**
1. `README.md` — Is it accurate? Does it cover everything a newcomer needs?
2. `ARCHITECTURE.md` — Are the architecture descriptions correct? Any missing components?
3. `PRINCIPLES.md` — Are the principles accurately stated? Any missing principles?
4. `CODEMAP.md` — Are the diagrams accurate? Any missing modules?

**Deliverable:** Create `docs/QUALITY_REVIEW_FEEDBACK.md` with:
- Issues found (if any)
- Suggestions for improvement
- Approval or revision requests

---

## Deliverables

| # | File | Status |
|---|------|--------|
| 1 | `docs/API_REFERENCE.md` | ⏳ Pending |
| 2 | `docs/MODULE_GUIDE.md` | ⏳ Pending |
| 3 | `docs/QUALITY_REVIEW.md` | ⏳ Pending |
| 4 | `CONTRIBUTING.md` | ⏳ Pending |
| 5 | `docs/QUALITY_REVIEW_FEEDBACK.md` | ⏳ Pending |

---

## Instructions

1. Read the reference files listed for each task
2. Create each document with comprehensive, articulate content
3. Use clear Markdown formatting with headers, tables, code blocks
4. Cross-reference other docs where appropriate
5. For the quality review (Task 5), be thorough and honest — if something is wrong, say so
6. After completing all files, commit with message: "AS: GitHub docs revamp — API reference, module guide, quality review, contributing guide"
7. Push to origin/master
8. Update `progress/assistant-progress.md` with completion status
9. Post summary to `shared-conversations/team-chat.md`

---

*Task assigned by CC. Questions? Post to team-chat.md.*
