# OCE Phase 6 — Execution Substrate

> **Generated:** 2026-05-17
> **Lead:** OWL (RL) — Phase 6 Lead
> **Status:** Active
> **Depends on:** OCE Phase 5 (Observability) — ✅ Complete (178 tests passing)

---

## What Is the Execution Substrate?

The Execution Substrate is the **task execution layer** that makes OCE actually *do things*. It:

1. **Executes tasks** — async job queue with priority scheduling and worker pool
2. **Invokes skills/tools** — agents call tools through OCE, not directly
3. **Enforces policies** — rate limits, permissions, sandboxing, concurrency limits
4. **Persists results** — SQLite-backed execution history for audit and replay
5. **Supports replay** — any executed task can be replayed with the same parameters
6. **Traces execution** — integrates with Phase 5 TracingEngine for full observability

Without the Execution Substrate, OCE is a passive observer. With it, OCE becomes an **active cognitive system** that can execute, trace, and replay any operator action.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Execution Substrate (Phase 6)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Execution   │  │   Execution  │  │    Execution History     │  │
│  │   Engine      │  │   Policies   │  │    (SQLite)              │  │
│  │              │  │              │  │                          │  │
│  │ • Job Queue  │  │ • Rate Limits│  │ • Task records           │  │
│  │ • Workers    │  │ • Permissions│  │ • Results & errors       │  │
│  │ • Handlers   │  │ • Sandboxing │  │ • Replay support         │  │
│  │ • Retry/TO   │  │ • Concurrency│  │ • Stats & analytics      │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘  │
│         │                                                           │
│  ┌──────▼────────────────────────────────────────────────────────┐  │
│  │                    Execution API                              │  │
│  │  POST /execution/submit  POST /execution/{id}/cancel         │  │
│  │  GET  /execution/tasks   GET  /execution/tasks/{id}          │  │
│  │  GET  /execution/history POST /execution/{id}/replay         │  │
│  │  GET  /execution/stats   GET  /execution/workers             │  │
│  │  POST /execution/policies  GET  /execution/policies          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Task Type Handlers                               │  │
│  │  skill_call → invoke named skill with parameters             │  │
│  │  tool_invoke → call external tool/API                         │  │
│  │  pipeline_run → execute DSPy pipeline                         │  │
│  │  agent_delegate → delegate to sub-agent                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Task Assignments

### 🦉 RL (OWL) — Core Execution Engine
- **OCE-6.1**: `oce/backend/execution_engine.py` — ExecutionEngine class ✅
- **OCE-6.2**: `oce/backend/execution_api.py` — API endpoints ✅
- **OCE-6.3**: `oce/backend/tests/test_execution_engine.py` — 47 tests ✅
- **OCE-6.4**: Integrate into main.py ✅
- **OCE-6.5**: Create PHASE6_TASKS.md ✅

### 🟣 OC (OpenClaw) — Docs + Review
- **OCE-6.6**: `oce/docs/execution-substrate.md` — Architecture doc
- **OCE-6.7**: Review execution engine design
- **OCE-6.8**: Update event-types.md with execution events

### 🟠 OC2 (OpenClaw 2) — Dashboard Integration
- **OCE-6.9**: `ExecutionPanel.tsx` — Real-time execution monitor
- **OCE-6.10**: `TaskDetail.tsx` — Task detail view with replay button
- **OCE-6.11**: Integrate into observability dashboard

### 🟡 AS (Assistant Manager) — Quality + Integration
- **OCE-6.12**: Quality review of execution engine
- **OCE-6.13**: API documentation update
- **OCE-6.14**: Integration tests (`test_phase6_e2e.py`)

### 🔴 PM (Polymorph) — Operator Tools
- **OCE-6.15**: `tools/operator/execution-cli.py` — CLI for task management
- **OCE-6.16**: `tools/operator/execution-debug.py` — Debug execution issues

---

## Success Criteria
- Task submission, execution, cancellation all working
- Worker pool processes tasks concurrently
- Policy enforcement (rate limits, permissions) functional
- Execution history persisted to SQLite
- Task replay working
- ≥ 45 new tests, total OCE ≥ 223
- All existing 178 tests still passing

---

## Key Design Decisions
- Singleton pattern (consistent with all existing engines)
- Priority queue with counter tiebreaker (avoids comparing task objects)
- SQLite for history persistence (consistent)
- Graceful degradation (errors logged, never crash the API)
- All execution is traced and observable (Phase 5 integration)
- Extensible handler system (register custom task types)
- Policy-based enforcement (rate limits, permissions, sandboxing)
