# OCE Phase 5 — Observability Architecture Review

> **Author:** OC (OpenClaw) — Analysis / Planning / Coordination
> **Date:** 2026-05-17
> **Phase:** OCE Phase 5 — Observability (OCE-5.8)
> **Role:** Architecture Reviewer
> **Scope:** MetricsCollector, TracingEngine, AlertingEngine, API endpoints, WebSocket streams

---

## Review Summary

**Overall Assessment:** ✅ **Solid foundation. Production-ready with minor improvements recommended.**

The observability layer is well-architected, follows the existing codebase patterns (singleton, SQLite backend, FastAPI integration), and provides comprehensive coverage of all OCE subsystems. 178 tests passing with only 1 Pydantic deprecation warning.

---

## 1. MetricsCollector Review

### Strengths
- **Singleton pattern** consistent with all other OCE engines
- **Rolling windows** (1min, 5min, 1hr) provide both real-time and historical views
- **SQLite persistence** for historical metrics — no external dependencies
- **Clean API**: `record_*` methods for ingestion, `get_*` methods for queries
- **Snapshot-based** summary returns a single coherent view of system state

### Recommendations
1. **Add configurable snapshot interval** — Currently snapshots are on-demand. Add a background thread that auto-saves snapshots every N seconds for historical continuity.
2. **Add metric retention policy** — Old SQLite entries should be pruned (configurable TTL, default 7 days).
3. **Consider adding a `get_health()` method** that returns a simple health score (0-1) for the entire system, useful for the SystemMap frontend.

### Code Quality
- Type hints: ✅ All methods typed
- Docstrings: ✅ All public methods documented
- Error handling: ✅ Graceful degradation
- Test coverage: ✅ Comprehensive (test_metrics_collector.py)

---

## 2. TracingEngine Review

### Strengths
- **Full event lifecycle tracking** — from ingestion to final outcome
- **Hop-level granularity** — each observer action is tracked with latency
- **Search and filter** — flexible query API for finding specific traces
- **Auto-expiry** — old traces are cleaned up automatically (configurable TTL)
- **Active trace tracking** — can see in-flight traces in real-time

### Recommendations
1. **Add trace sampling** — For high-throughput systems, trace every Nth event rather than every event. Add a `sample_rate` config (default 1.0 = trace everything).
2. **Add trace export** — Allow exporting traces as JSON for external analysis tools.
3. **Consider adding parent-child trace relationships** — Some events spawn sub-events. A `parent_trace_id` field would enable tree-structured traces.

### Code Quality
- Type hints: ✅ All methods typed
- Docstrings: ✅ All public methods documented
- Error handling: ✅ Graceful (non-existent traces return None, not exceptions)
- Test coverage: ✅ Excellent (test_tracing_engine.py — 22 tests)

---

## 3. AlertingEngine Review

### Strengths
- **Rule-based** — flexible alert rules with configurable conditions
- **Cooldown mechanism** — prevents alert storms
- **State machine** — firing → acknowledged → resolved lifecycle
- **Auto-resolve** — rules can auto-resolve when condition clears
- **History** — full alert history maintained in SQLite

### Recommendations
1. **Add alert grouping** — Multiple alerts from the same rule should be grouped in the UI rather than listed separately.
2. **Add escalation** — If an alert is not acknowledged within N minutes, escalate to higher severity.
3. **Add notification channels** — Currently alerts are in-memory/SQLite only. Add webhook/Telegram notification support.
4. **Add alert templates** — Pre-configured alert rules for common OCE scenarios (see observability-map.md).

### Code Quality
- Type hints: ✅ All methods typed
- Docstrings: ✅ All public methods documented
- Error handling: ✅ Graceful
- Test coverage: ✅ Good (test_alerting_engine.py)

---

## 4. API Endpoints Review

### Coverage Assessment

| Feature | Endpoint | Status |
|---------|----------|--------|
| Metrics snapshot | `GET /metrics` | ✅ |
| Metrics history | `GET /metrics/history` | ✅ |
| Trace list | `GET /traces` | ✅ |
| Trace detail | `GET /traces/{trace_id}` | ✅ |
| Traces by observer | `GET /traces/observer/{observer_id}` | ✅ |
| Active alerts | `GET /alerts` | ✅ |
| Alert history | `GET /alerts/history` | ✅ |
| Acknowledge alert | `POST /alerts/{id}/acknowledge` | ✅ |
| Alert rules | `POST /alerts/rules` | ✅ |
| Dashboard data | `GET /dashboard` | ✅ |
| WS metrics | `/ws/metrics` | ✅ |
| WS alerts | `/ws/alerts` | ✅ |
| WS events | `/ws/events` | ✅ |
| WS observers | `/ws/observers` | ✅ |

### Recommendations
1. **Add `GET /alerts/rules`** — List all configured alert rules (currently only add, no list).
2. **Add `DELETE /alerts/rules/{rule_id}`** — Remove alert rules via API.
3. **Add `GET /dashboard`** — Already exists but should be documented in API reference.
4. **Add pagination** — `GET /traces` and `GET /alerts` should support `limit`/`offset` for large result sets.
5. **Add OpenAPI tags** — Group endpoints by feature (metrics, traces, alerts, observers) for better docs.

---

## 5. WebSocket Streams Review

### Strengths
- **4 separate streams** — metrics, alerts, events, observers each have dedicated WS
- **Real-time** — dashboard gets live updates without polling
- **ConnectionManager** — centralized WS connection management

### Recommendations
1. **Add heartbeat/ping** — WebSocket connections should have a heartbeat mechanism to detect dead connections.
2. **Add subscription filtering** — Clients should be able to subscribe to specific event types rather than receiving everything.
3. **Add reconnection state** — On reconnect, send a full snapshot to bring the client up to date.

---

## 6. Integration with Existing OCE Layers

| Observability Feature | Integrates With | Method |
|----------------------|-----------------|--------|
| MetricsCollector | EventFabric | `record_event()` called on each event |
| MetricsCollector | ObserverRuntime | `record_observer_health()` on health check |
| MetricsCollector | StructuralMemory | `record_memory_usage()` on store/compress |
| TracingEngine | EventFabric | `start_trace()` on event ingestion |
| TracingEngine | ObserverRuntime | `add_hop()` per observer processing |
| AlertingEngine | All layers | `evaluate()` called periodically |
| AlertingEngine | ObserverRuntime | Health-based alerts |

### Gap Analysis
- **SRRA-OPH substrate metrics** — The SRRS adapter doesn't currently emit metrics to MetricsCollector. Add `srra_adapter.record_metrics(mc)` calls.
- **DSPy pipeline metrics** — Pipeline success rates should be tracked in MetricsCollector.
- **Entropy economics** — Entropy budget tracking exists but should be connected to AlertingEngine for automatic alerts.

---

## 7. Test Coverage Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| test_event_fabric.py | 32 | ✅ All passing |
| test_observer_runtime.py | 27 | ✅ All passing |
| test_structural_memory.py | 30 | ✅ All passing |
| test_topology_routing.py | 19 | ✅ All passing |
| test_metrics_collector.py | 28 | ✅ All passing |
| test_tracing_engine.py | 22 | ✅ All passing |
| test_alerting_engine.py | 20 | ✅ All passing |
| **Total** | **178** | **✅ 178/178 passing** |

---

## 8. Action Items for Phase 5 Completion

### Must Have (Blocking OC2 Frontend)
- [x] MetricsCollector API stable ✅
- [x] TracingEngine API stable ✅
- [x] AlertingEngine API stable ✅
- [x] WebSocket streams working ✅
- [x] Data model documented ✅ (OCE-5.6)
- [x] System map documented ✅ (OCE-5.7)

### Should Have (Post-Frontend)
- [ ] Add `GET /alerts/rules` endpoint
- [ ] Add `DELETE /alerts/rules/{rule_id}` endpoint
- [ ] Add pagination to trace/alert list endpoints
- [ ] Add WebSocket heartbeat mechanism
- [ ] Add alert grouping in API response
- [ ] Connect SRRS adapter metrics
- [ ] Add metric retention policy (7-day TTL default)

### Nice to Have (Phase 6+)
- [ ] Trace sampling for high throughput
- [ ] Parent-child trace relationships
- [ ] Alert escalation
- [ ] Webhook/Telegram alert notifications
- [ ] Trace export (JSON)

---

## 9. Sign-off

**Architecture approved for OC2 frontend development.** The observability backend is stable, well-tested, and fully documented. OC2 can begin building dashboard components (OCE-5.9 through OCE-5.13) against the current API with confidence that the backend contracts are stable.

**Reviewed by:** OC (OpenClaw) — Architecture Review
**Date:** 2026-05-17
**Verdict:** ✅ **APPROVED — Ready for frontend development**
