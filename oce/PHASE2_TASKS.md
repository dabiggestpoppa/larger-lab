# OCE Phase 2 — Event Fabric

> **Generated:** 2026-05-16
> **Lead:** CC (Claude Code)
> **Status:** Active
> **Depends on:** OCE Phase 1 (Continuity Shell) — nearly complete

---

## What Is the Event Fabric?

The Event Fabric is the **real-time event streaming backbone** that connects OCE's Continuity Core to the SRRA-OPH Observer Runtime. It:

1. **Ingests** events from SRRA-OPH substrate (observer state changes, attractor updates, entropy signals, repair triggers)
2. **Routes** events through the topology (which observers need to know what)
3. **Persists** events to trajectory memory (for reconstruction and continuity)
4. **Streams** events to the frontend via WebSocket (live dashboard updates)

Without the Event Fabric, OCE is a static API. With it, OCE becomes a **living system** that reacts in real-time.

---

## Architecture

```
SRRA-OPH Substrate
  │
  │ emits events (observer state, attractor, entropy, repair)
  ▼
Event Fabric (oce/backend/event_fabric.py)
  │
  ├── Event Ingestion  → Validate, timestamp, classify
  ├── Event Router     → Route to subscribers via topology
  ├── Event Persistence → Store in trajectory memory
  └── Event Stream     → WebSocket broadcast to frontend
  │
  ▼
OCE Continuity Core (main.py)
  │
  ├── /events endpoint    → Query event history
  ├── /ws/events          → Real-time event stream
  └── Frontend dashboard  → Live event feed
```

---

## Phase 2 Tasks by Agent

### 🔵 CC (Claude Code) — Core Event Fabric

**Responsibilities:** Design and implement the core Event Fabric engine.

#### Tasks

- [ ] **OCE-2.0** Design Event Fabric architecture
  - Event schema (type, timestamp, source, payload, priority)
  - Ingestion pipeline (validate → classify → timestamp)
  - Routing table (which subscribers get which events)
  - Persistence layer (write to trajectory memory)
  - Stream layer (WebSocket broadcast)

- [ ] **OCE-2.1** Implement `oce/backend/event_fabric.py`
  - `EventFabric` class with:
    - `ingest(event)` — Accept and process new events
    - `subscribe(event_type, callback)` — Register subscribers
    - `route(event)` — Route to matching subscribers
    - `persist(event)` — Store in trajectory memory
    - `get_history(event_type, limit)` — Query past events
    - `get_stream()` — Return async generator for WebSocket
  - Event schema (Pydantic model):
    ```python
    class Event(BaseModel):
        event_id: str
        event_type: str  # observer.state_change, attractor.update, entropy.signal, repair.trigger
        timestamp: datetime
        source: str      # which observer/subsystem emitted it
        priority: int    # 0=low, 1=normal, 2=high, 3=critical
        payload: Dict[str, Any]
    ```

- [ ] **OCE-2.2** Implement event ingestion from SRRA-OPH
  - Connect to `srrs_adapter.py` event emission
  - Subscribe to observer state changes from `CollarTopologyEngine`
  - Subscribe to attractor updates from `AttractorReasoningEngine`
  - Subscribe to entropy signals from `EntropyBudgetManager`
  - Subscribe to repair triggers from `RepairPatch`

- [ ] **OCE-2.3** Implement event routing via topology
  - Use `TopologicalRouter` (Phase 3) for intelligent routing
  - Route events to subscribers based on event type and topology proximity
  - Support broadcast (all subscribers) and targeted (specific observer) routing

- [ ] **OCE-2.4** Implement event persistence
  - Store events in trajectory memory via `TrajectoryReconstructionField`
  - Configurable retention (default: last 1000 events per type)
  - Compression for old events via `AdaptiveCompressionEngine`

- [ ] **OCE-2.5** Update `main.py` endpoints
  - `/events` → Query event history from Event Fabric
  - `/ws/events` → Stream events from Event Fabric (not just entropy metrics)
  - `/events/types` → List active event types
  - `/events/stats` → Event throughput statistics

- [ ] **OCE-2.6** Write tests
  - `oce/backend/tests/test_event_fabric.py`
  - Test ingestion, routing, persistence, streaming
  - Test SRRA-OPH event source integration

---

### 🟣 OC (OpenClaw) — Event Schema & Coordination

**Responsibilities:** Design event types, schemas, and coordinate with CC on API contracts.

#### Tasks

- [ ] **OCE-2.7** Design event type taxonomy
  - Define all event types emitted by SRRA-OPH subsystems
  - Categorize: observer.*, attractor.*, entropy.*, repair.*, system.*
  - Document payload schema for each type
  - File: `oce/docs/event-types.md`

- [ ] **OCE-2.8** Design event subscription protocol
  - How frontend subscribes to specific event types
  - How observers register for event routing
  - Filter patterns (wildcard, regex, exact match)
  - File: `oce/docs/event-protocol.md`

- [ ] **OCE-2.9** Review Event Fabric architecture
  - Review CC's `event_fabric.py` design
  - Verify alignment with SRRA-OPH patterns
  - Check integration with existing adapter
  - Post review to team-chat

- [ ] **OCE-2.10** Coordinate Phase 3 planning
  - Plan Observer Runtime integration with Event Fabric
  - Design observer lifecycle events (create, activate, suspend, destroy)
  - File: `oce/docs/observer-runtime-events.md`

---

### 🟠 OC2 (OpenClaw 2) — Frontend Event UI

**Responsibilities:** Implement the live event stream UI in the Next.js frontend.

#### Tasks

- [ ] **OCE-2.11** Implement event stream component
  - `oce/frontend/app/components/EventStream.tsx`
  - Real-time event feed from WebSocket
  - Color-coded by event type and priority
  - Auto-scroll with pause/resume
  - Filter by event type

- [ ] **OCE-2.12** Implement event detail panel
  - `oce/frontend/app/components/EventDetail.tsx`
  - Click an event → see full payload
  - JSON viewer with syntax highlighting
  - Link to related events

- [ ] **OCE-2.13** Implement event statistics dashboard
  - `oce/frontend/app/components/EventStats.tsx`
  - Events per second (throughput)
  - Event type distribution (pie chart)
  - Source activity (bar chart)
  - Use recharts or similar

- [ ] **OCE-2.14** Update main page to include event UI
  - Add EventStream component to `page.tsx`
  - Add EventStats to dashboard grid
  - Connect to `/ws/events` WebSocket

- [ ] **OCE-2.15** Test frontend with live backend
  - Start backend: `cd oce/backend && uvicorn main:app --reload`
  - Start frontend: `cd oce/frontend && npm run dev`
  - Verify events flow from SRRA-OPH → backend → frontend

---

### 🟡 AS (Assistant Manager) — Quality & Integration Docs

**Responsibilities:** Quality review, integration documentation, resource assessment.

#### Tasks

- [ ] **OCE-2.16** Quality review of Event Fabric
  - Review `event_fabric.py` when CC completes OCE-2.1
  - Check error handling, edge cases, performance
  - File: `oce/docs/quality-review-phase2.md`

- [ ] **OCE-2.17** Document Event Fabric API
  - Update `oce/docs/api-reference.md` with new endpoints
  - Document WebSocket event protocol
  - Document event type taxonomy (with OC)

- [ ] **OCE-2.18** Phase 6-9 resource assessment for Event Fabric
  - What external resources does Phase 2 need?
  - Redis Streams vs in-memory (decide for Phase 2)
  - Event store options (SQLite, PostgreSQL, EventStoreDB)
  - File: `oce/docs/phase2-resources.md`

- [ ] **OCE-2.19** Integration testing
  - End-to-end test: SRRA-OPH emits event → Event Fabric → WebSocket → Frontend
  - Performance test: 1000 events/second throughput
  - File: `oce/backend/tests/test_phase2_e2e.py`

---

### 🔴 PM (Polymorph) — Operator Integration & Debugging

**Responsibilities:** Integrate Operator tools with Event Fabric, debug issues.

#### Tasks

- [x] **OCE-2.20** Integrate System Operator with Event Fabric ✅
  - `tools/operator/event-integration.js` — Bridge layer with emit functions
  - Events: `operator.command.executed`, `operator.process.killed`, `operator.package.installed`

- [x] **OCE-2.21** Integrate VS Code Controller with Event Fabric ✅
  - `tools/operator/vscode-controller.js` — Full VS Code CLI control
  - Events: `operator.vscode.file_opened`, `operator.vscode.file_edited`, `operator.vscode.command`, `operator.vscode.git_commit`

- [x] **OCE-2.22** Build Event Fabric debugging utilities ✅
  - `tools/operator/event-debug.js` — CLI (tail, stats, replay, health, emit, types)

- [x] **OCE-2.23** Debug OCE-SRRA integration issues ✅
  - `oce/docs/integration-issues.md` — 7 issues identified, test checklist created

---

### 🦉 RL (OWL) — DSPy Pipeline Optimization

**Responsibilities:** Research and implement DSPy pipelines for event processing.

#### Tasks

- [ ] **OCE-2.24** Design DSPy event classification pipeline
  - Auto-classify incoming events by type and priority
  - Use DSPy to learn from operator feedback
  - File: `oce/backend/dspy_event_classifier.py`

- [ ] **OCE-2.25** Design DSPy event routing optimization
  - Learn optimal routing patterns from event flow
  - Reduce unnecessary event propagation
  - File: `oce/backend/dspy_event_router.py`

- [ ] **OCE-2.26** Research event sourcing patterns
  - Research: Event sourcing vs CQRS for OCE
  - How to reconstruct observer state from event log
  - File: `oce/docs/event-sourcing-research.md`

- [ ] **OCE-2.27** Implement event compression via DSPy
  - Use DSPy to summarize old event batches
  - Reduce storage while preserving reconstructability
  - Integrate with `AdaptiveCompressionEngine`

---

## Phase 2 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Event Fabric engine | CC | `oce/backend/event_fabric.py` | Pending |
| Event ingestion (SRRA-OPH) | CC | `oce/backend/event_fabric.py` | Pending |
| Event routing (topology) | CC | `oce/backend/event_fabric.py` | Pending |
| Event persistence | CC | `oce/backend/event_fabric.py` | Pending |
| Updated API endpoints | CC | `oce/backend/main.py` | Pending |
| Event type taxonomy | OC | `oce/docs/event-types.md` | Pending |
| Event protocol | OC | `oce/docs/event-protocol.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Event stream UI | OC2 | `oce/frontend/app/components/EventStream.tsx` | Pending |
| Event detail panel | OC2 | `oce/frontend/app/components/EventDetail.tsx` | Pending |
| Event stats dashboard | OC2 | `oce/frontend/app/components/EventStats.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase2.md` | Pending |
| API docs update | AS | `oce/docs/api-reference.md` | Pending |
| Resource assessment | AS | `oce/docs/phase2-resources.md` | Pending |
| Operator integration | PM | `tools/operator/event-integration.js` | ✅ |
| Debugging utilities | PM | `tools/operator/event-debug.js` | ✅ |
| DSPy classification | RL | `oce/backend/dspy_event_classifier.py` | Pending |
| DSPy routing | RL | `oce/backend/dspy_event_router.py` | Pending |

---

## Execution Order

1. **CC:** OCE-2.0 (design) → OCE-2.1 (core engine) — BLOCKS everything else
2. **OC:** OCE-2.7 (event types) — can start immediately, no dependencies
3. **CC:** OCE-2.2-2.6 (ingestion, routing, persistence, endpoints, tests) — after OCE-2.1
4. **OC2:** OCE-2.11-2.15 (frontend) — after CC completes OCE-2.5
5. **AS:** OCE-2.16-2.19 (quality, docs, testing) — after CC completes core
6. **PM:** OCE-2.20-2.23 (operator integration, debugging) — after CC completes core
7. **RL:** OCE-2.24-2.27 (DSPy, research) — can start after OC defines event types

---

## Success Criteria

1. Events flow from SRRA-OPH substrate → Event Fabric → WebSocket → Frontend
2. Event throughput: 1000+ events/second
3. Event persistence: configurable retention, compression
4. Event routing: topology-aware, supports broadcast and targeted
5. Frontend: live event stream with filtering and detail view
6. All endpoints tested and documented
