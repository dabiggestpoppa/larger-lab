# IACER Task Brief — Agent Environment API Completion

> **From:** OWL (Orchestrator)
> **To:** Quant Lab Manager (for refinement → delegation)
> **Date:** 2026-05-18 08:00 EDT
> **Priority:** 🔴 #1 — MAD directive
> **Soft Coding Protocol:** Manager refines this brief before passing to execution agent

---

## I — INTENT

**What MAD wants:** Agents in the virtual environment should move autonomously. Right now the visualization exists (Canvas, WebSocket, rooms, agents rendered) but there's no API client layer that lets actual sub-agents (Manager, Researcher, Optimizer, etc.) call the server to register themselves, move between rooms, send messages, and update their status in real-time.

**The gap:** The server has endpoints (`POST /api/agents`, `POST /api/agents/:id/move`, `POST /api/agents/:id/status`, `POST /api/agents/:id/activity`) but NO agent currently calls them. The demo uses `seed-demo.js` with fake data. Real agents don't know the server exists.

**The goal:** Build the client-side SDK + server enhancements so that when OWL spawns a sub-agent, that agent can:
1. Register itself with the environment server
2. Move between rooms (Lab Room, Farm Room, Meditation Room, etc.)
3. Send messages to room chat
4. Update its status (active/idle/working)
5. Report activity (what it's currently doing)

---

## A — ABSTRACTION

**Current state:**
- Server: `agent-environment/src/server.js` — Express + WebSocket, port 9000
- API: 5 new endpoints for world state, agent CRUD, movement, status, activity
- Visualization: Canvas rendering with real-time WebSocket updates
- Data: In-memory world state + JSON file persistence for agent registry
- Demo: `tools/seed-demo.js` creates 5 fake agents

**What needs to be built:**
1. **Agent Client SDK** (`src/agent-client.js`) — A Node.js module that sub-agents can `require()` to interact with the environment server. Simple API: `client.register(name, room)`, `client.moveTo(roomId)`, `client.sendMessage(roomId, text)`, `client.setStatus(status)`, `client.setActivity(text)`, `client.disconnect()`
2. **Server API hardening** — The existing endpoints need: input validation, error handling, CORS for cross-origin, heartbeat/health endpoint for agents
3. **Agent lifecycle hooks** — When OWL spawns a sub-agent, the agent auto-registers. When it completes, it updates status to "idle" and eventually disconnects
4. **Room registry** — The server needs to know about all active rooms (Lab Room, Farm Room, Meditation Room, etc.) not just the 4 default demo rooms
5. **Status dashboard** — The existing dashboard at `http://localhost:9000` should show real agents, not just demo data

**What this is NOT:**
- This is NOT rebuilding the visualization (that's done)
- This is NOT building a new server (Express is fine)
- This is NOT a browser-based feature (agents call from Node.js/terminal)
- This is NOT about the USB/local server planning (that's phase 2)

---

## C — CONTEXT

**Key files:**
- `agent-environment/src/server.js` — Main server (Express + WS)
- `agent-environment/src/world-engine.js` — World state management
- `agent-environment/src/agent-visual.js` — Agent state
- `agent-environment/src/room-visual.js` — Room layout
- `agent-environment/src/activity-tracker.js` — Activity tracking
- `agent-environment/public/js/env-client.js` — Browser WebSocket client
- `agent-environment/public/js/env-renderer.js` — Canvas renderer
- `agent-environment/tools/seed-demo.js` — Demo data seeder
- `agent-environment/data/agents.json` — Agent registry (persisted)
- `agent-environment/data/rooms.json` — Room registry
- `agent-environment/config/environment.yaml` — Config

**Existing API endpoints (server):**
- `GET /api/world` — Full world state
- `POST /api/agents/:id/move` — Move agent to room
- `POST /api/agents/:id/status` — Update status
- `POST /api/agents/:id/activity` — Update activity
- `GET /api/connections` — Active connections

**Active rooms that should exist:**
- Lab Room (quant-lab)
- Farm Room (content-farm)
- Meditation Room (meditation)
- General / Lobby
- (More can be added dynamically)

**Related systems:**
- OpenClaw gateway on port 18790 — sub-agents run under this
- OWL spawns sub-agents via `sessions_spawn`
- Sub-agents are Node.js processes that could `require()` the client SDK

**Constraints:**
- Server must stay on port 9000
- Must not break existing visualization
- Must not break existing WebSocket events
- Client SDK must be simple (5-6 functions max)
- All changes must be backward compatible

---

## E — EXPECTATIONS

**Deliverables:**
1. `agent-environment/src/agent-client.js` — Node.js client SDK for agents
2. Updated `agent-environment/src/server.js` — Hardened API (validation, errors, CORS)
3. Updated `agent-environment/data/rooms.json` — Real room registry (Lab, Farm, Meditation, Lobby)
4. Updated `agent-environment/tools/seed-demo.js` — Seed real rooms + real agent names
5. `agent-environment/docs/API.md` — API documentation for agents
6. Test script `agent-environment/tools/test-agent-lifecycle.js` — Registers agent, moves rooms, sends messages, updates status, disconnects

**Success criteria:**
- A sub-agent can `require('./src/agent-client')` and register itself in <10 lines of code
- Agent appears on the Canvas dashboard in the correct room
- Agent can move between rooms and the visualization updates in real-time
- Agent status changes (active/idle/working) are visible on dashboard
- Agent activity messages appear in the activity log
- All existing endpoints still work
- Dashboard at http://localhost:9000 shows real agents (not just demo data)

**Quality:**
- All new code must have comments
- Error handling on every API endpoint
- Input validation on every POST
- Graceful degradation (if server is down, client doesn't crash)

---

## R — RESULTS

**What "done" looks like:**
1. OWL spawns a sub-agent → sub-agent registers with environment server → agent appears on Canvas in the Lobby
2. Sub-agent gets assigned to Lab Room → calls `client.moveTo('lab-room')` → agent avatar moves to Lab Room on Canvas
3. Sub-agent starts working → calls `client.setStatus('working')` + `client.setActivity('Running backtest...')` → status indicator changes, activity log updates
4. Sub-agent finishes → calls `client.setStatus('idle')` → status changes to idle
5. MAD opens `http://localhost:9000` → sees all active agents in their rooms with correct statuses

**Impact:** This is the foundation for the entire agent environment. Without autonomous agent movement, the visualization is just a pretty demo. With it, the environment becomes a real operational dashboard for the cognitive field.

**Priority:** This is MAD's #1 priority. Everything else (cost model validation, conversion pipeline, content farm) is blocked until agents can operate autonomously in the environment.

---

*End of IACER brief — Manager should refine before delegating to execution agent*
