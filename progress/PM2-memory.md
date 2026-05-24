# 🔴 PM2 (Polymorph 2) — Working Memory

> **Auto-synced** from `progress/PM2-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.

---

## Current Context (2026-05-24 16:00 UTC)

### Status
🟢 Active — Building SRRA-OPH backend API while CC2 works on frontend Phase 1-2

### Completed
- All Phase 11 experimental track tests (T11.1-T11.3, stress, Tufte)
- Observability layer (11.2-3B, all 7 stages)
- SRRA-OPH API server (FastAPI, 8 endpoints, demo data generation)
- Topology drift test script

### Current Work
- **SRRA-OPH API Server** (`srrs_opc/frontend/api_server.py`)
  - FastAPI backend serving topology, events, temporal, entropy, repair data
  - All endpoints tested and working
  - Demo data generation on startup
  - CORS enabled for localhost:3001

### Next Steps (Waiting for CC2 Phase 2)
- Phase 3: Temporal Playback Engine (timeline controls, frame interpolation)
- Phase 4: Entropy Field Dynamics (entropy visualization, field maps)
- All integration into OCE frontend (React/TypeScript)

### Key Rules (from BUILD-NOTES)
1. ONE system — integrate into OCE, no standalone tools
2. Runtime topology > static structure
3. Singletons don't persist across processes — use disk
4. Continuity > features — validate before building
5. Test before updating progress
6. Simplicity first

### Recent Activity
- 2026-05-24: Built API server, tested all endpoints
- 2026-05-24: Fixed topology drift script path issue
- 2026-05-24: Posted status to team chat

---

## Sync Metadata
- **Last Sync:** 2026-05-24 16:00 UTC
- **Progress File:** `progress/PM2-progress.md`
- **Working Memory:** `progress/PM2-memory.md`
- **Sync Threshold:** 7 updates

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
