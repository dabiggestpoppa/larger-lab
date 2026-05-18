# SW Dev Room — Project Board

> **Manager:** SW Dev Manager (sub-agent of OWL)
> **Last Updated:** 2026-05-18
> **Sprint:** Sprint 0 — UI Fixes & Stabilization

---

## 🔄 Current Sprint: Sprint 0 — UI Fixes & Stabilization

**Goal:** Fix known UI issues in the agent environment dashboard so it's stable and usable.

### Tasks

| # | Task | Assignee | Status | Notes |
|---|------|----------|--------|-------|
| 0.1 | Fix canvas rendering — rooms/agents not visible on load | sw-frontend-dev | 🔲 TODO | Canvas may not render until window resize; investigate `resize()` call timing |
| 0.2 | Fix agent movement via drag or click-to-move | sw-frontend-dev | 🔲 TODO | Currently only programmatic move; add UI interaction |
| 0.3 | Fix WebSocket reconnection state sync | sw-backend-dev | 🔲 TODO | After reconnect, world state may not re-sync properly |
| 0.4 | Fix room layout — grid overflow with many rooms | sw-frontend-dev | 🔲 TODO | 2-column grid doesn't scale; needs responsive layout |
| 0.5 | Fix activity log entries not showing for non-selected agents | sw-frontend-dev | 🔲 TODO | Activity log only updates for selected agent in some code paths |
| 0.6 | Add error handling for failed API calls in env-client.js | sw-frontend-dev | 🔲 TODO | fetch() calls have no `.catch()` — silent failures |
| 0.7 | Fix dashboard static file serving conflict | sw-backend-dev | 🔲 TODO | `express.static(dashboard)` before `express.static(public)` may shadow env assets |
| 0.8 | Add input sanitization for XSS prevention | sw-backend-dev | 🔲 TODO | `_escapeHtml` exists but not applied consistently in server-side message rendering |

---

## 📋 Backlog

### Features (from Software CEO direction — pending meditation)
- [ ] Agent-to-agent direct messaging UI
- [ ] Room creation/deletion from dashboard
- [ ] Agent capability management UI
- [ ] Real-time code execution panel (sandbox)
- [ ] Meditation room visualization
- [ ] Quant room — strategy/backtest dashboard
- [ ] Agent activity heatmap / timeline view
- [ ] Multi-user support (multiple dashboards, different views)
- [ ] Export world state as JSON
- [ ] Agent "memory" viewer panel

### Tech Debt
- [ ] Add unit tests for world-engine.js
- [ ] Add unit tests for room-manager.js
- [ ] Add integration tests for API endpoints
- [ ] Refactor env-client.js — split into smaller modules
- [ ] Add TypeScript types for WebSocket message protocol
- [ ] Add proper logging levels (currently uses custom logger)

---

## 📊 Resource Links

From `room-wikis/sw-dev-wiki.md`:
- **Design:** [designmd.sh](https://designmd.sh/), [Excalidraw](https://excalidraw.com/), [tldraw](https://tldraw.com/)
- **Dev Docs:** [roadmap.sh](https://roadmap.sh/), [devdocs.io](https://devdocs.io/), [learnxinyminutes.com](https://learnxinyminutes.com/)
- **Fork/White-label:** [12 Factor Agents](https://github.com/humanlayer/12-factor-agents), [Hello Agents](https://hello-agents.datawhale.cc/)
- **Free Media:** [Pixabay](https://pixabay.com/), [Mixkit](https://mixkit.co/)

---

## 🏗️ Architecture Notes

- **Port:** 9000
- **Stack:** Node.js + Express + WebSocket (ws) + Canvas API
- **Pattern:** Modular — rooms, agents, communication, sandbox are separate modules
- **World Engine:** 30 FPS tick loop, broadcasts state every 500ms
- **Frontend:** Vanilla JS (no framework), Canvas for world map, HTML/CSS for UI
- **Data:** JSON file-based persistence (rooms.json, agents.json)

---

## 📝 Sprint Retrospective (Template)

**Sprint:** 
**What went well:**
**What didn't go well:**
**Action items:**
