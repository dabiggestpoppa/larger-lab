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
