# OCE-SRRA Integration Issues

> **Maintained by:** PM (Polymorph)
> **Last Updated:** 2026-05-16 21:30 UTC
> **Purpose:** Track and classify integration issues between OCE and SRRA-OPH substrate

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
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** CC is building `observer_runtime.py` (OCE-3.1). Observer API endpoints don't exist yet.
- **Impact:** PM's observer-integration.js and observer-debug.js can't fully test against live observer API.
- **Fix Required:** CC completes OCE-3.1 + OCE-3.4 (API endpoints).
- **Assigned:** CC (OCE-3.1, OCE-3.4)

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

### Phase 3 Tests (Pending CC API)
- [ ] Create observer via API
- [ ] Activate/suspend/destroy observer
- [ ] Observer health endpoint
- [ ] Observer event subscription
- [ ] Observer state persistence
- [ ] Operator → Observer lifecycle integration
- [ ] Observer debug CLI (list, status, health, events, logs)
