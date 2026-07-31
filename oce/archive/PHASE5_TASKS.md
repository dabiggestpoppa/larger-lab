# OCE Phase 5 â€” Observability

> **Generated:** 2026-05-17
> **Lead:** OWL (RL) â€” Phase 5 Lead
> **Status:** Planning â†’ Active
> **Depends on:** OCE Phase 4 (Structural Memory) â€” âœ… Complete (101 tests passing)

---

## What Is Observability?

Observability is the **monitoring, metrics, and transparency layer** that makes the entire OCE system visible, debuggable, and self-aware. It:

1. **Collects metrics** â€” event throughput, observer health, memory usage, entropy consumption
2. **Provides dashboards** â€” real-time system state, historical trends, anomaly detection
3. **Enables alerting** â€” threshold-based alerts for degradation, failures, entropy exhaustion
4. **Supports tracing** â€” event flow tracing through the topology, observer decision trails
5. **Exposes system introspection** â€” OCE can observe itself, detect drift, self-diagnose

Without Observability, OCE is a black box. With it, OCE becomes a **self-aware cognitive system** that can detect and report its own state.

---

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     Observability Layer (Phase 5)                   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                     â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚   Metrics     â”‚  â”‚   Tracing    â”‚  â”‚      Alerting            â”‚  â”‚
â”‚  â”‚   Collector   â”‚  â”‚   Engine     â”‚  â”‚      Engine              â”‚  â”‚
â”‚  â”‚              â”‚  â”‚              â”‚  â”‚                          â”‚  â”‚
â”‚  â”‚ â€¢ Event rates â”‚  â”‚ â€¢ Event flow â”‚  â”‚ â€¢ Threshold alerts       â”‚  â”‚
â”‚  â”‚ â€¢ Observer    â”‚  â”‚ â€¢ Observer   â”‚  â”‚ â€¢ Anomaly detection      â”‚  â”‚
â”‚  â”‚   health      â”‚  â”‚   decision   â”‚  â”‚ â€¢ Entropy exhaustion     â”‚  â”‚
â”‚  â”‚ â€¢ Memory      â”‚  â”‚   trails     â”‚  â”‚ â€¢ Health degradation     â”‚  â”‚
â”‚  â”‚   usage       â”‚  â”‚ â€¢ Topology   â”‚  â”‚ â€¢ Auto-repair triggers   â”‚  â”‚
â”‚  â”‚ â€¢ Entropy     â”‚  â”‚   path trace â”‚  â”‚                          â”‚  â”‚
â”‚  â”‚   budget      â”‚  â”‚              â”‚  â”‚                          â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚         â”‚                 â”‚                        â”‚                â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚                    Observability API                           â”‚  â”‚
â”‚  â”‚  GET /metrics  GET /traces  GET /alerts  GET /dashboard       â”‚  â”‚
â”‚  â”‚  WS /ws/metrics  WS /ws/alerts                                 â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                             â”‚                                       â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚                  Dashboard Frontend                            â”‚  â”‚
â”‚  â”‚  MetricsPanel  TraceView  AlertPanel  SystemMap              â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                                                                     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚                    â”‚                      â”‚
         â–¼                    â–¼                      â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Event Fabric   â”‚ â”‚ Observer Runtimeâ”‚ â”‚  Structural Memory      â”‚
â”‚  (Phase 2)      â”‚ â”‚  (Phase 3)      â”‚ â”‚  (Phase 4)              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Phase 5 Tasks by Agent

### ðŸ¦‰ RL (OWL) â€” Metrics Collector + Tracing Engine + Alerting

**Responsibilities:** Core observability engine â€” metrics, traces, alerts.

#### Backend Tasks

- [x] **OCE-5.1** Implement `oce/backend/metrics_collector.py`
  - `MetricsCollector` class:
    - `record_event(event_type, source, latency_ms)` â€” Record event metrics
    - `record_observer_health(observer_id, health_score, entropy)` â€” Observer metrics
    - `record_memory_usage(layer, size_bytes, entry_count)` â€” Memory metrics
    - `record_entropy_budget(consumed, remaining, total)` â€” Entropy tracking
    - `get_metrics_summary()` â€” Aggregated metrics snapshot
    - `get_metrics_history(metric_name, time_range)` â€” Historical data
    - `reset_counters()` â€” Reset rolling counters
  - Rolling window counters (1min, 5min, 1hr)
  - SQLite storage for historical metrics at `data/metrics.db`
  - Singleton pattern (consistent with existing codebase)

- [x] **OCE-5.2** Implement `oce/backend/tracing_engine.py`
  - `TracingEngine` class:
    - `start_trace(event_id, source)` â€” Begin event trace
    - `add_hop(trace_id, observer_id, action, latency_ms)` â€” Add topology hop
    - `end_trace(trace_id, outcome)` â€” Complete trace
    - `get_trace(trace_id)` â€” Full trace with all hops
    - `get_active_traces()` â€” Currently in-flight traces
    - `get_traces_by_observer(observer_id)` â€” All traces through an observer
    - `search_traces(filters)` â€” Filter by time, observer, outcome
  - Trace data: event flow path, observer actions, latency per hop, outcome
  - Auto-expire traces older than configurable TTL

- [x] **OCE-5.3** Implement `oce/backend/alerting_engine.py`
  - `AlertingEngine` class:
    - `add_rule(name, metric, threshold, comparison, severity, cooldown_sec)` â€” Add alert rule
    - `evaluate(metrics_snapshot)` â€” Evaluate all rules against current metrics
    - `get_active_alerts()` â€” Currently firing alerts
    - `get_alert_history(limit)` â€” Recent alert history
    - `acknowledge_alert(alert_id)` â€” Acknowledge alert
    - `clear_alert(alert_id)` â€” Clear resolved alert
  - Built-in rules:
    - Observer health < 0.3 â†’ critical alert
    - Event queue depth > 1000 â†’ warning alert
    - Memory usage > 90% â†’ critical alert
    - Entropy budget < 10% â†’ warning alert
    - Observer error rate > 20% â†’ critical alert
  - Alert states: firing, acknowledged, resolved
  - Cooldown to prevent alert storms

- [x] **OCE-5.4** Add observability API endpoints to `main.py`
  - `GET /metrics` â€” Current metrics summary
  - `GET /metrics/history` â€” Historical metrics (query: metric_name, range)
  - `GET /traces` â€” List active traces
  - `GET /traces/{id}` â€” Full trace detail
  - `GET /traces/observer/{id}` â€” Traces by observer
  - `GET /alerts` â€” Active alerts
  - `GET /alerts/history` â€” Alert history
  - `POST /alerts/{id}/acknowledge` â€” Acknowledge alert
  - `POST /alerts/rules` â€” Add custom alert rule
  - `GET /dashboard` â€” Full dashboard data (metrics + alerts + traces summary)
  - `WS /ws/metrics` â€” Real-time metrics stream
  - `WS /ws/alerts` â€” Real-time alert stream

- [x] **OCE-5.5** Write tests
  - `oce/backend/tests/test_metrics_collector.py` â€” 15+ tests
  - `oce/backend/tests/test_tracing_engine.py` â€” 15+ tests
  - `oce/backend/tests/test_alerting_engine.py` â€” 15+ tests

---

### ðŸŸ£ OC (OpenClaw) â€” Observability Docs + System Map

**Responsibilities:** Documentation, system visualization design.

#### Tasks

- [x] **OCE-5.6** Design observability data model
  - Define metrics schema (name, type, labels, retention)
  - Define trace schema (spans, references, attributes)
  - Define alert schema (rules, states, history)
  - File: `oce/docs/observability-data-model.md`

- [x] **OCE-5.7** Design system observability map
  - What to monitor in each OCE layer (Event Fabric, Observer Runtime, Structural Memory)
  - Key metrics per layer
  - Alert thresholds per layer
  - File: `oce/docs/observability-map.md`

- [x] **OCE-5.8** Review observability architecture
  - Review RL's observability engine design
  - Verify alignment with SRRA-OPH entropy economics patterns
  - Post review to team-chat

---

### ðŸŸ  OC2 (OpenClaw 2) â€” Observability Dashboard Frontend

**Responsibilities:** Build the observability dashboard UI.

#### Tasks

- [ ] **OCE-5.9** Implement metrics panel component
  - `oce/frontend/app/components/MetricsPanel.tsx`
  - Real-time metrics display (event rates, observer health, memory, entropy)
  - Auto-refreshing via WebSocket (`/ws/metrics`)
  - Color-coded status indicators

- [ ] **OCE-5.10** Implement trace view component
  - `oce/frontend/app/components/TraceView.tsx`
  - Visual trace timeline (event â†’ observer hops â†’ outcome)
  - Filter by observer, time range, outcome
  - Click to expand trace detail

- [ ] **OCE-5.11** Implement alert panel component
  - `oce/frontend/app/components/AlertPanel.tsx`
  - Active alerts list with severity colors
  - Acknowledge/clear controls
  - Alert history toggle
  - Real-time via WebSocket (`/ws/alerts`)

- [ ] **OCE-5.12** Implement system map component
  - `oce/frontend/app/components/SystemMap.tsx`
  - Visual topology map with observer nodes
  - Color-coded by health status
  - Event flow animation
  - Click node for detail panel

- [ ] **OCE-5.13** Create observability dashboard page
  - `oce/frontend/app/observability/page.tsx`
  - Combine MetricsPanel, TraceView, AlertPanel, SystemMap
  - Responsive grid layout
  - Time range selector

---

### ðŸŸ¡ AS (Assistant Manager) â€” Quality Review + Integration

**Responsibilities:** Quality assurance, documentation, integration testing.

#### Tasks

- [ ] **OCE-5.14** Quality review of observability engine
  - Review `metrics_collector.py`, `tracing_engine.py`, `alerting_engine.py`
  - Check metrics accuracy, trace completeness, alert correctness
  - File: `oce/docs/quality-review-phase5.md`

- [ ] **OCE-5.15** Document observability API
  - Update `oce/docs/api-reference.md` with observability endpoints
  - Document alert rule configuration
  - Document metrics query language

- [ ] **OCE-5.16** Integration testing
  - End-to-end: emit events â†’ verify metrics â†’ check traces â†’ trigger alerts
  - File: `oce/backend/tests/test_phase5_e2e.py`

---

### ðŸ”´ PM (Polymorph) â€” Operator Integration + Debug Tools

**Responsibilities:** Integrate Operator tools with observability.

#### Tasks

- [ ] **OCE-5.17** Integrate Operator with Observability
  - Operator actions generate trace spans
  - Operator can query metrics for context
  - File: `tools/operator/observability-integration.py`

- [ ] **OCE-5.18** Build observability debugging utilities
  - `tools/operator/observability-debug.py` â€” CLI for inspecting observability
  - Commands: `metrics`, `traces`, `alerts`, `dashboard`, `topology`
  - Color-coded output, filterable

---

## Phase 5 Deliverables

| Component | Owner | File | Status |
|-----------|-------|------|--------|
| Metrics Collector | RL | `oce/backend/metrics_collector.py` | âœ… Complete |
| Tracing Engine | RL | `oce/backend/tracing_engine.py` | âœ… Complete |
| Alerting Engine | RL | `oce/backend/alerting_engine.py` | âœ… Complete |
| Observability API | RL | `oce/backend/main.py` (new endpoints) | âœ… Complete |
| Metrics tests | RL | `oce/backend/tests/test_metrics_collector.py` | âœ… Complete |
| Tracing tests | RL | `oce/backend/tests/test_tracing_engine.py` | âœ… Complete |
| Alerting tests | RL | `oce/backend/tests/test_alerting_engine.py` | âœ… Complete |
| Data model docs | OC | `oce/docs/observability-data-model.md` | Pending |
| Observability map | OC | `oce/docs/observability-map.md` | Pending |
| Architecture review | OC | team-chat | Pending |
| Metrics panel UI | OC2 | `MetricsPanel.tsx` | Pending |
| Trace view UI | OC2 | `TraceView.tsx` | Pending |
| Alert panel UI | OC2 | `AlertPanel.tsx` | Pending |
| System map UI | OC2 | `SystemMap.tsx` | Pending |
| Dashboard page | OC2 | `observability/page.tsx` | Pending |
| Quality review | AS | `oce/docs/quality-review-phase5.md` | Pending |
| API docs | AS | `oce/docs/api-reference.md` | Pending |
| Integration tests | AS | `oce/backend/tests/test_phase5_e2e.py` | Pending |
| Operator integration | PM | `tools/operator/observability-integration.py` | Pending |
| Debug utilities | PM | `tools/operator/observability-debug.py` | Pending |

---

## Success Criteria

1. Metrics collected for all core subsystems (events, observers, memory, entropy)
2. Event traces show full flow path through topology with latency per hop
3. Alerting rules fire correctly with cooldown and acknowledgment
4. All observability endpoints tested and documented
5. Frontend dashboard shows real-time metrics, traces, alerts, and system map
6. Operator tools integrated with observability layer
7. Minimum 45 new tests (15 per engine), all passing
8. Total OCE tests â‰¥ 146 (101 current + 45 new)

---

## Implementation Order

1. **OCE-5.1** Metrics Collector (RL) â€” Foundation, no dependencies
2. **OCE-5.2** Tracing Engine (RL) â€” Can start in parallel with 5.1
3. **OCE-5.3** Alerting Engine (RL) â€” Depends on 5.1 (needs metrics)
4. **OCE-5.6** Data Model (OC) â€” Can start immediately (docs)
5. **OCE-5.4** API Endpoints (RL) â€” Depends on 5.1, 5.2, 5.3
6. **OCE-5.5** Tests (RL) â€” Depends on 5.1, 5.2, 5.3
7. **OCE-5.9-5.13** Frontend (OC2) â€” Depends on 5.4 (API ready)
8. **OCE-5.14-5.16** Quality (AS) â€” Depends on 5.1-5.5
9. **OCE-5.17-5.18** Operator (PM) â€” Depends on 5.4

