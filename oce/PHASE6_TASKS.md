# OCE Phase 6 — Execution Substrate

> **Generated:** 2026-05-17
> **Lead:** OWL (RL) — Phase 6 Lead
> **Status:** Planning → Active
> **Depends on:** OCE Phase 5 (Observability) — ✅ Complete (178 tests passing)

---

## What Is the Execution Substrate?

The Execution Substrate is the **task execution layer** that brings OCE from a passive event-processing system to an **active cognitive engine**. It:

1. **Manages a worker pool** — configurable concurrency for parallel task execution
2. **Processes task queues** — priority scheduling with rate limiting and backpressure
3. **Invokes skills and tools** — dispatches work to registered handlers (trading, repair, entropy, content, system)
4. **Enforces execution policies** — permissions, sandboxing, timeout, retry logic
5. **Persists execution history** — SQLite-backed replay, audit trail, debugging
6. **Integrates with observability** — every execution is traced (Phase 5 TracingEngine) and emits metrics
7. **Provides execution API** — REST endpoints for task submission, cancellation, replay, and inspection

Without the Execution Substrate, OCE observes but cannot act. With it, OCE becomes a **sovereign cognitive system** that can execute tasks autonomously.

---

## Current State

The following already exist (built in previous session):
- `oce/backend/execution_engine.py` (633 lines) — Full ExecutionEngine with worker pool, task queue, policies, history
- `oce/backend/execution_api.py` (252 lines) — REST API endpoints
- `oce/backend/tests/test_execution_engine.py` — 12 test classes covering all functionality
- Registered in `main.py` via `register_execution_endpoints(app)`

**Singleton tests pass. Full test suite needs async test fixes.**

---

## Phase 6 Tasks by Agent

### 🦉 RL (OWL) — Execution Engine Hardening + DSPy Integration

**Responsibilities:** Fix failing async tests, integrate DSPy optimization, execution analytics.

#### Tasks

- [ ] **OCE-6.1** Fix async test failures in `test_execution_engine.py`
  - Some async tests hang due to event loop / worker pool cleanup issues
  - Ensure all 12 test classes pass (currently singleton tests pass)
  - Add proper `asyncio` fixture cleanup with `shutdown()` calls

- [ ] **OCE-6.2** Implement `oce/backend/dspy_execution_optimizer.py`
  - `ExecutionOptimizerPipeline` — Learns optimal worker pool sizing from execution history
  - `TaskSchedulingPipeline` — Optimizes priority assignment based on task type and system load
  - `RetryPolicyPipeline` — Learns optimal retry strategies per task type
  - Integrates with existing DSPy pipeline pattern (heuristic fallbacks when DSPy not installed)

- [ ] **OCE-6.3** Implement execution analytics endpoint
  - `GET /execution/analytics` — Execution throughput, success rate, avg latency per task type
  - `GET /execution/bottlenecks` — Identifies slow tasks, worker starvation, queue buildup
  - `POST /execution/tune` — Auto-tunes worker pool size based on current load
  - Add to `execution_api.py`

- [ ] **OCE-6.4** Write tests for new Phase 6 components
  - `oce/backend/tests/test_dspy_execution.py` — 10+ tests for DSPy optimizer
  - `oce/backend/tests/test_execution_analytics.py` — 10+ tests for analytics endpoints
  - Fix remaining `test_execution_engine.py` async tests

---

### 🟣 OC (OpenClaw) — Execution Policy Design + Documentation

**Responsibilities:** Design execution policies, document the execution model.

#### Tasks

- [ ] **OCE-6.5** Design execution policy framework
  - Define policy types: rate limiting, permission levels, sandboxing rules, timeout defaults
  - Define policy enforcement points (pre-execution, during execution, post-execution)
  - File: `oce/docs/execution-policies.md`

- [ ] **OCE-6.6** Design skill/tool registry specification
  - How skills are registered, discovered, and invoked
  - Tool capability declarations and permission requirements
  - File: `oce/docs/skill-tool-registry.md`

- [ ] **OCE-6.7** Review execution engine architecture
  - Review RL's execution engine design
  - Verify alignment with SRRA-OPH execution patterns (ExecutionPatch, capability fields)
  - Post review to team-chat

---

### 🟠 OC2 (OpenClaw 2) — Execution Dashboard Frontend

**Responsibilities:** Build the execution monitoring UI.

#### Tasks

- [ ] **OCE-6.8** Implement execution monitor component
  - `oce/frontend/app/components/ExecutionMonitor.tsx`
  - Real-time task queue visualization (pending, running, completed, failed)
  - Worker pool status with utilization bars
  - Auto-refreshing via WebSocket or polling

- [ ] **OCE-6.9** Implement task detail component
  - `oce/frontend/app/components/TaskDetail.tsx`
  - Full task info: payload, execution history, retry count, trace
  - Cancel/replay controls

- [ ] **OCE-6.10** Implement execution analytics component
  - `oce/frontend/app/components/ExecutionAnalytics.tsx`
  - Throughput charts, success rate trends, bottleneck indicators
  - Auto-tune controls

- [ ] **OCE-6.11** Create execution dashboard page
  - `oce/frontend/app/execution/page.tsx`
  - Combine ExecutionMonitor, TaskDetail, ExecutionAnalytics
  - Add to main navigation

---

### 🟡 AS (Assistant Manager) — Quality Review + Integration

**Responsibilities:** Quality assurance, documentation, integration testing.

#### Tasks

- [ ] **OCE-6.12** Quality review of execution engine
  - Review `execution_engine.py` for correctness, performance, edge cases
  - Check worker pool behavior under load, task cancellation, timeout handling
  - File: `oce/docs/quality-review-phase6.md`

- [ ] **OCE-6.13** Document execution API
  - Update `oce/docs/api-reference.md` with execution endpoints
  - Document task submission format, execution policies, replay protocol

- [ ] **OCE-6.14** Integration testing
  - End-to-end: submit task → worker processes → result persisted → trace recorded
  - File: `oce/backend/tests/test_phase6_e2e.py`

---

### 🔴 PM (Polymorph) — Operator Integration + Debug Tools

**Responsibilities:** Integrate Operator tools with execution engine.

#### Tasks

- [ ] **OCE-6.15** Integrate Operator with Execution Engine
  - Operator can submit tasks, monitor execution, cancel/replay
  - File: `tools/operator/execution-integration.py`

- [ ] **OCE-6.16** Build execution debugging utilities
  - `tools/operator/execution-debug.py` — CLI for inspecting execution state
  - Commands: `queue`, `workers`, `task <id>`, `replay <id>`, `cancel <id>`, `history`

---

## Phase 6 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Async test fixes | RL | `test_execution_engine.py` | 🔄 Needs fixes |
| DSPy execution optimizer | RL | `dspy_execution_optimizer.py` | Pending |
| Execution analytics API | RL | `execution_api.py` (new endpoints) | Pending |
| DSPy optimizer tests | RL | `test_dspy_execution.py` | Pending |
| Analytics tests | RL | `test_execution_analytics.py` | Pending |
| Execution policies doc | OC | `oce/docs/execution-policies.md` | Pending |
| Skill/tool registry doc | OC | `oce/docs/skill-tool-registry.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Execution monitor UI | OC2 | `ExecutionMonitor.tsx` | Pending |
| Task detail UI | OC2 | `TaskDetail.tsx` | Pending |
| Execution analytics UI | OC2 | `ExecutionAnalytics.tsx` | Pending |
| Execution dashboard page | OC2 | `execution/page.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase6.md` | Pending |
| API docs | AS | `oce/docs/api-reference.md` | Pending |
| Integration tests | AS | `test_phase6_e2e.py` | Pending |
| Operator integration | PM | `tools/operator/execution-integration.py` | Pending |
| Debug utilities | PM | `tools/operator/execution-debug.py` | Pending |

---

## Success Criteria

1. All execution engine tests pass (12 test classes, 50+ tests)
2. Worker pool handles concurrent tasks with proper cleanup
3. Task cancellation and timeout work correctly
4. Execution history is queryable and replayable
5. DSPy optimizer provides heuristic fallbacks
6. Analytics endpoint identifies bottlenecks
7. Frontend shows real-time execution state
8. Operator tools can submit/monitor/cancel tasks
9. Total OCE tests ≥ 240 (178 current + 60+ new)

---

## Implementation Order

1. **OCE-6.1** Fix async test failures (RL) — Unblocks all other tests
2. **OCE-6.5** Execution policies (OC) — Can start immediately (docs)
3. **OCE-6.2** DSPy optimizer (RL) — After test fixes
4. **OCE-6.3** Analytics API (RL) — After DSPy optimizer
5. **OCE-6.4** Tests (RL) — After all backend code done
6. **OCE-6.8-6.11** Frontend (OC2) — After API ready
7. **OCE-6.12-6.14** Quality (AS) — After all backend code done
8. **OCE-6.15-6.16** Operator (PM) — After API ready
