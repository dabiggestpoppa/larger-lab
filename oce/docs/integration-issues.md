# OCE-SRRA Integration Issues

> **Maintained by:** PM (Polymorph)  
> **Last Updated:** 2026-05-16  
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
- **Description:** `event_fabric.py` has `ingest()` method but `srrs_adapter.py` doesn't call it. Events are created in the fabric manually but SRRA-OPH subsystem state changes don't automatically emit events.
- **Impact:** Event Fabric is empty during normal OCE operation. No real-time updates.
- **Fix Required:** Connect SRRA-OPH observer state changes, attractor updates, entropy signals to `EventFabric.ingest()`.
- **Assigned:** CC (OCE-2.2)

### 🟠 HIGH-001: Operator Tools Can't Reach OCE Backend
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `event-integration.js` assumes OCE backend at `127.0.0.1:8000`. If backend isn't running, all operator→event calls fail silently.
- **Impact:** Operator actions don't appear in Event Fabric. No error surfaced to user.
- **Fix Required:** Add connection retry, fallback to local queue, and health check before emitting.
- **Assigned:** PM (OCE-2.20)

### 🟠 HIGH-002: VS Code Controller CLI Detection Fails on Clean Windows
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `find_vscode_cli()` checks common paths but may fail if VS Code is installed in a non-standard location or if `code` isn't on PATH.
- **Impact:** VS Code Controller tools fail with "command not found".
- **Fix Required:** Add registry lookup on Windows, add config file for custom path.
- **Assigned:** PM (OCE-2.21)

### 🟡 MEDIUM-001: Event Persistence Is In-Memory Only
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `EventFabric.persist()` only increments a counter. Events are stored in Python lists — lost on restart.
- **Impact:** No event history across restarts. Trajectory reconstruction impossible.
- **Fix Required:** Add SQLite persistence layer (Phase 2+).
- **Assigned:** CC (OCE-2.4)

### 🟡 MEDIUM-002: No Event Compression for Old Events
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** Retention is enforced by dropping oldest events. No compression/summarization.
- **Impact:** Important historical context lost when retention limit hit.
- **Fix Required:** Integrate with `AdaptiveCompressionEngine` or DSPy summarization (RL's OCE-2.27).
- **Assigned:** RL (OCE-2.27)

### 🟢 LOW-001: Event Debug CLI Has No Filtering by Time Range
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `event-debug.js tail` and `replay` don't support time-range filtering.
- **Impact:** Hard to debug issues that happened at a specific time.
- **Fix Required:** Add `--since` and `--until` flags.
- **Assigned:** PM (OCE-2.22)

### 🟢 LOW-002: Operator Events Don't Include Duration
- **Status:** Open
- **Discovered:** 2026-05-16
- **Description:** `operator.command.executed` event doesn't include execution duration.
- **Impact:** Can't track performance of operator commands over time.
- **Fix Required:** Add `duration_ms` field to operator event payloads.
- **Assigned:** PM (OCE-2.20)

## Resolved Issues

| ID | Description | Resolution | Date |
|----|-------------|------------|------|
| — | — | — | — |

## Integration Test Checklist

- [ ] SRRA-OPH observer state change → Event Fabric → WebSocket → Frontend
- [ ] System command execution → Event Fabric → visible in debug tail
- [ ] VS Code file open → Event Fabric → visible in debug tail
- [ ] Git commit → Event Fabric → visible in debug tail
- [ ] Event history query returns correct results
- [ ] Event stats show accurate counts
- [ ] Health check reports all components healthy
- [ ] Event replay works for all event types
