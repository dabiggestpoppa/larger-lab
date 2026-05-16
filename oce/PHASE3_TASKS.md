# OCE Phase 3 — Observer Runtime

> **Generated:** 2026-05-16
> **Lead:** CC (Claude Code)
> **Status:** Active — CC building core, all agents assigned
> **Depends on:** OCE Phase 2 (Event Fabric) — core complete

---

## What Is the Observer Runtime?

The Observer Runtime is the **execution layer** that brings SRRA-OPH observers to life within OCE. It:

1. **Manages observer lifecycle** — create, activate, suspend, destroy observers
2. **Routes events to observers** — via the Event Fabric's topology-aware routing
3. **Monitors observer health** — entropy tracking, drift detection, repair triggers
4. **Persists observer state** — reconstruction from sparse anchors
5. **Provides observer API** — for frontend and external tools to query/control observers

Without the Observer Runtime, events flow through the fabric but nothing acts on it. With it, OCE becomes an **autonomous cognitive system**.

---

## Architecture

```
Event Fabric (Phase 2)
  │
  │ events routed by topology
  ▼
Observer Runtime (Phase 3)
  │
  ├── Observer Lifecycle Manager — create/activate/suspend/destroy
  ├── Observer State Tracker — entropy, drift, health
  ├── Observer Repair Engine — trigger repair on failure
  └── Observer API — query/control via REST + WebSocket
  │
  ▼
SRRA-OPH Substrate (srrs_opc/)
  │
  ├── BasePatch, PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch
  ├── CollarLayer, AgentBridge
  ├── CollarTopologyEngine, TopologyObserver
  └── DriftDetector, ReinforcementEngine
```

---

## Phase 3 Tasks by Agent

### 🔵 CC (Claude Code) — Core Observer Runtime

**Responsibilities:** Design and implement the Observer Runtime engine.

#### Tasks

- [ ] **OCE-3.0** Design Observer Runtime architecture
  - Observer lifecycle state machine (created → active → suspended → destroyed)
  - Event subscription model (observers subscribe to event types)
  - Health monitoring integration (entropy, drift, repair)
  - State persistence model (reconstruction from anchors)

- [ ] **OCE-3.1** Implement `oce/backend/observer_runtime.py`
  - `ObserverRuntime` class with:
    - `create_observer(config)` — Register new observer
    - `activate_observer(observer_id)` — Start processing events
    - `suspend_observer(observer_id)` — Pause processing
    - `destroy_observer(observer_id)` — Remove observer
    - `get_observer_status(observer_id)` — Health + state
    - `list_observers()` — All observers
    - `subscribe_observer(observer_id, event_types)` — Event subscription
  - Integrates with Event Fabric for event routing
  - Integrates with SRRA-OPH for observer state

- [ ] **OCE-3.2** Implement observer health monitoring
  - Connect to `CollarTopologyEngine` for entropy metrics
  - Connect to `DriftDetector` for drift signals
  - Connect to `EntropyBudgetManager` for budget tracking
  - Health endpoint: `/observers/{id}/health`

- [ ] **OCE-3.3** Implement observer state persistence
  - Use `TrajectoryReconstructionField` for state snapshots
  - Use `RecoveryAnchors` for sparse persistence
  - Configurable snapshot interval
  - Reconstruction from event log

- [ ] **OCE-3.4** Update `main.py` endpoints
  - `POST /observers` — Create observer
  - `GET /observers` — List all observers
  - `GET /observers/{id}` — Observer details
  - `GET /observers/{id}/health` — Health metrics
  - `POST /observers/{id}/activate` — Activate
  - `POST /observers/{id}/suspend` — Suspend
  - `DELETE /observers/{id}` — Destroy
  - `POST /observers/{id}/subscribe` — Subscribe to events
  - `WS /ws/observers` — Real-time observer updates

- [ ] **OCE-3.5** Write tests
  - `oce/backend/tests/test_observer_runtime.py`
  - Test lifecycle, health, persistence, API endpoints

---

### 🟣 OC (OpenClaw) — Observer Schema & Coordination

**Responsibilities:** Design observer types, schemas, and coordinate with CC.

#### Tasks

- [ ] **OCE-3.6** Design observer type taxonomy
  - Define observer types: trading, repair, entropy, content, system
  - Define observer capabilities per type
  - Define observer configuration schema
  - File: `oce/docs/observer-types.md`

- [ ] **OCE-3.7** Design observer-event binding protocol
  - How observers subscribe to event types
  - How events trigger observer actions
  - How observer outputs become new events
  - File: `oce/docs/observer-event-protocol.md`

- [ ] **OCE-3.8** Review Observer Runtime architecture
  - Review CC's `observer_runtime.py` design
  - Verify alignment with SRRA-OPH observer patterns
  - Post review to team-chat

---

### 🟠 OC2 (OpenClaw 2) — Frontend Observer UI

**Responsibilities:** Implement the observer management UI.

#### Tasks

- [ ] **OCE-3.9** Implement observer list component
  - `oce/frontend/app/components/ObserverList.tsx`
  - Table of all observers with status, type, health
  - Filter by type and status
  - Sort by health/entropy

- [ ] **OCE-3.10** Implement observer detail panel
  - `oce/frontend/app/components/ObserverDetail.tsx`
  - Full observer info: config, state, health metrics
  - Event subscription management
  - Activate/suspend/destroy controls

- [ ] **OCE-3.11** Implement observer health dashboard
  - `oce/frontend/app/components/ObserverHealth.tsx`
  - Entropy chart over time
  - Drift signal visualization
  - Budget usage gauge

- [ ] **OCE-3.12** Update main page
  - Add ObserverList to dashboard
  - Add ObserverHealth to dashboard grid
  - Connect to `/ws/observers` WebSocket

---

### 🟡 AS (Assistant Manager) — Quality & Integration

**Responsibilities:** Quality review, documentation, integration testing.

#### Tasks

- [ ] **OCE-3.13** Quality review of Observer Runtime
  - Review `observer_runtime.py`
  - Check lifecycle, health monitoring, persistence
  - File: `oce/docs/quality-review-phase3.md`

- [ ] **OCE-3.14** Document Observer Runtime API
  - Update `oce/docs/api-reference.md`
  - Document WebSocket observer protocol

- [ ] **OCE-3.15** Integration testing
  - End-to-end: create observer → emit event → observer processes → state persists
  - File: `oce/backend/tests/test_phase3_e2e.py`

---

### 🔴 PM (Polymorph) — Operator Integration

**Responsibilities:** Integrate Operator tools with Observer Runtime.

#### Tasks

- [ ] **OCE-3.16** Integrate Operator with Observer Runtime
  - System commands → observer actions
  - Operator events → observer triggers
  - File: `tools/operator/observer-integration.js`

- [ ] **OCE-3.17** Build observer debugging utilities
  - `tools/operator/observer-debug.js` — CLI for inspecting observers
  - Commands: list, status, health, events, logs

- [ ] **OCE-3.18** Update integration issues
  - Update `oce/docs/integration-issues.md`
  - Close resolved issues, add new ones

---

### 🦉 RL (OWL) — DSPy Observer Optimization

**Responsibilities:** DSPy pipelines for observer intelligence.

#### Tasks

- [ ] **OCE-3.19** Design DSPy observer behavior pipeline
  - Auto-configure observer parameters from event patterns
  - Learn optimal observer activation schedules
  - File: `oce/backend/dspy_observer_config.py`

- [ ] **OCE-3.20** Design DSPy observer repair pipeline
  - Auto-diagnose observer failures
  - Suggest repair actions
  - File: `oce/backend/dspy_observer_repair.py`

- [ ] **OCE-3.21** Research observer patterns
  - Research: autonomous agent architectures
  - How OCE observers compare to LangGraph, CrewAI, AutoGen
  - File: `oce/docs/observer-research.md`

---

## Phase 3 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Observer Runtime engine | CC | `oce/backend/observer_runtime.py` | Pending |
| Health monitoring | CC | `oce/backend/observer_runtime.py` | Pending |
| State persistence | CC | `oce/backend/observer_runtime.py` | Pending |
| API endpoints | CC | `oce/backend/main.py` | Pending |
| Tests | CC | `oce/backend/tests/test_observer_runtime.py` | Pending |
| Observer type taxonomy | OC | `oce/docs/observer-types.md` | Pending |
| Observer-event protocol | OC | `oce/docs/observer-event-protocol.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Observer list UI | OC2 | `ObserverList.tsx` | Pending |
| Observer detail UI | OC2 | `ObserverDetail.tsx` | Pending |
| Observer health UI | OC2 | `ObserverHealth.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase3.md` | Pending |
| API docs | AS | `oce/docs/api-reference.md` | Pending |
| Integration testing | AS | `oce/backend/tests/test_phase3_e2e.py` | Pending |
| Operator integration | PM | `tools/operator/observer-integration.js` | Pending |
| Debug utilities | PM | `tools/operator/observer-debug.js` | Pending |
| DSPy observer config | RL | `oce/backend/dspy_observer_config.py` | Pending |
| DSPy observer repair | RL | `oce/backend/dspy_observer_repair.py` | Pending |

---

## Success Criteria

1. Observers can be created, activated, suspended, destroyed via API
2. Events from Event Fabric are routed to subscribed observers
3. Observer health is monitored (entropy, drift, budget)
4. Observer state persists and can be reconstructed
5. Frontend shows observer list, detail, and health dashboard
6. Operator tools integrate with observer lifecycle
7. All endpoints tested and documented
