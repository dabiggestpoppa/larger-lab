# 🟡 Assistant Manager (AS) — PO × VTuber Integration Tasks

> **Agent:** Assistant Manager (AS)
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Start:** 2026-06-05 15:00 UTC
> **Status:** 🟡 STANDBY → wait for PM recon, then P1.6 smoke. Then take ownership of all integration test suites.

---

## Mission

You are the **quality gate** for PO × VTuber integration. You write the smoke tests, the integration suites, the memory continuity, the state persistence, and the e2e identity tests. Every phase gate depends on you.

## Tasks

### Phase 1 — Smoke Test (your first)

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P1.6 | E2E smoke test | `vtuber_integration/tests/test_smoke.py` | 2 | ⏳ Queued |

### Phase 2 — Session + State + Tests

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P2.6 | Memory continuity session | `oce/backend/po_session.py` | 3 | ⏳ Queued |
| P2.10 | PO state persistence | `oce/backend/po_state.py` | 3 | ⏳ Queued |
| P2.12 | Phase 2 integration test suite | `vtuber_integration/tests/test_phase2.py` | 5 | ⏳ Queued |

### Phase 3 — E2E Identity Test

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P3.5 | Phase 3 e2e identity test | `vtuber_integration/tests/test_phase3.py` | 4 | ⏳ Queued |

**Total: 17 tests across 5 components.**

## Component Specs

### P1.6 — E2E Smoke Test (`test_smoke.py`)

Real VTuber → OCE round-trip. Two tests:
1. **Select PO from provider list** — spawn VTuber subprocess, set provider to "PO" via config, verify the model registry contains "po"
2. **Chat round-trip** — POST to OCE `/api/po/chat` with OpenAI-shape request, verify OpenAI-shape response, no exceptions

**Test framework:** pytest. May need to skip subprocess test if VTuber not installable in CI.

### P2.6 — Memory Continuity Session (`po_session.py`)

Maintains conversation history keyed by `session_id`. Sliding window of 20 messages. Persisted to disk (JSON or SQLite).

**Interface:**
```python
class POSessionStore:
    def __init__(self, storage_path: str = "oce/state/po_sessions/"):
        ...

    def get_or_create(self, session_id: str) -> POSession:
        ...

    def append(self, session_id: str, message: Message) -> None:
        ...

    def history(self, session_id: str, limit: int = 20) -> list[Message]:
        ...

    def clear(self, session_id: str) -> None:
        ...
```

**Tests (3):**
1. Create new session → empty history
2. Append messages → history grows up to limit
3. Restart (new instance) → history persists

### P2.10 — PO State Persistence (`po_state.py`)

Persists PO operational state (last-seen ts, total requests, error count, etc.) across restarts. Used for telemetry and graceful resume.

**Interface:**
```python
class POStateStore:
    def __init__(self, path: str = "oce/state/po_state.json"):
        ...

    def get(self) -> POState:
        ...

    def update(self, **kwargs) -> None:
        ...

    def increment(self, key: str, by: int = 1) -> None:
        ...
```

**Tests (3):**
1. Get default state on first run
2. Update fields → persists to disk
3. Reload → state survives

### P2.12 — Phase 2 Integration Suite (`test_phase2.py`)

End-to-end tests for the streaming cognitive layer. Five tests:
1. POST `/api/po/chat` (no stream) → full response, contains expected stages
2. POST `/api/po/stream` → SSE events arrive in correct order (processing → scan → retrieve → route → chunks → done)
3. `/api/po/context` returns workspace + vault summary
4. `/api/po/commands` accepts and dispatches a command
5. Multi-provider regression — OpenAI provider endpoint still works after PO module is loaded

### P3.5 — Phase 3 E2E Identity Test (`test_phase3.py`)

Cross-interface identity test. Four tests:
1. Start Telegram session (mock if OC2 off-table) → write to `po_session`
2. Start VTuber session with same identity → reads same `po_session` history
3. Cross-interface message continuity — message in A appears in B's history
4. Identity bridge handles missing/invalid session gracefully

## Build Order

```
Wait for PM recon ✅
              ↓
        P1.6 (smoke test)  ← blocks Phase 1 gate
              ↓
        P2.6 (POSessionStore)
        P2.10 (POStateStore)  ← parallel
              ↓
        P2.12 (Phase 2 suite)  ← blocks Phase 2 gate
              ↓
        P3.5 (Phase 3 suite)  ← blocks Phase 3 gate
```

## Commit Prefix

- `[PO-VTUBER P1] AS: <description>` for P1.6
- `[PO-VTUBER P2] AS: <description>` for P2.6, P2.10, P2.12
- `[PO-VTUBER P3] AS: <description>` for P3.5

## Test Reporting

After each phase gate, post to team-chat:
```
[AS] 2026-06-05 HH:MM UTC — PHASE {N} GATE RESULTS

P{N} components: X/X built
P{N} tests: Y/Y passing
P{N+1} cleared to start

Notes: <any failures, blockers, or open issues>
```

---

## Phase 3 Gate Results — 2026-06-06 10:00 UTC

### P3 Test Results
| Test Suite | Tests | Status |
|------------|-------|--------|
| P1.6 Smoke | 12 | ✅ PASS |
| P2.1-P2.12 Integration | 34 | ✅ PASS |
| P3.1-P3.5 Identity | 15 | ✅ PASS |
| **TOTAL** | **61** | ✅ **ALL PASS** |

### Fix Applied
- Added `EXCLUDE_DIRS` to `po_workspace.py` to skip `.venv`, `__pycache__`, `.git`, `node_modules`, `archive`, `.openclaw`, `memory-bank`
- Reduced scan time from 7+ min to ~2 min

### Commit
- `b562f1f1` — `[PO-VTUBER P3] AS: Exclude .venv and large dirs in WorkspaceScanner for fast tests`

### Status
- ✅ PHASE 3 GATE COMPLETE
- Ready for Phase 4
