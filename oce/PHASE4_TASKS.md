# OCE Phase 4 — Structural Memory

> **Generated:** 2026-05-16
> **Lead:** CC (Claude Code) — handing off to OC2
> **Status:** Planning
> **Depends on:** OCE Phase 3 (Observer Runtime) — core complete

---

## What Is Structural Memory?

Structural Memory is the **long-term memory layer** that gives OCE continuity across sessions. It:

1. **Stores observer state** — trajectory fragments, topology snapshots, repair history
2. **Compresses old data** — adaptive compression preserves recoverability
3. **Reconstructs state** — rebuild observer state from sparse anchors + event log
4. **Provides memory API** — query, search, and replay historical state
5. **Integrates with SRRA-OPH** — uses TrajectoryReconstructionField, StructuralMemoryFields, RecoveryAnchors

Without Structural Memory, OCE forgets everything when it restarts. With it, OCE has **persistent identity**.

---

## Architecture

```
Observer Runtime (Phase 3)
  │
  │ state snapshots, events
  ▼
Structural Memory (Phase 4)
  │
  ├── Trajectory Store — observer trajectories over time
  ├── Topology Graph — collar topology snapshots
  ├── Repair History — repair triggers, actions, outcomes
  ├── Compression Engine — adaptive compression of old data
  └── Reconstruction Engine — rebuild state from anchors + events
  │
  ▼
SRRA-OPH Substrate
  ├── TrajectoryReconstructionField
  ├── StructuralMemoryFields
  ├── RecoveryAnchors
  └── AdaptiveCompressionEngine
```

---

## Phase 4 Tasks by Agent

### 🔵 CC (Claude Code) — Core Structural Memory

**Responsibilities:** Design and implement the Structural Memory engine.

#### Tasks

- [ ] **OCE-4.0** Design Structural Memory architecture
  - Memory layers: trajectory, topology, repair, attractor, event, context
  - Compression strategy: adaptive, preserves recoverability
  - Reconstruction protocol: anchors + events → full state

- [ ] **OCE-4.1** Implement `oce/backend/structural_memory.py`
  - `StructuralMemory` class with:
    - `store_snapshot(observer_id, snapshot)` — Store observer state
    - `get_snapshot(observer_id, timestamp)` — Retrieve state at time
    - `compress(observer_id, max_age)` — Compress old data
    - `reconstruct(observer_id, timestamp)` — Rebuild state from anchors
    - `search(query)` — Search across memory layers
    - `get_timeline(observer_id)` — Full timeline for observer

- [ ] **OCE-4.2** Implement trajectory store
  - Use `TrajectoryReconstructionField` for trajectory fragments
  - Configurable retention per observer
  - Time-range queries

- [ ] **OCE-4.3** Implement topology graph
  - Use `CollarTopologyEngine` for topology snapshots
  - Store topology deltas (not full snapshots)
  - Reconstruct topology at any point in time

- [ ] **OCE-4.4** Implement compression engine
  - Integrate with `AdaptiveCompressionEngine`
  - Configurable compression ratio per memory layer
  - Preserve recoverability anchors

- [ ] **OCE-4.5** Update `main.py` endpoints
  - `GET /memory/observers/{id}/timeline` — Observer timeline
  - `GET /memory/observers/{id}/snapshot` — State at time
  - `POST /memory/observers/{id}/compress` — Trigger compression
  - `POST /memory/observers/{id}/reconstruct` — Rebuild state
  - `GET /memory/search` — Search across memory
  - `GET /memory/stats` — Memory usage statistics

- [ ] **OCE-4.6** Write tests
  - `oce/backend/tests/test_structural_memory.py`

---

### 🟣 OC (OpenClaw) — Memory Schema & Coordination

**Responsibilities:** Design memory schemas and coordinate with CC.

#### Tasks

- [ ] **OCE-4.7** Design memory layer taxonomy
  - Define layers: trajectory, topology, repair, attractor, event, context
  - Define schema per layer
  - Define retention policies per layer
  - File: `oce/docs/memory-layers.md`

- [ ] **OCE-4.8** Design reconstruction protocol
  - How to reconstruct observer state from sparse anchors
  - How to validate reconstruction accuracy
  - File: `oce/docs/reconstruction-protocol.md`

- [ ] **OCE-4.9** Review Structural Memory architecture
  - Review CC's `structural_memory.py` design
  - Verify alignment with SRRA-OPH memory patterns
  - Post review to team-chat

---

### 🟠 OC2 (OpenClaw 2) — Frontend Memory UI

**Responsibilities:** Implement the memory visualization UI.

#### Tasks

- [ ] **OCE-4.10** Implement memory timeline component
  - `oce/frontend/app/components/MemoryTimeline.tsx`
  - Visual timeline of observer state changes
  - Zoomable, filterable by event type

- [ ] **OCE-4.11** Implement memory search
  - `oce/frontend/app/components/MemorySearch.tsx`
  - Full-text search across memory layers
  - Results grouped by layer

- [ ] **OCE-4.12** Implement memory stats dashboard
  - `oce/frontend/app/components/MemoryStats.tsx`
  - Memory usage by layer
  - Compression ratios
  - Reconstruction accuracy metrics

- [ ] **OCE-4.13** Update main page
  - Add MemoryTimeline and MemoryStats to dashboard

---

### 🟡 AS (Assistant Manager) — Quality & Integration

**Responsibilities:** Quality review, documentation, integration testing.

#### Tasks

- [ ] **OCE-4.14** Quality review of Structural Memory
  - Review `structural_memory.py`
  - Check compression, reconstruction, search
  - File: `oce/docs/quality-review-phase4.md`

- [ ] **OCE-4.15** Document Memory API
  - Update `oce/docs/api-reference.md`
  - Document memory query language

- [ ] **OCE-4.16** Integration testing
  - End-to-end: store → compress → reconstruct → verify
  - File: `oce/backend/tests/test_phase4_e2e.py`

---

### 🔴 PM (Polymorph) — Operator Integration

**Responsibilities:** Integrate Operator tools with Structural Memory.

#### Tasks

- [ ] **OCE-4.17** Integrate Operator with Structural Memory
  - Operator actions stored in memory
  - Operator can query memory for context
  - File: `tools/operator/memory-integration.js`

- [ ] **OCE-4.18** Build memory debugging utilities
  - `tools/operator/memory-debug.js` — CLI for inspecting memory
  - Commands: timeline, snapshot, search, compress, reconstruct

---

### 🦉 RL (OWL) — DSPy Memory Optimization

**Responsibilities:** DSPy pipelines for memory intelligence.

#### Tasks

- [ ] **OCE-4.19** Design DSPy memory compression pipeline
  - Learn optimal compression strategies per observer type
  - File: `oce/backend/dspy_memory_compression.py`

- [ ] **OCE-4.20** Design DSPy reconstruction pipeline
  - Improve reconstruction accuracy with learned patterns
  - File: `oce/backend/dspy_memory_reconstruction.py`

- [ ] **OCE-4.21** Research memory architectures
  - Research: episodic memory, semantic memory, procedural memory
  - How OCE memory compares to human memory models
  - File: `oce/docs/memory-research.md`

---

## Phase 4 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Structural Memory engine | CC | `oce/backend/structural_memory.py` | Pending |
| Trajectory store | CC | `oce/backend/structural_memory.py` | Pending |
| Topology graph | CC | `oce/backend/structural_memory.py` | Pending |
| Compression engine | CC | `oce/backend/structural_memory.py` | Pending |
| API endpoints | CC | `oce/backend/main.py` | Pending |
| Tests | CC | `oce/backend/tests/test_structural_memory.py` | Pending |
| Memory layer taxonomy | OC | `oce/docs/memory-layers.md` | Pending |
| Reconstruction protocol | OC | `oce/docs/reconstruction-protocol.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Memory timeline UI | OC2 | `MemoryTimeline.tsx` | Pending |
| Memory search UI | OC2 | `MemorySearch.tsx` | Pending |
| Memory stats UI | OC2 | `MemoryStats.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase4.md` | Pending |
| API docs | AS | `oce/docs/api-reference.md` | Pending |
| Integration testing | AS | `oce/backend/tests/test_phase4_e2e.py` | Pending |
| Operator integration | PM | `tools/operator/memory-integration.js` | Pending |
| Debug utilities | PM | `tools/operator/memory-debug.js` | Pending |
| DSPy compression | RL | `oce/backend/dspy_memory_compression.py` | Pending |
| DSPy reconstruction | RL | `oce/backend/dspy_memory_reconstruction.py` | Pending |

---

## Success Criteria

1. Observer state can be stored, compressed, and reconstructed
2. Memory layers: trajectory, topology, repair, attractor, event, context
3. Compression preserves recoverability
4. Reconstruction accuracy > 90%
5. Frontend shows memory timeline, search, and stats
6. All endpoints tested and documented
