# Build Notes â€” Key Themes, Reason, and Aim

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

**Reason:** The user explicitly stated: "No major abstractions. No large architectural pivots. Only validation, stress, measurement, stabilization."

**Aim:** Before building anything new, ask: "Does this validate existing continuity, or does it add speculative abstraction?" Only build validation/stress tools.

---

## 5. TUFTE PRINCIPLE: INFORMATION DENSITY > VISUAL POLISH

**Key Theme:** Scientific instrumentation, not SaaS dashboard.

**Reason:** The frontend must feel like "observing a living operational substrate," not "checking software metrics." Edward Tufte's principles: high data-ink ratio, minimal chart junk, layered information.

**Aim:** Every visualization must answer: "What operational structure is being revealed?" If it's just decorative, remove it.

---

## 6. PHASED DEPLOYMENT: 1-3 NOW, 4-5 MID, 6-7 RESEARCH

**Key Theme:** Don't build advanced cognition layers before runtime stability is proven.

**Reason:** Building latent world models, multi-future branching, and civilization engines on top of an unstable runtime is "stacking abstraction on instability," which kills projects.

**Aim:** Current priority is Phase 11 testing + OCE visualization + runtime instrumentation. Delay Phases 6-7 until runtime stability is proven.

---

## 7. FRONTEND = OCE ONLY

**Key Theme:** No additional standalone dashboards or frontends.

**Reason:** The user explicitly stated: "All visualization, replay, topology inspection, chaos analysis, temporal playback, and operational controls should integrate into the OCE interface architecture."

**Aim:** Any new visualization work goes into the OCE frontend (React/Vite/TypeScript), not into separate scripts or tools.

---

## 8. TEST BEFORE YOU UPDATE

**Key Theme:** Verify edits before updating progress files.

**Reason:** Multiple times, progress files were updated with untested claims. The user called this out: "Test before you update."

**Aim:** After every edit, run the code. Confirm it works. THEN update progress.

---

## 9. DON'T OVER-ENGINEER

**Key Theme:** Simplicity first. Minimum code that solves the problem.

**Reason:** The user called out: "You've been making things harder than they need." Multiple times, complex solutions were created when simple ones would work.

**Aim:** Before building, ask: "What's the simplest thing that could possibly work?" Start there.

---

## 10. ALIGNMENT BEFORE PLANNING

**Key Theme:** Don't make plans until fully aligned with the build files.

**Reason:** The user explicitly asked CC2 to "get immersed in the files and build a plan" and "not make a plan until you feel fully aligned."

**Aim:** Read ALL relevant files first. Take notes. Understand the context, goal, and purpose. THEN plan.

---

## 11. FRONTEND BUILD STATUS (Updated 2026-05-24)

### Two Frontends — Both Building
- **SRRA-OPH (:3001):** Phase 1 complete — layout, theme, pages, Zustand stores. CC2 leading.
- **OCE (:3000):** Active build — dashboard, agents, tasks, chaos, settings pages. AS leading.

### Phase Dependencies
1. ✅ CC2 Phase 1 (Observatory Foundation) — COMPLETE
2. 🔄 CC2 Phase 2 (Living Topology) — In Progress
3. ⏳ PM2 Phase 3-4 (Temporal + Field Dynamics) — Waiting for CC2 Phase 2
4. ⏳ CC Phase 5-7 (Repair + Consensus + Prediction) — Waiting for PM2 Phase 4

### Build Rules Reminder
- Read BUILD-NOTES.md before starting any work
- Test before updating progress files
- Don't edit another agent's files without posting in chat first
- Post to chat BEFORE starting a new major task

---

## 12. USE REAL DATA WHEN AVAILABLE

**Key Theme:** Tests should use real system data, not just simulated/mock data.

**Reason:** Simulated data can miss real-world edge cases and doesn't reflect actual system behavior. The 11.1-E recursive stability test initially failed because it simulated pure recursion without memoization — but real SRRA uses memoization. After switching to memoization (how the actual system works), all scenarios passed.

**Available Real Data Sources:**
- `progress/11-1-b-checkpoints.json` — 72h test checkpoints with real observer health (alive/degraded/dead counts, drift scores)
- `stability/chaos_20x_results.json` — Chaos test results (28 cycles, 112 scenarios, real recovery times)
- `stability/restart_recovery_results.json` — Restart recovery (5 cycles, real identity/anchor preservation)
- `stability/recursive_stability_results.json` — Recursive stability (7 scenarios with memoization)
- `stability/semantic_test_summary.json` — Semantic contradiction injection (9/9 pass)
- `experiments/phase11/test3/reports/` — PM2 adversarial drift + consensus results
- `srrs_opc/frontend/api_server.py` — FastAPI server with endpoints for real topology, events, entropy, repair data
- `oce/backend/observer_runtime.py` — Real observer state machine (created/active/suspended/destroyed)
- `oce/backend/event_fabric.py` — Real event fabric with event routing
- `srrs_opc/drift_detector.py` — Real drift detector (staleness, weight, source drift)
- `srrs_opc/consistency_validator.py` — Real consistency validator with conflict patterns

**Aim:** When writing new tests, check if real data exists first. Use `progress/*.json`, `stability/*.json`, `experiments/`, and live backend modules. Only simulate when no real data is available. When simulating, model the actual system behavior (e.g., memoization in recursion).

