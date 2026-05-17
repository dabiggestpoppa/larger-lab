# OCE Phase 3 — Quality Review: Observer Runtime

> **Reviewer:** Sub-AS (Assistant Manager)
> **Date:** 2026-05-16
> **Scope:** `oce/backend/observer_runtime.py`, `oce/backend/tests/test_observer_runtime.py`, `oce/backend/main.py` (observer endpoints)

## Summary

CC's Observer Runtime implementation is **solid and well-architected** — clean state machine, proper async patterns, comprehensive lifecycle management, and 20/20 tests passing. The design follows SRRA-OPH principles (no global state, self-stabilizing observers, health monitoring). Several issues found ranging from minor to medium severity.

## What's Good ✅

1. **Clean state machine** — `ObserverState` enum with CREATED → ACTIVE → SUSPENDED → DESTROYED lifecycle is well-defined and enforced
2. **Proper async throughout** — All lifecycle methods use `asyncio.Lock` for thread safety, event handling is async
3. **Pydantic models** — `ObserverConfig`, `Observer`, `ObserverHealth` are well-structured with sensible defaults
4. **Event-driven architecture** — Observers subscribe to Event Fabric events, state changes emit events
5. **Health monitoring** — Health score tracking, entropy, event/error counts, uptime calculation
6. **State persistence** — Snapshot/restore pattern for reconstruction from sparse anchors
7. **Statistics** — Comprehensive stats API (by state, by type, avg health, totals)
8. **Singleton pattern** — `get_runtime()` ensures single instance, consistent with Event Fabric pattern
9. **Test coverage** — 20 tests covering config, lifecycle, query, health, persistence, stats, singleton
10. **API integration** — 9 REST endpoints + 1 WebSocket endpoint in `main.py`, all with proper error handling

## Issues Found 🔧

### 🟡 MEDIUM-001: State change event emits wrong previous_state

**File:** `oce/backend/observer_runtime.py`
**Method:** `activate_observer()` (line ~101)
**Issue:** The state is changed to ACTIVE *before* emitting the event, so `previous_state` in the event payload always shows "active" instead of the actual previous state.

```python
# Current (bug):
observer.state = ObserverState.ACTIVE  # State changed first
...
"previous_state": observer.state.value,  # This is now "active", not the real previous state
```

**Fix:** Capture previous state before changing:
```python
previous_state = observer.state
observer.state = ObserverState.ACTIVE
...
"previous_state": previous_state.value,
```

**Same bug in:** `suspend_observer()` — `previous_state` is captured correctly there (line ~119). Inconsistent pattern.

**Impact:** Event consumers can't accurately track state transition history. The `suspend_observer` method does this correctly, so this is likely a copy-paste oversight.

---

### 🟡 MEDIUM-002: Health score can go negative or exceed 1.0 with enough events

**File:** `oce/backend/observer_runtime.py`
**Method:** `_handle_event()` (line ~169)
**Issue:** Health score decrements by 0.1 for critical events and increments by 0.01 for low-priority events. With enough critical events, `health_score` can go below 0.0 (the `max(0.0, ...)` clamp prevents negative, but the increment has no upper bound check beyond `min(1.0, ...)`).

Actually, looking closer, the clamps *are* correct: `max(0.0, ...)` and `min(1.0, ...)`. **This is not a bug** — the bounds are properly enforced. However, the asymmetry (0.1 decrement vs 0.01 increment) means health degrades 10x faster than it recovers. This may be intentional (critical events are serious), but worth noting.

**Recommendation:** Document the health score algorithm explicitly. Consider whether the 10:1 ratio is intentional. If observers process many critical events, they'll stay unhealthy for a long time.

---

### 🟡 MEDIUM-003: Observer subscriptions are not cleaned up on destroy

**File:** `oce/backend/observer_runtime.py`
**Method:** `destroy_observer()` (line ~131)
**Issue:** When an observer is destroyed, it's removed from `self._observers`, but its Event Fabric subscription remains active. The lambda callback `lambda e, oid=observer.observer_id: self._handle_event(oid, e)` will still fire for events matching the subscription, but `_handle_event` will find no observer (since it was deleted) and return silently.

**Impact:** Minor — the `_handle_event` method checks `self._observers.get(observer_id)` and returns None if not found. But it means unnecessary event processing and a small memory leak (the lambda closure holds references).

**Fix:** Track subscriptions per observer and unsubscribe on destroy:
```python
# In create_observer:
sub = self._fabric.subscribe(...)
observer.metadata["_subscription"] = sub

# In destroy_observer:
if sub := observer.metadata.get("_subscription"):
    self._fabric.unsubscribe(sub)
```

---

### 🟡 MEDIUM-004: `subscribe_observer` endpoint doesn't validate event types

**File:** `oce/backend/main.py`
**Endpoint:** `POST /observers/{observer_id}/subscribe`
**Issue:** The endpoint accepts any list of event types without validating them against the `EVENT_TYPES` registry. Invalid event types will create subscriptions that never match any events.

**Impact:** Low — silent failure, no error. But it could confuse operators who think they're subscribing to events that don't exist.

**Fix:** Validate event types against `EVENT_TYPES` and return a warning for unknown types:
```python
valid_types = set(fabric.get_event_types())
unknown = [t for t in event_types if t not in valid_types]
if unknown:
    logger.warning(f"Unknown event types in subscription: {unknown}")
```

---

### 🟢 LOW-001: No drift_signals tracking in health model

**File:** `oce/backend/observer_runtime.py`
**Model:** `ObserverHealth` (line ~68)
**Issue:** `ObserverHealth` has a `drift_signals` field (default 0), but it's never populated or updated anywhere in the runtime. The field exists in the model but is always 0.

**Impact:** None currently — the field is a placeholder for future drift detection integration. But it could confuse API consumers who expect it to have real data.

**Recommendation:** Either implement drift signal tracking or remove the field until Phase 5 (Observability).

---

### 🟢 LOW-002: `budget_remaining` is hardcoded

**File:** `oce/backend/observer_runtime.py`
**Model:** `ObserverHealth` (line ~69)
**Issue:** `budget_remaining` is hardcoded to 500.0. There's no actual budget tracking in the Observer Runtime.

**Impact:** None — this is a placeholder for Phase 9 (Entropy Economics) integration. But the hardcoded value could be misleading.

**Recommendation:** Add a TODO comment linking to Phase 9, or make it configurable via observer config.

---

### 🟢 LOW-003: `get_observer_status` endpoint returns different schema than observer endpoints

**File:** `oce/backend/main.py`
**Endpoints:** `GET /observers` (line ~139) vs `GET /observers` (line ~259)
**Issue:** There are TWO `/observers` GET endpoints — one at line ~139 (returns `List[ObserverStatus]` with `state`, `entropy`, `task`) and one at line ~259 (returns a different schema with `name`, `type`, `state`, `health_score`, `event_count`). FastAPI will only register one of them (whichever is defined first), so the second one is dead code.

**Impact:** Medium — the first endpoint (`get_observer_status`) uses the SRRA-OPH adapter's `get_observer_status()` which returns a different schema than what the Observer Runtime provides. The second endpoint (from Observer Runtime) is unreachable.

**Fix:** Remove the duplicate endpoint or merge them. The Observer Runtime's `GET /observers` should be the canonical one since it's the Phase 3 implementation.

---

### 🟢 LOW-004: WebSocket observer endpoint sends stats, not individual updates

**File:** `oce/backend/main.py`
**Endpoint:** `WS /ws/observers`
**Issue:** The WebSocket endpoint broadcasts the same `runtime.get_stats()` every 5 seconds. It doesn't send individual observer state changes, health updates, or event processing notifications. The `ObserverHealth` model has fields like `drift_signals` and `budget_remaining` that are never updated in real-time.

**Impact:** Low — the WebSocket works for basic monitoring, but it's essentially a polling loop over a WebSocket. True push-based updates would be more efficient.

**Recommendation:** For Phase 3 this is acceptable. For Phase 5 (Observability), consider event-driven WebSocket messages.

---

## Test Results

```
oce/backend/tests/test_observer_runtime.py — 20 passed ✅
oce/backend/tests/test_event_fabric.py — 32 passed ✅
Total: 52 OCE tests passing
```

## Test Coverage Analysis

| Area | Tests | Coverage |
|------|-------|----------|
| Config creation | 1 | ✅ ObserverConfig validation |
| Lifecycle (create/activate/suspend/destroy) | 6 | ✅ All state transitions + edge cases |
| Query (get/list/filter) | 4 | ✅ By ID, all, by state, by type |
| Health | 3 | ✅ Basic, after events, nonexistent |
| Persistence | 3 | ✅ Snapshot, restore, nonexistent |
| Stats | 2 | ✅ With observers, empty |
| Singleton | 1 | ✅ Same instance |

**Missing test coverage:**
- Event routing to observers (no test verifies `_handle_event` actually processes events)
- Concurrent observer operations (no test for race conditions)
- Subscription management (no test for subscribe/unsubscribe)
- Observer restoration to ACTIVE state (restore always restores to CREATED state)

## Recommendations (Priority Order)

1. **Fix MEDIUM-001** — Capture previous_state before state change in `activate_observer()`
2. **Fix MEDIUM-003** — Clean up Event Fabric subscriptions on observer destroy
3. **Fix LOW-003** — Remove duplicate `GET /observers` endpoint
4. **Add tests** for event routing, subscription lifecycle, and concurrent operations
5. **Document health score algorithm** — Make the 10:1 degrade:recover ratio explicit
6. **Add TODO comments** for placeholder fields (`drift_signals`, `budget_remaining`)

## Verdict

**APPROVED for Phase 3 Observer Runtime.** Core engine is solid, well-tested, and ready for Phase 4 integration. The issues found are minor and can be addressed in follow-up work. The architecture is clean, the state machine is correct, and the API is comprehensive.

**Key strength:** The observer lifecycle is clean and the event-driven integration with Event Fabric is well-designed.

**Key risk:** The duplicate `GET /observers` endpoint in main.py needs to be resolved before frontend integration.
