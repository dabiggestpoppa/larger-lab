# 🎨 FRONTEND BUILD PLAN — SRRA-OPH + OCE
> **Created:** 2026-05-24 | **Phase:** Frontend Build Planning
> **Scope:** Two separate frontends serving different purposes

---

## ARCHITECTURE CLARIFICATION

**Two separate frontends, two different purposes:**

| Frontend | Port | Purpose | User |
|----------|------|---------|------|
| **SRRA-OPH** | 3001 | System introspection — observer mesh, topology, field state, entropy, repair visualization. The "continuity observatory." | System operators, developers |
| **OCE** | 3000 | User-facing operational interface — controls, task management, agent coordination, workflow cockpit. The "operational cockpit." | End users, operators |

**They are NOT the same system.** They share the SRRA/OPH runtime backend but serve different audiences and use cases.

---

## EXISTING STATE

### SRRA-OPH Frontend (:3001) — Next.js 15 + React 19
- ✅ Basic shell with sidebar layout
- ✅ Phase bars, modules page, events page, topology page
- ✅ Skeleton loaders, ErrorBanner, polling
- ❌ No Cytoscape/D3 graph rendering
- ❌ No entropy/repair/temporal visualization
- ❌ No dark scientific theme (still light/default)
- ❌ No WebSocket real-time data

### OCE Frontend (:3000) — Next.js 15 + React 19
- ✅ Basic shell layout
- ✅ QuickStat cards, nav routing
- ✅ WebSocket with exponential backoff
- ❌ No operational control panels
- ❌ No task management UI
- ❌ No agent coordination interface
- ❌ No chaos test monitoring

---

## AGENT ASSIGNMENTS

### 🔵 CC2 — SRRA-OPH Frontend: Topology Observatory Engine (Phases 1-2)
**File:** `tasks/frontend-cc2-srra-plan.md`

**Scope:** Transform the SRRA-OPH frontend into a scientific continuity observatory.

**Phase 1 — Observatory Foundation:**
1. Dark scientific theme (deep matte black, low-glow, IBM Plex Mono)
2. Four-region layout: Left Rail | Main Canvas | Bottom Timeline | Right Context Panel
3. Zustand state management (topologyStore, playbackStore, entropyStore, observerStore)
4. Routing: /topology, /entropy, /repair, /attractors, /experiments, /playback
5. Mock data generation (500 nodes, 2000 edges)
6. Cytoscape.js integration with pan/zoom/select
7. Timeline controller (play, pause, scrub, speed)
8. WebSocket infrastructure for live data

**Phase 2 — Living Topology:**
1. Observer state engine (ACTIVE, SYNCED, ISOLATED, ENTROPIC, REPAIRING, DORMANT, FAILED)
2. Edge dynamics (directional flow, routing, repair propagation, entropy spread)
3. Spatial layout engine (force-directed, cluster-aware, entropy-reactive)
4. Clustering engine (synchronization groups, stability scores)
5. Entropy overlay (heat layer, perturbation spread)
6. Repair propagation visualization (coherence restoration waves)
7. Filtering + inspection system
8. Performance: 10k+ nodes, 30fps minimum

**Dependencies:** None (can start immediately)
**Estimated:** Large build, 2-3 sessions

---

### 🟠 PM2 — SRRA-OPH Frontend: Temporal + Field Dynamics (Phases 3-4)
**File:** `tasks/frontend-pm2-srra-plan.md`

**Scope:** Add temporal playback and entropy field dynamics to SRRA-OPH.

**Phase 3 — Temporal Playback Engine:**
1. Timeline core engine (master temporal controller, frame indexing)
2. Playback controls (play, pause, reverse, frame step, speed scale 0.25x-10x)
3. Frame state engine (complete continuity snapshots per frame)
4. Multi-view temporal synchronization (topology + entropy + repair + metrics locked)
5. Event sequencing (PERTURBATION, REPAIR_TRIGGER, SYNC_COLLAPSE, etc.)
6. Frame interpolation (smooth node movement, entropy gradients)
7. Long-horizon storage (temporal chunking, compression, 24-72hr replay)
8. Temporal scrubber with event markers
9. Experiment replay engine (load, replay, side-by-side comparison)

**Phase 4 — Entropy + Perturbation Field:**
1. Entropy core engine (observer/cluster/global entropy metrics)
2. Perturbation injection system (NODE_FAILURE, SYNC_BREAK, ROUTING_CORRUPTION, etc.)
3. Propagation dynamics (shockwaves, stress gradients, collapse regions)
4. Stability gradient system (high stability zones, fragility zones, drift regions)
5. Pressure field renderer (thermal/vector/gradient modes)
6. Resonance collapse detection (predictive, before total failure)
7. Repair ↔ entropy interaction visualization
8. Multi-scale field (observer → cluster → region → global)
9. Entropy timeline integration

**Dependencies:** CC2 must complete Phase 1 (layout, theme, state) before PM2 starts Phase 3
**Estimated:** Large build, 2-3 sessions

---

### 🟢 AS — OCE Frontend: Operational Cockpit Build
**File:** `tasks/frontend-as-oce-plan.md`

**Scope:** Transform OCE frontend into the user-facing operational cockpit.

**Phase 1 — Cockpit Foundation:**
1. Clean operational theme (not scientific dark — functional, clean, low-fatigue)
2. Layout: Top nav | Main content area | Right context panel | Bottom status bar
3. Zustand stores (taskStore, agentStore, sessionStore, uiStore)
4. Routing: /dashboard, /tasks, /agents, /chaos, /settings
5. WebSocket connection to OCE backend (:8000)
6. Real-time status indicators

**Phase 2 — Task + Agent Management:**
1. Task queue view (active, pending, completed, failed)
2. Agent status cards (health, current task, uptime, errors)
3. Task creation/delegation interface
4. Agent communication log
5. Progress tracking with live updates

**Phase 3 — Chaos Test Monitoring:**
1. Live chaos test dashboard (amplification factor, cycle progress, pass/fail)
2. Chaos event timeline
3. Recovery time charts
4. Scenario breakdown (observer_death, event_flood, memory_poison, full_chaos)
5. Historical chaos test results

**Phase 4 — Semantic Test Results (Phase 11.4.1+11.4.2):**
1. Contradiction injection test results viewer
2. Metrics dashboard (SDI, RIS, OCS, APS, FAR, RVA, SIS, TVT)
3. Semantic conflict timeline visualization
4. Observer consensus report
5. Reconstruction report

**Dependencies:** None (can start immediately, independent from SRRA-OPH work)
**Estimated:** Medium-large build, 2 sessions

---

### 🔴 CC — SRRA-OPH Frontend: Repair + Consensus + Prediction (Phases 5-7)
**File:** `tasks/frontend-cc-srra-plan.md`

**Scope:** Complete the SRRA-OPH observatory with repair, consensus, and prediction layers.

**Phase 5 — Repair + Self-Stabilization:**
1. Repair core engine visualization (autonomous repair detection/coordination)
2. Repair wave rendering (coherence restoration across topology)
3. Continuity monitoring dashboard (drift scanning, coherence tracking)
4. Recovery sequencing visualization
5. Saturation detection (repair overload indicators)
6. Cascade prevention visualization
7. Reintegration tracking

**Phase 6 — Distributed Observer Consensus:**
1. Consensus visualization (observer agreement maps)
2. Signaling overlays (observer communication patterns)
3. Trust metrics per observer
4. Synchronization agreement maps
5. Coordination playback
6. Distributed awareness panels

**Phase 7 — Field Cognition + Predictive:**
1. Attractor basin visualization (recurring stable operational states)
2. Future-state overlays (predicted trajectories)
3. Collapse forecasting indicators
4. Repair strategy comparison panels
5. Multi-future branching visualization

**Dependencies:** PM2 must complete Phases 3-4 before CC starts Phase 5
**Estimated:** Large build, 2-3 sessions

---

## EXECUTION ORDER

```
SESSION 1 (NOW):
  ├── CC2: SRRA-OPH Phase 1 (Observatory Foundation)
  ├── AS:  OCE Phase 1 (Cockpit Foundation)  
  └── AS:  OCE Phase 2 (Task + Agent Management)

SESSION 2:
  ├── CC2: SRRA-OPH Phase 2 (Living Topology)
  ├── PM2: SRRA-OPH Phase 3 (Temporal Playback) [starts after CC2 Phase 1 done]
  ├── AS:  OCE Phase 3 (Chaos Test Monitoring)
  └── AS:  OCE Phase 4 (Semantic Test Results)

SESSION 3:
  ├── PM2: SRRA-OPH Phase 4 (Entropy Field Dynamics)
  ├── CC:  SRRA-OPH Phase 5 (Repair + Stabilization)
  └── CC:  SRRA-OPH Phase 6 (Distributed Consensus)

SESSION 4:
  └── CC:  SRRA-OPH Phase 7 (Predictive Modeling)
```

---

## KEY TECHNICAL DECISIONS

1. **Both frontends stay Next.js** — no Vite migration, build on existing shells
2. **SRRA-OPH gets Cytoscape.js + D3** — for topology/entropy/repair visualization
3. **OCE gets Recharts + custom components** — for operational dashboards and metrics
4. **Zustand for state management** — in both frontends
5. **WebSocket for real-time** — both frontends connect to respective backends
6. **Dark scientific theme for SRRA-OPH** — Edward Tufte + scientific instrumentation
7. **Clean operational theme for OCE** — functional, not decorative
8. **Mock data first** — all visualization built with mock data, then connected to real backend APIs

---

## FILES TO CREATE PER AGENT

See individual plan files for detailed file breakdowns.
