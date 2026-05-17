# OCE Phase 7 — Adaptive Evolution

> **Generated:** 2026-05-17
> **Lead:** OWL (RL) — Phase 7 Lead
> **Status:** Planning → Active
> **Depends on:** OCE Phase 6 (Execution Substrate) — ✅ Complete (244 tests passing)

---

## What Is Adaptive Evolution?

Adaptive Evolution is the **self-improvement layer** that makes OCE learn from its own execution history and optimize its behavior over time. It:

1. **Learns from execution history** — analyzes past task executions to identify patterns, bottlenecks, and optimization opportunities
2. **Optimizes worker pool sizing** — dynamically adjusts concurrency based on load patterns (via DSPy ExecutionOptimizerPipeline)
3. **Improves task scheduling** — learns optimal priority assignment per task type (via DSPy TaskSchedulingPipeline)
4. **Adapts retry strategies** — per-task-type retry policies that minimize failures (via DSPy RetryPolicyPipeline)
5. **Detects performance drift** — monitors execution metrics for degradation and triggers auto-tuning
6. **Self-heals** — identifies recurring failures and applies preventive measures
7. **Evolves attractors** — adjusts operational goals based on observed outcomes

Without Adaptive Evolution, OCE executes but never improves. With it, OCE becomes a **self-improving cognitive system** that gets better at every task it performs.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Adaptive Evolution Layer (Phase 7)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Execution       │  │   Performance    │  │   Self-Healing   │  │
│  │   Optimizer       │  │   Drift Detector │  │   Engine         │  │
│  │   (DSPy)          │  │                  │  │                  │  │
│  │                   │  │ • Latency trend  │  │ • Failure pattern│  │
│  │ • Worker sizing   │  │ • Error rate     │  │   detection      │  │
│  │ • Task scheduling │  │ • Throughput     │  │ • Auto-repair    │  │
│  │ • Retry policies  │  │ • Queue depth    │  │ • Prevention     │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                      │            │
│  ┌────────▼─────────────────────▼──────────────────────▼─────────┐  │
│  │                    Evolution API                               │  │
│  │  GET /evolution/status   GET /evolution/recommendations        │  │
│  │  POST /evolution/tune    POST /evolution/heal                  │  │
│  │  GET /evolution/history  GET /evolution/drift                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Current State

The following already exist (built in Phase 6):
- `oce/backend/dspy_execution_optimizer.py` — 3 DSPy pipelines with heuristic fallbacks
- `oce/backend/execution_api.py` — Analytics endpoints (`/analytics`, `/bottlenecks`, `/tune`)
- `oce/backend/execution_engine.py` — Full execution engine with history and replay

Phase 7 builds on these foundations to add:
- Performance drift detection
- Self-healing engine
- Evolution API endpoints
- Attractor evolution

---

## Phase 7 Tasks by Agent

### 🦉 RL (OWL) — Drift Detection + Self-Healing + Evolution API

**Responsibilities:** Core adaptive intelligence — drift detection, self-healing, evolution API.

#### Tasks

- [ ] **OCE-7.1** Implement `oce/backend/drift_detector.py`
  - `DriftDetector` class:
    - `analyze_latency_trend(task_type, window_hours)` — Detect latency degradation
    - `analyze_error_rate_trend(task_type, window_hours)` — Detect error rate increases
    - `analyze_throughput_trend(window_hours)` — Detect throughput drops
    - `get_drift_report()` — Full drift analysis across all metrics
    - `register_alert_callback(callback)` — Trigger alerts on significant drift
  - Rolling window analysis (1hr, 6hr, 24hr, 7day)
  - Configurable drift thresholds per metric
  - SQLite persistence for historical trend data

- [ ] **OCE-7.2** Implement `oce/backend/self_healing_engine.py`
  - `SelfHealingEngine` class:
    - `analyze_failures(time_range)` — Identify recurring failure patterns
    - `generate_recommendations(failure_pattern)` — Suggest fixes
    - `apply_healing_action(action)` — Execute auto-repair
    - `get_healing_history(limit)` — Past healing actions
  - Built-in healing actions:
    - Worker pool scaling (up/down based on queue depth)
    - Retry policy adjustment (increase retries for flaky task types)
    - Timeout adjustment (increase timeout for slow task types)
    - Handler restart (re-register handlers after repeated failures)
  - Cooldown to prevent healing storms

- [ ] **OCE-7.3** Add evolution API endpoints to `execution_api.py`
  - `GET /evolution/status` — Current evolution state (drift + healing)
  - `GET /evolution/drift` — Drift report
  - `GET /evolution/recommendations` — Self-healing recommendations
  - `POST /evolution/tune` — Trigger auto-tuning (combines DSPy optimizer + drift data)
  - `POST /evolution/heal` — Execute healing action
  - `GET /evolution/history` — Evolution action history

- [ ] **OCE-7.4** Write tests for Phase 7 components
  - `oce/backend/tests/test_drift_detector.py` — 15+ tests
  - `oce/backend/tests/test_self_healing.py` — 15+ tests
  - `oce/backend/tests/test_evolution_api.py` — 10+ tests

---

### 🟣 OC (OpenClaw) — Evolution Strategy + Documentation

**Responsibilities:** Design evolution strategy, document adaptive behavior.

#### Tasks

- [ ] **OCE-7.5** Design evolution strategy framework
  - Define evolution triggers (drift detection, failure patterns, performance targets)
  - Define evolution actions (tuning, healing, policy adjustment)
  - Define evolution constraints (max change rate, rollback capability)
  - File: `oce/docs/evolution-strategy.md`

- [ ] **OCE-7.6** Design attractor evolution model
  - How operational goals (attractors) adapt based on execution outcomes
  - Convergence/divergence detection
  - File: `oce/docs/attractor-evolution.md`

- [ ] **OCE-7.7** Review adaptive evolution architecture
  - Review RL's drift detector and self-healing designs
  - Verify alignment with SRRA-OPH Phase 7 (Overlap Cognition) patterns
  - Post review to team-chat

---

### 🟠 OC2 (OpenClaw 2) — Evolution Dashboard Frontend

**Responsibilities:** Build the evolution monitoring UI.

#### Tasks

- [ ] **OCE-7.8** Implement drift monitor component
  - `oce/frontend/app/components/DriftMonitor.tsx`
  - Real-time drift indicators per task type
  - Trend charts (latency, error rate, throughput)
  - Alert badges for significant drift

- [ ] **OCE-7.9** Implement self-healing panel component
  - `oce/frontend/app/components/SelfHealingPanel.tsx`
  - Active healing actions list
  - Healing history timeline
  - Manual trigger controls

- [ ] **OCE-7.10** Create evolution dashboard page
  - `oce/frontend/app/evolution/page.tsx`
  - Combine DriftMonitor, SelfHealingPanel, EvolutionHistory
  - Add to main navigation

---

### 🟡 AS (Assistant Manager) — Quality Review + Integration

**Responsibilities:** Quality assurance, documentation, integration testing.

#### Tasks

- [ ] **OCE-7.11** Quality review of adaptive evolution components
  - Review `drift_detector.py`, `self_healing_engine.py`
  - Check drift detection accuracy, healing action safety
  - File: `oce/docs/quality-review-phase7.md`

- [ ] **OCE-7.12** Document evolution API
  - Update `oce/docs/api-reference.md` with evolution endpoints
  - Document drift thresholds, healing actions, tuning parameters

- [ ] **OCE-7.13** Integration testing
  - End-to-end: execute tasks → detect drift → trigger healing → verify improvement
  - File: `oce/backend/tests/test_phase7_e2e.py`

---

### 🔴 PM (Polymorph) — Operator Tools

**Responsibilities:** Integrate Operator tools with evolution engine.

#### Tasks

- [ ] **OCE-7.14** Add evolution commands to operator CLI
  - `evolution status` — Show drift + healing state
  - `evolution drift` — Show drift report
  - `evolution heal` — Trigger healing action
  - `evolution tune` — Trigger auto-tuning
  - `evolution history` — Show evolution history
  - Add to `tools/operator/execution-integration.py`

- [ ] **OCE-7.15** Build evolution debugging utilities
  - `tools/operator/evolution-debug.py` — CLI for inspecting evolution state
  - Commands: `status`, `drift`, `heal`, `tune`, `history`, `reset`

---

## Phase 7 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Drift Detector | RL | `oce/backend/drift_detector.py` | Pending |
| Self-Healing Engine | RL | `oce/backend/self_healing_engine.py` | Pending |
| Evolution API | RL | `execution_api.py` (new endpoints) | Pending |
| Drift tests | RL | `test_drift_detector.py` | Pending |
| Healing tests | RL | `test_self_healing.py` | Pending |
| API tests | RL | `test_evolution_api.py` | Pending |
| Evolution strategy doc | OC | `oce/docs/evolution-strategy.md` | Pending |
| Attractor evolution doc | OC | `oce/docs/attractor-evolution.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Drift monitor UI | OC2 | `DriftMonitor.tsx` | Pending |
| Self-healing panel UI | OC2 | `SelfHealingPanel.tsx` | Pending |
| Evolution dashboard page | OC2 | `evolution/page.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase7.md` | Pending |
| API docs | AS | `oce/docs/api-reference.md` | Pending |
| Integration tests | AS | `test_phase7_e2e.py` | Pending |
| Operator evolution CLI | PM | `execution-integration.py` | Pending |
| Evolution debug CLI | PM | `evolution-debug.py` | Pending |

---

## Success Criteria

1. Drift detection identifies latency/error/throughput degradation within 5 minutes
2. Self-healing engine generates actionable recommendations for common failure patterns
3. Auto-tuning improves execution throughput by ≥ 10% under load
4. Evolution API provides full visibility into adaptive behavior
5. Frontend shows real-time drift and healing status
6. Operator tools can trigger/inspect evolution actions
7. ≥ 40 new tests, total OCE ≥ 284
8. All existing 244 tests still passing

---

## Implementation Order

1. **OCE-7.1** Drift detector (RL) — Foundation for all adaptive behavior
2. **OCE-7.2** Self-healing engine (RL) — Uses drift data
3. **OCE-7.5** Evolution strategy (OC) — Can start immediately (docs)
4. **OCE-7.3** Evolution API (RL) — After drift + healing engines
5. **OCE-7.4** Tests (RL) — After all backend code
6. **OCE-7.8-7.10** Frontend (OC2) — After API ready
7. **OCE-7.11-7.13** Quality (AS) — After all backend code
8. **OCE-7.14-7.15** Operator (PM) — After API ready
