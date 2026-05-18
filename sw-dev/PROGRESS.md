# SW Dev Room — Progress Tracker

> **Manager:** SW Dev Manager
> **Last Updated:** 2026-05-18 16:44 EDT

## Status: 🟢 Active

### Backend Fixes (Sub-agent: backend-dev)
| # | Fix | Status | Time |
|---|-----|--------|------|
| 1 | WebSocket reconnection state sync | ✅ Done | 16:44 |
| 2 | Static file serving order (public before dashboard) | ✅ Done | 16:44 |
| 3 | XSS prevention — escapeHtml utility + apply to WS messages | ✅ Done | 16:45 |
| 4 | Async error handling (sandbox endpoints + run-code WS) | ✅ Done | 16:45 |
| 5 | Graceful shutdown (SIGTERM/SIGINT + uncaughtException) | ✅ Done | 16:45 |
| 6 | Global Express error handler + 404 handler | ✅ Done | 16:45 |

### Fix Details

**Fix #1 — WebSocket Reconnection State Sync**
- **Root cause:** On WS reconnect, client only received `auth-ok` with no world state
- **Fix:** After auth, server now sends full `world.state` + `room.history` for the agent's current room
- **File:** `server.js` WS `auth` handler

**Fix #2 — Static File Serving Order**
- **Root cause:** `express.static(dashboard)` mounted before `express.static(public)`, shadowing public assets
- **Fix:** Reversed order — `public` now takes priority over `dashboard`
- **File:** `server.js` static middleware section

**Fix #3 — XSS Prevention**
- **Root cause:** No HTML escaping anywhere; user content (messages, names) sent raw to clients
- **Fix:** Created `src/utils/escape.js` with `escapeHtml()` and `escapeObject()`. Applied to WS `room-message` and `direct-message` handlers
- **Files:** `src/utils/escape.js` (new), `server.js` WS handlers

**Fix #4 — Async Error Handling**
- **Root cause:** Sandbox API routes and `run-code` WS handler had no try/catch; unhandled rejections could crash server
- **Fix:** Wrapped all async route handlers in try/catch; added `.catch()` to promise-based sandbox calls in WS handler
- **File:** `server.js` sandbox routes + `run-code` case

**Fix #5 — Graceful Shutdown**
- **Root cause:** Shutdown handlers were basic with no timeout, no client notification, no error handling
- **Fix:** Created `gracefulShutdown()` function with: shutdown guard, client notification, 10s timeout, error logging, `uncaughtException`/`unhandledRejection` handlers
- **File:** `server.js` process handlers

**Fix #6 — Global Error Middleware**
- **Root cause:** No catch-all error middleware; unhandled errors in routes could crash the server
- **Fix:** Added Express error handler middleware + 404 handler at end of middleware chain
- **File:** `server.js`

### Sprint 0 — UI Fixes & Stabilization
- [x] Project board created
- [x] Wiki reviewed
- [x] Codebase analyzed
- [x] Frontend sub-agent spawned (sw-frontend-dev)
- [x] Backend fixes complete (backend-dev)
- [ ] Sprint 0 tasks in progress
