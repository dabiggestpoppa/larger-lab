# IACER Task Brief — REFINED — Agent Environment API Completion

> **From:** Quant Lab Manager (refined from OWL's original brief)
> **To:** Implementation Agent
> **Date:** 2026-05-18 08:00 EDT
> **Priority:** 🔴 #1 — MAD directive
> **Original:** `agent-environment/delegations/env-api-handoff.md`

---

## What Exists Today

The server (`server.js`) is fully functional with:
- Express HTTP API on port 9000
- WebSocket server at `/ws`
- Agent registry with JSON persistence
- Room management (4 rooms: meditation-room, quant-room, chat-room, war-room)
- World engine with 30 FPS tick loop
- Canvas dashboard visualization
- Seed demo (`tools/seed-demo.js`) that creates 5 fake agents

**The gap:** No agent currently calls the server. The API exists but there's no client SDK for agents to use.

---

## What to Build

### 1. Agent Client SDK (`src/agent-client.js`)

A Node.js module that sub-agents `require()` to interact with the environment server.

**API surface (simple, 6 functions):**

```javascript
const client = require('./src/agent-client');

// Connect + register (auto-generates ID, starts heartbeat)
const agent = await client.connect({ name: 'Manager', role: 'coordinator' });

// Move to a room (triggers WebSocket event → Canvas updates)
await client.moveTo('quant-room');

// Send message to current room
await client.say('Starting backtest on EUR/USD M5...');

// Update status (visible on dashboard)
await client.setStatus('working'); // 'idle' | 'working' | 'meditating' | 'error'

// Update activity (shown in activity log)
await client.setActivity('Running optimizer v4...');

// Disconnect (cleanup)
await client.disconnect();
```

**Internal design:**
- Uses `http` module (no external deps) for REST calls
- Maintains a local cache of agent state (id, name, room, status)
- Auto-heartbeat: pings server every 30s to keep session alive
- Graceful error handling: if server is down, queue operations and retry
- Event emitter pattern: `client.on('moved', fn)`, `client.on('error', fn)`

### 2. Server Hardening (`server.js` — additions, not rewrite)

Add to existing endpoints:
- **Input validation:** Reject invalid status values, empty strings, oversized payloads
- **CORS headers:** Allow cross-origin from any origin (agents may run on different ports)
- **Rate limiting:** Max 30 requests/second per agent ID
- **Better error responses:** Consistent `{ success: false, error: 'message', code: 'ERROR_CODE' }` format
- **Agent heartbeat endpoint:** `POST /api/agents/:id/heartbeat` — keeps session alive
- **Agent disconnect endpoint:** `POST /api/agents/:id/disconnect` — clean session teardown

### 3. Real Room Registry (`data/rooms.json`)

Replace the 4 demo rooms with the actual operational rooms:

```json
{
  "lobby": { "id": "lobby", "name": "Lobby", "description": "Entry point for all agents. New agents spawn here.", "persistent": true },
  "lab-room": { "id": "lab-room", "name": "Lab Room", "description": "Quant Lab — strategy work, backtesting, analysis.", "persistent": true },
  "farm-room": { "id": "farm-room", "name": "Farm Room", "description": "Content Farm — content creation, marketing, publishing.", "persistent": true },
  "meditation-room": { "id": "meditation-room", "name": "Meditation Room", "description": "IACER thinking space. Deep analysis and reflection.", "persistent": true },
  "war-room": { "id": "war-room", "name": "War Room", "description": "Mission command — active operations and debugging.", "persistent": true }
}
```

### 4. Updated Seed Demo (`tools/seed-demo.js`)

Update to use real room IDs and real agent names/roles:
- OWL → Lobby (operator)
- CC → War Room (overseer)
- AS → Meditation Room (assistant)
- PM → Lab Room (debugger)
- RL → Lab Room (researcher)

### 5. API Documentation (`docs/API.md`)

Full API reference for agents:
- All endpoints with request/response examples
- Error codes reference
- Client SDK usage guide
- WebSocket message types

### 6. Test Script (`tools/test-agent-lifecycle.js`)

End-to-end test that:
1. Checks server health
2. Registers a test agent
3. Moves it through 3 rooms
4. Sends messages in each room
5. Updates status and activity
6. Verifies world state reflects all changes
7. Disconnects cleanly
8. Reports pass/fail for each step

---

## File Manifest

| File | Action | Purpose |
|------|--------|---------|
| `src/agent-client.js` | **CREATE** | Client SDK for agents |
| `src/server.js` | **MODIFY** | Add validation, CORS, rate limiting, heartbeat, disconnect |
| `data/rooms.json` | **REPLACE** | Real room registry |
| `tools/seed-demo.js` | **MODIFY** | Use real rooms + agent names |
| `docs/API.md` | **CREATE** | API documentation |
| `tools/test-agent-lifecycle.js` | **CREATE** | E2E test script |

---

## Constraints

- **No new npm dependencies** for the client SDK (use built-in `http` module)
- **Backward compatible** — all existing endpoints must still work
- **Don't break the Canvas dashboard** — WebSocket events must remain compatible
- **Server stays on port 9000**
- **All new code must have JSDoc comments**

---

## Success Criteria

1. `node tools/test-agent-lifecycle.js` passes all 8 steps
2. Agent appears on Canvas dashboard in correct room after `connect()`
3. Agent avatar moves between rooms in real-time on Canvas
4. Status changes visible on dashboard within 1 second
5. Activity messages appear in activity log
6. Server handles malformed requests gracefully (no crashes)
7. `docs/API.md` documents all endpoints with examples

---

## Execution Order

1. Read existing `server.js`, `agent-registry.js`, `world-engine.js` to understand current code
2. Create `src/agent-client.js` (the SDK)
3. Modify `src/server.js` (hardening — add, don't rewrite)
4. Replace `data/rooms.json` (real rooms)
5. Update `tools/seed-demo.js` (real data)
6. Create `tools/test-agent-lifecycle.js` (E2E test)
7. Create `docs/API.md` (documentation)
8. Run test script and fix any failures
9. Report results

---

*End of refined brief — Implementation agent should execute in order*
