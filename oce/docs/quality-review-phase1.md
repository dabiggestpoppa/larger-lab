# OCE Phase 1 — Quality Review

> **Reviewer:** AS (Assistant Manager)
> **Date:** 2026-05-16
> **Scope:** `oce/backend/main.py`, `oce/frontend/package.json`, `oce/README.md`, `oce/TEAM_TASKS.md`

## Summary

CC's Phase 1 scaffold is **solid and well-structured**. The FastAPI backend follows standard patterns, models are clean, and the WebSocket implementation is correct. All placeholder endpoints are properly marked with TODOs. No blockers found.

## What's Good ✅

1. **Clean separation of concerns** — Models, endpoints, and WebSocket manager are clearly separated with comment headers
2. **Pydantic models** — All request/response models properly typed with `BaseModel`
3. **CORS configured** — Correctly set up for Next.js frontend on port 3000
4. **WebSocket manager** — `ConnectionManager` class properly handles connect/disconnect/broadcast
5. **TODO markers** — Every placeholder endpoint clearly marks what needs SRRA-OPH integration
6. **Frontend package.json** — Correct dependencies (Next.js 15, React 19, Socket.IO client, Tailwind)

## Issues Found 🟡

### 1. Missing `ChatMessage` model usage
- **File:** `oce/backend/main.py`
- **Issue:** `ChatMessage` model is defined but never used in any endpoint
- **Severity:** Low — likely intended for future chat history feature
- **Recommendation:** Either use it in `/chat` response or remove until needed

### 2. Hardcoded timestamps in WebSocket heartbeat
- **File:** `oce/backend/main.py` line ~175
- **Issue:** `timestamp` is hardcoded to `"2026-05-16T16:00:00Z"` instead of using `datetime.utcnow().isoformat()`
- **Severity:** Low — cosmetic, but will confuse debugging
- **Recommendation:** Use `datetime.utcnow().isoformat() + "Z"`

### 3. No input validation on `limit` parameter
- **File:** `oce/backend/main.py` — `get_events()`
- **Issue:** `limit: int = 50` has no max bound — could return unlimited events
- **Severity:** Medium — potential DoS vector
- **Recommendation:** Add `limit: int = Query(50, ge=1, le=1000)`

### 4. No error handling in WebSocket
- **File:** `oce/backend/main.py` — `websocket_events()`
- **Issue:** Only catches `WebSocketDisconnect` — other exceptions will crash the connection silently
- **Severity:** Medium
- **Recommendation:** Add generic `except Exception` handler with logging

### 5. Frontend has no source files
- **File:** `oce/frontend/`
- **Issue:** Only `package.json` exists — no `pages/`, `app/`, or `src/` directory
- **Severity:** High — OC2 needs to build the UI but has no scaffold
- **Recommendation:** CC or OC2 should create minimal Next.js app structure

### 6. No requirements.txt for backend
- **File:** `oce/backend/`
- **Issue:** No `requirements.txt` or dependency spec for the FastAPI backend
- **Severity:** Medium — developers can't install dependencies
- **Recommendation:** Create `oce/backend/requirements.txt` with fastapi, uvicorn, pydantic

## Recommendations (Priority Order)

1. **Create `oce/backend/requirements.txt`** — fastapi, uvicorn, pydantic
2. **Create minimal frontend scaffold** — `oce/frontend/app/page.tsx`, `oce/frontend/app/layout.tsx`
3. **Add input validation** — Query parameter bounds on `limit`
4. **Add WebSocket error handling** — Generic exception handler
5. **Fix hardcoded timestamp** — Use `datetime.utcnow()`
6. **Remove or use `ChatMessage`** — Clean up unused model

## Verdict

**APPROVED for Phase 1 scaffold.** Issues are minor and don't block progress. CC should address #1 and #2 before OC2 begins frontend work. No re-review needed for scaffold changes — only when SRRA-OPH integration begins.
