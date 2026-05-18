# Agent Virtual Environment — API Documentation

> **Version:** 2.0
> **Base URL:** `http://localhost:9000`
> **WebSocket:** `ws://localhost:9000/ws`

---

## Table of Contents

1. [REST API](#rest-api)
2. [Client SDK](#client-sdk)
3. [WebSocket Protocol](#websocket-protocol)
4. [Error Codes](#error-codes)
5. [Data Models](#data-models)

---

## REST API

### Health

#### `GET /health`

Check server status.

**Response:**
```json
{
  "status": "ok",
  "uptime": 1234.56,
  "timestamp": "2026-05-18T08:00:00.000Z",
  "rooms": 5,
  "agents": 5,
  "online": 3
}
```

---

### Agents

#### `GET /api/agents`

List all agents. Optional filters: `?room=lab-room&status=working`.

**Response:**
```json
{
  "success": true,
  "agents": [
    {
      "id": "abc12345",
      "name": "Manager",
      "role": "coordinator",
      "capabilities": ["communicate", "read_files"],
      "currentRoom": "lab-room",
      "status": "working",
      "createdAt": "2026-05-18T08:00:00.000Z",
      "lastActive": "2026-05-18T08:05:00.000Z",
      "metadata": {}
    }
  ]
}
```

#### `POST /api/agents`

Register a new agent.

**Request:**
```json
{
  "name": "Manager",
  "role": "coordinator",
  "capabilities": ["communicate", "read_files", "write_files"]
}
```

**Response (201):**
```json
{
  "success": true,
  "agent": {
    "id": "abc12345",
    "name": "Manager",
    "role": "coordinator",
    "capabilities": ["communicate", "read_files", "write_files"],
    "currentRoom": "meditation-room",
    "status": "meditating",
    "createdAt": "2026-05-18T08:00:00.000Z",
    "lastActive": "2026-05-18T08:00:00.000Z",
    "metadata": {}
  }
}
```

#### `GET /api/agents/:id`

Get a specific agent by ID.

**Response:**
```json
{
  "success": true,
  "agent": { ... },
  "online": true
}
```

#### `POST /api/agents/:id/move`

Move an agent to a different room. Triggers WebSocket `agent-moved` event.

**Request:**
```json
{
  "roomId": "lab-room"
}
```

**Response:**
```json
{
  "success": true,
  "agent": {
    "id": "abc12345",
    "currentRoom": "lab-room",
    "status": "active",
    ...
  }
}
```

#### `POST /api/agents/:id/status`

Update agent status. Triggers WebSocket `agent.status` event.

**Request:**
```json
{
  "status": "working"
}
```

**Valid statuses:** `idle`, `working`, `meditating`, `active`, `error`, `offline`

#### `POST /api/agents/:id/activity`

Update agent activity. Shown in the activity log on the dashboard.

**Request:**
```json
{
  "action": "Running backtest on EUR/USD M5...",
  "level": 0.8
}
```

- `action` (string, required): Description of current activity
- `level` (number, 0.0-1.0): Activity intensity

#### `POST /api/agents/:id/heartbeat`

Keep agent session alive. Called automatically by the client SDK every 30s.

**Response:**
```json
{
  "success": true,
  "agent": { ... }
}
```

#### `POST /api/agents/:id/disconnect`

Clean session teardown. Sets agent status to `offline` and ends session.

**Response:**
```json
{
  "success": true
}
```

---

### Rooms

#### `GET /api/rooms`

List all rooms.

**Response:**
```json
{
  "success": true,
  "rooms": [
    {
      "id": "lobby",
      "name": "Lobby",
      "description": "Entry point for all agents.",
      "agents": [],
      "persistent": true,
      "createdAt": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

#### `GET /api/rooms/:id`

Get room details with recent messages.

**Response:**
```json
{
  "success": true,
  "room": { ... },
  "messages": [
    {
      "id": "msg-1",
      "from": "abc12345",
      "type": "chat",
      "content": "Hello!",
      "timestamp": "2026-05-18T08:00:00.000Z"
    }
  ]
}
```

#### `POST /api/rooms/:id/messages`

Post a message to a room.

**Request:**
```json
{
  "agentId": "abc12345",
  "text": "Starting backtest...",
  "type": "task"
}
```

**Valid message types:** `chat`, `system`, `task`

**Max message length:** 4096 characters

#### `POST /api/rooms/:id/join`

Join an agent to a room.

**Request:**
```json
{
  "agentId": "abc12345"
}
```

#### `POST /api/rooms/:id/leave`

Remove an agent from a room.

**Request:**
```json
{
  "agentId": "abc12345"
}
```

---

### World State

#### `GET /api/world`

Get the full world state (rooms, agents, connections, recent activity).

**Response:**
```json
{
  "success": true,
  "rooms": [
    {
      "id": "lab-room",
      "name": "Lab Room",
      "icon": "🧪",
      "color": "#0984e3",
      "position": { "x": 300, "y": 100 },
      "size": { "w": 260, "h": 180 },
      "agentCount": 2,
      "agents": [
        {
          "id": "abc12345",
          "name": "Manager",
          "role": "coordinator",
          "color": "#6c5ce7",
          "status": "working",
          "online": true,
          "activity": { "level": 0.8, "lastAction": "Running backtest..." },
          "avatar": { "label": "M", "emoji": "🤖", "radius": 18 }
        }
      ]
    }
  ],
  "agents": [ ... ],
  "connections": [ ... ],
  "recentActivity": [ ... ],
  "timestamp": "2026-05-18T08:00:00.000Z"
}
```

---

## Client SDK

The Agent Client SDK (`src/agent-client.js`) provides a simple Node.js interface for agents to interact with the environment server.

### Installation

```javascript
const client = require('./src/agent-client');
```

No external dependencies — uses only built-in Node.js modules.

### Quick Start

```javascript
const client = require('./src/agent-client');

async function main() {
  // 1. Connect and register
  const agent = await client.connect({
    name: 'Manager',
    role: 'coordinator',
    room: 'lobby',
  });
  console.log(`Registered as ${agent.name} (${agent.id})`);

  // 2. Move to a room
  await client.moveTo('lab-room');

  // 3. Send a message
  await client.say('Starting backtest on EUR/USD M5...', 'task');

  // 4. Update status
  await client.setStatus('working');

  // 5. Update activity
  await client.setActivity('Running optimizer v4...', 0.8);

  // 6. Check world state
  const world = await client.getWorld();
  console.log(`${world.agents.length} agents online`);

  // 7. Disconnect when done
  await client.disconnect();
}

main().catch(console.error);
```

### API Reference

#### `connect(opts)`

Connect to the server and register as a new agent.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | **required** | Agent display name |
| `role` | string | `'agent'` | Agent role |
| `capabilities` | string[] | `['communicate']` | Agent capabilities |
| `room` | string | `'lobby'` | Initial room |
| `host` | string | `'localhost'` | Server hostname |
| `port` | number | `9000` | Server port |

**Returns:** `Promise<agent>` — The registered agent object

#### `moveTo(roomId)`

Move the agent to a different room. Triggers real-time Canvas update.

**Returns:** `Promise<agent>`

#### `say(text, type='chat')`

Send a message to the current room.

**Returns:** `Promise<message>`

#### `setStatus(status)`

Update agent status. Valid: `idle`, `working`, `meditating`, `active`, `error`.

**Returns:** `Promise<agent>`

#### `setActivity(action, level=0.5)`

Update activity description. Level is 0.0-1.0.

**Returns:** `Promise<{ success: true }>`

#### `getWorld()`

Fetch full world state.

**Returns:** `Promise<worldState>`

#### `whoami()`

Get local agent state (synchronous).

**Returns:** `{ id, name, role, room, status, connected }`

#### `disconnect()`

Clean disconnect. Stops heartbeat, sets status to `offline`.

**Returns:** `Promise<void>`

#### `on(event, fn)`

Register event listener. Events: `connected`, `moved`, `message-sent`, `status-changed`, `activity-updated`, `heartbeat`, `queued`, `dequeued`, `error`, `disconnected`.

#### `off(event, fn)`

Remove event listener.

---

## WebSocket Protocol

Connect to `ws://localhost:9000/ws`.

### Client → Server Messages

| Type | Payload | Description |
|------|---------|-------------|
| `auth` | `{ agentId, roomId }` | Authenticate as an agent |
| `join-room` | `{ roomId }` | Join a room via WS |
| `room-message` | `{ content, messageType }` | Send message to current room |
| `direct-message` | `{ to, content, messageType }` | Send direct message |
| `request-world` | `{}` | Request full world state |
| `move-agent` | `{ agentId, roomId }` | Move an agent |
| `set-agent-status` | `{ agentId, status }` | Update agent status |
| `simulate-activity` | `{ agentId }` | Simulate random activity |
| `run-code` | `{ language, code, timeout }` | Run code in sandbox |

### Server → Client Events

| Event | Payload | Description |
|-------|---------|-------------|
| `auth-ok` | `{ agentId }` | Authentication confirmed |
| `room-joined` | `{ roomId }` | Room join confirmed |
| `world.state` | `{ rooms, agents, connections, recentActivity, timestamp }` | Full world state (broadcast every 500ms) |
| `agent.joined` | `{ agentId, agent }` | New agent registered |
| `agent.moved` | `{ agentId, fromRoom, toRoom }` | Agent moved rooms |
| `agent.status` | `{ agentId, status }` | Agent status changed |
| `agent.left` | `{ agentId }` | Agent disconnected |
| `error` | `{ error }` | Error occurred |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AGENT_NOT_FOUND` | 404 | Agent ID not in registry |
| `INVALID_NAME` | 400 | Agent name missing or too long |
| `INVALID_ROOM_ID` | 400 | Room ID missing or invalid |
| `INVALID_STATUS` | 400 | Status not in valid set |
| `INVALID_TEXT` | 400 | Message text missing or too long |
| `INVALID_TYPE` | 400 | Message type not in valid set |
| `INVALID_ACTIVITY` | 400 | Activity action empty |
| `INVALID_AGENT_ID` | 400 | agentId missing in request |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests (>30/sec) |
| `REGISTRATION_FAILED` | 400 | Agent registration failed |
| `MOVE_FAILED` | 400 | Room move failed |
| `MESSAGE_FAILED` | 400 | Message post failed |
| `HTTP_ERROR` | * | Non-2xx HTTP response |
| `TIMEOUT` | — | Request timed out |
| `NETWORK_ERROR` | — | Connection refused or network error |

---

## Data Models

### Agent

```typescript
{
  id: string;             // 8-char UUID slice
  name: string;           // Display name (max 64 chars)
  role: string;           // e.g., 'operator', 'researcher'
  capabilities: string[]; // e.g., ['communicate', 'read_files']
  currentRoom: string;    // Room ID
  status: string;         // 'idle' | 'working' | 'meditating' | 'active' | 'error' | 'offline'
  createdAt: string;      // ISO 8601 timestamp
  lastActive: string;     // ISO 8601 timestamp
  metadata: object;       // Custom metadata
}
```

### Room

```typescript
{
  id: string;          // e.g., 'lab-room'
  name: string;        // Display name
  description: string; // Room description
  agents: string[];    // Agent IDs currently in room
  persistent: boolean; // Survives server restart
  createdAt: string;   // ISO 8601 timestamp
}
```

### Message

```typescript
{
  id: string;        // Message UUID
  from: string;      // Sender agent ID
  type: string;      // 'chat' | 'system' | 'task'
  content: string;   // Message text (max 4096 chars)
  timestamp: string; // ISO 8601 timestamp
}
```

---

*API Documentation — Agent Virtual Environment v2.0 — 2026-05-18*
