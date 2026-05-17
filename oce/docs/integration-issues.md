# OCE-SRRA Integration Issues

> **Maintained by:** PM (Polymorph)
> **Last Updated:** 2026-05-17 06:00 UTC
> **Purpose:** Track and classify integration issues between OCE and SRRA-OPH substrate
> **Current Phase:** Phase 5 — Observability (178 tests passing)

## Issue Classification

| Severity | Meaning | Response Time |
|----------|---------|---------------|
| 🔴 Critical | System down, data loss | Immediate |
| 🟠 High | Feature broken, workaround exists | Same session |
| 🟡 Medium | Degraded performance, minor bug | Next session |
| 🟢 Low | Cosmetic, enhancement | Backlog |

## Active Issues

### 🔴 CRITICAL-001: Event Fabric → SRRA-OPH Event Ingestion Not Connected
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `event_fabric.py` has `ingest()` method but `srrs_adapter.py` doesn't call it. SRRA-OPH subsystem state changes don't automatically emit events.
- **Impact:** Event Fabric only has manual/system events. No real-time SRRA-OPH updates.
- **Fix Required:** Connect SRRA-OPH observer state changes, attractor updates, entropy signals to `EventFabric.ingest()`.
- **Assigned:** CC (OCE-2.2)

### 🟠 HIGH-002: VS Code Controller CLI Detection Fails on Clean Windows
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `find_vscode_cli()` checks common paths but may fail if VS Code is installed in a non-standard location.
- **Impact:** VS Code Controller tools fail with "command not found".
- **Fix Required:** Add registry lookup on Windows, add config file for custom path.
- **Assigned:** PM (OCE-2.21)

### 🟡 MEDIUM-001: Event Persistence Is In-Memory Only
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `EventFabric.persist()` only increments a counter. Events stored in Python lists — lost on restart.
- **Impact:** No event history across restarts. Trajectory reconstruction impossible.
- **Fix Required:** Add SQLite persistence layer.
- **Assigned:** CC (OCE-2.4)

### 🟡 MEDIUM-002: No Event Compression for Old Events
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** Retention enforced by dropping oldest events. No compression/summarization.
- **Impact:** Important historical context lost when retention limit hit.
- **Fix Required:** Integrate with `AdaptiveCompressionEngine` or DSPy summarization.
- **Assigned:** RL (OCE-2.27)

### 🟡 MEDIUM-003: Observer Runtime API Endpoints Not Yet Available
- **Status:** ✅ Resolved
- **Discovered:** 2026-05-16
- **Resolved:** 2026-05-16
- **Description:** CC built `observer_runtime.py` (OCE-3.1) + 9 API endpoints (OCE-3.4). 20 tests passing.
- **Resolution:** All observer endpoints live. PM's observer-integration.py and observer-debug.py fully operational.
- **Assigned:** CC (OCE-3.1, OCE-3.4)

### 🟡 MEDIUM-004: Observability Endpoints Not Yet Available
- **Status:** ✅ Resolved
- **Discovered:** 2026-05-17
- **Resolved:** 2026-05-17
- **Description:** RL built metrics_collector.py (OCE-5.1), tracing_engine.py (OCE-5.2), alerting_engine.py (OCE-5.3) + 12 API endpoints (OCE-5.4). 77 new tests passing.
- **Resolution:** All observability endpoints live. PM built observability-integration.py (OCE-5.17) and observability-debug.py (OCE-5.18).
- **Assigned:** RL (OCE-5.1-5.4), PM (OCE-5.17-5.18)

### 🟢 LOW-003: Observability Integration Not Tracing Operator Actions
- **Status:** ✅ Resolved
- **Discovered:** 2026-05-17
- **Resolved:** 2026-05-17
- **Description:** Operator actions (exec, kill, install) weren't recording metrics or trace spans.
- **Resolution:** observability-integration.py wraps all operator actions with metric recording + trace span lifecycle.
- **Assigned:** PM (OCE-5.17)

### 🟢 LOW-001: Event Debug CLI Has No Time-Range Filtering
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `event-debug.js tail` and `replay` don't support `--since` / `--until` flags.
- **Impact:** Hard to debug issues at specific times.
- **Fix Required:** Add time-range filtering flags.
- **Assigned:** PM (OCE-2.22)

## Resolved Issues

| ID | Description | Resolution | Date |
|----|-------------|------------|------|
| HIGH-001 | Operator tools can't reach OCE backend | Fixed API path mismatch (removed `/api/v1` prefix) | 2026-05-16 |
| — | POST /events/ingest endpoint missing | Added to main.py | 2026-05-16 |
| LOW-002 | Operator events missing duration | Added `duration_ms` to execAndEmit payload | 2026-05-16 |

## Integration Test Checklist

### Phase 2 Tests (12/12 Passing)
- [x] Backend health endpoint
- [x] SRRA-OPH substrate health (4 patches)
- [x] Event ingestion (POST /events/ingest)
- [x] Event query (GET /events with filters)
- [x] Event stats (throughput, type/source breakdown)
- [x] Event types listing (22 registered)
- [x] Node.js → OCE event emission
- [x] Debug CLI (stats, replay, health, types)
- [x] Observer status (4 active from SRRA-OPH)
- [x] Attractor state
- [x] Memory view
- [x] Operator → Event Fabric integration (observer.command.executed)

### Phase 3 Tests (All Complete)
- [x] Create observer via API
- [x] Activate/suspend/destroy observer
- [x] Observer health endpoint
- [x] Observer event subscription
- [x] Observer state persistence
- [x] Operator → Observer lifecycle integration
- [x] Observer debug CLI (list, status, health, events, logs)

### Phase 4 Tests (All Complete)
- [x] Structural memory store/search/timeline
- [x] Memory compression and export
- [x] FTS5 full-text search
- [x] Operator → Memory integration
- [x] Memory debug CLI

### Phase 5 Tests (Ongoing)
- [x] Metrics collection (event rates, observer health, memory, entropy)
- [x] Tracing engine (start/add_hop/end/search)
- [x] Alerting engine (rules, evaluate, acknowledge)
- [x] 12 observability API endpoints
- [x] Dashboard endpoint
- [x] Operator → Observability integration (OCE-5.17)
- [x] Observability debug CLI (OCE-5.18)
- [ ] Frontend observability dashboard (OCE-5.9-5.13) — Pending OC2
- [ ] Quality review (OCE-5.14) — Pending AS
- [ ] Integration tests (OCE-5.16) — Pending AS
