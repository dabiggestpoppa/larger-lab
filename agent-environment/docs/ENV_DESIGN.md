# Virtual Agent Environment v2 — Design Document

> **Date:** 2026-05-18 | **Version:** 2.0.0 | **Author:** Environment Builder (Sub-Agent)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Dashboard)                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ Sidebar   │  │ World    │  │  Agent Detail Panel    │ │
│  │ - Rooms   │  │ Canvas   │  │  - Status              │ │
│  │ - Agents  │  │ (agents  │  │  - Activity            │ │
│  │           │  │  moving) │  │  - Capabilities        │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
│                         ▲                               │
│                    WebSocket                             │
│                         │                               │
├─────────────────────────┼───────────────────────────────┤
│                    Node.js Server :9000                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ World    │  │ Agent    │  │  Activity             │ │
│  │ Engine   │◄─┤ Visual   │◄─┤  Tracker              │ │
│  │          │  │ State    │  │                       │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
│       ▲              ▲                ▲                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ Room     │  │ Agent    │  │  Message              │ │
│  │ Visual   │  │ Registry │  │  Bus                  │ │
│  │ Manager  │  │          │  │                       │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| World Engine | `src/world-engine.js` | Main update loop, ties all visual systems together |
| Agent Visual | `src/agent-visual.js` | Agent visual state (position, color, activity, avatar) |
| Room Visual | `src/room-visual.js` | Room layout, agent positioning within rooms |
| Activity Tracker | `src/activity-tracker.js` | Tracks agent activity, broadcasts changes |
| Env Renderer | `public/js/env-renderer.js` | Canvas rendering of the world |
| Env Client | `public/js/env-client.js` | WebSocket client, UI interactions |
| World Dashboard | `public/index.html` | New visual dashboard (replaces old dashboard) |

---

## 2. Visual Design

### World Map View (ASCII Mockup)

```
┌─────────────────────────────────────────────────────────────┐
│  🦉 Agent Environment v2                    [●] Connected   │
├────────────┬─────────────────────────────────┬──────────────┤
│  ROOMS     │         WORLD MAP               │  AGENT INFO  │
│            │                                 │              │
│ 🧘 Medit.  │  ┌──────────┐  ┌──────────┐    │  Name: OWL   │
│ 📊 Quant   │  │🧘        │  │📊        │    │  Role: Op    │
│ 💬 Chat    │  │  ●OWL    │   │  ●PM     │    │  Room: Chat  │
│ ⚔️ War     │  │  ●AS     │   │          │    │  Status: ✓   │
│            │  └──────────┘  └──────────┘    │              │
│  AGENTS    │                                 │  Activity:   │
│ ● OWL      │  ┌──────────┐  ┌──────────┐    │  ████████░░  │
│ ● PM       │  │💬        │  │⚔️        │    │              │
│ ● AS       │  │  ●CC     │  │  ●RL     │    │  Recent:     │
│ ● CC       │  │          │  │          │    │  "Running.." │
│ ● RL       │  └──────────┘  └──────────┘    │              │
│            │                                 │              │
│            │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │              │
│            │  Communication lines:           │              │
│            │  OWL ──── CC (chat)            │              │
│            │  PM ───── RL (task)            │              │
├────────────┴─────────────────────────────────┴──────────────┤
│  [World] [Chat] [Agents] [Sandbox]        System: 3m up    │
└─────────────────────────────────────────────────────────────┘
```

### Agent Avatar Design

Each agent is a colored circle with:
- **Label**: Agent name (truncated)
- **Color**: Unique per agent (from palette)
- **Pulse ring**: When active/working
- **Status dot**: Green = online, Gray = offline, Yellow = idle

```
  ╭──────╮
  │ ●OWL │  ← Name label
  │  ◉   │  ← Avatar (colored circle)
  │  ╲   │  ← Activity pulse ring (animated)
  ╰──────╯
  Color: #6c5ce7 (purple for OWL)
```

### Room Design

Each room is a rounded rectangle in the canvas:
- **Header**: Room name + icon
- **Body**: Agent avatars positioned inside
- **Border color**: Matches room theme
- **Agent count badge**: Top-right corner

---

## 3. Data Model

### Agent State
```json
{
  "id": "a1b2c3d4",
  "name": "OWL",
  "role": "operator",
  "color": "#6c5ce7",
  "currentRoom": "chat-room",
  "status": "active",
  "online": true,
  "position": { "x": 350, "y": 200 },
  "activity": {
    "level": 0.8,
    "lastAction": "Running strategy backtest",
    "lastActionTime": "2026-05-18T01:55:00Z"
  },
  "capabilities": ["communicate", "read_files"],
  "createdAt": "2026-05-18T01:00:00Z"
}
```

### Room State
```json
{
  "id": "chat-room",
  "name": "Chat Room",
  "icon": "💬",
  "color": "#00cec9",
  "position": { "x": 300, "y": 100 },
  "size": { "w": 200, "h": 150 },
  "agents": ["a1b2c3d4", "e5f6g7h8"],
  "agentCount": 2
}
```

### World State
```json
{
  "rooms": [...],
  "agents": [...],
  "connections": [
    { "from": "OWL", "to": "CC", "type": "chat", "active": true }
  ],
  "timestamp": "2026-05-18T01:55:00Z"
}
```

### Message State (extended)
```json
{
  "id": "msg_123",
  "from": "OWL",
  "to": "CC",
  "type": "chat",
  "content": "Hello!",
  "roomId": "chat-room",
  "timestamp": "2026-05-18T01:55:00Z"
}
```

---

## 4. API Endpoints

### New Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/world` | Full world state (rooms + agents + connections) |
| GET | `/api/room/:id` | Room state with agents and messages |
| POST | `/api/agent/:id/move` | Move agent to a room |
| POST | `/api/agent/:id/status` | Update agent status (active/idle/working) |
| POST | `/api/agent/:id/activity` | Update agent activity level and last action |
| GET | `/api/connections` | Active communication connections |

### Existing Endpoints (unchanged)

All existing endpoints from v1 remain functional:
- `/health`, `/api/rooms`, `/api/agents`, `/api/rooms/:id/messages`, etc.

---

## 5. WebSocket Events

### Server → Client

| Event | Data | Purpose |
|-------|------|---------|
| `world.state` | Full world state | Initial sync + periodic updates |
| `agent.moved` | `{ agentId, fromRoom, toRoom }` | Agent changed rooms |
| `agent.status` | `{ agentId, status }` | Agent status changed |
| `agent.activity` | `{ agentId, level, lastAction }` | Agent activity update |
| `agent.joined` | `{ agentId, agent }` | New agent registered |
| `agent.left` | `{ agentId }` | Agent disconnected |
| `message.sent` | `{ from, to, roomId, content, type }` | New message (shows connection line) |
| `connection.active` | `{ from, to, type }` | Communication line activated |
| `connection.idle` | `{ from, to }` | Communication line went idle |

### Client → Server

| Event | Data | Purpose |
|-------|------|---------|
| `auth` | `{ agentId }` | Dashboard authentication |
| `request-world` | — | Request full world state |
| `move-agent` | `{ agentId, roomId }` | Move agent to room |
| `set-agent-status` | `{ agentId, status }` | Update agent status |
| `simulate-activity` | `{ agentId }` | Trigger demo activity |

---

## 6. Rendering Approach

### Canvas-Based World Map
- HTML5 Canvas for the world map area
- Rooms drawn as rounded rectangles
- Agents drawn as colored circles with labels
- Animation loop at 30fps for smooth movement
- Agents interpolate positions when moving between rooms

### DOM-Based UI
- Sidebar: Room list + Agent list (DOM elements)
- Right panel: Agent detail (DOM elements)
- Tabs: World Map / Chat / Agents / Sandbox
- Communication lines drawn on canvas overlay

### Color Palette
| Agent | Color |
|-------|-------|
| OWL | #6c5ce7 (purple) |
| CC | #e17055 (red) |
| AS | #00cec9 (teal) |
| PM | #fd79a8 (pink) |
| RL | #74b9ff (blue) |

| Room | Color |
|------|-------|
| meditation-room | #6c5ce7 |
| quant-room | #00b894 |
| chat-room | #00cec9 |
| war-room | #e17055 |

---

## 7. Demo Data

5 agents pre-registered:
1. **OWL** (operator) → chat-room
2. **CC** (overseer) → war-room
3. **AS** (assistant) → meditation-room
4. **PM** (debugger) → quant-room
5. **RL** (researcher) → chat-room

Simulated behaviors:
- Agents randomly move between rooms every 10-30 seconds
- Activity pulses when agents "work"
- Communication lines flash when messages are sent

---

## 8. File Structure

```
agent-environment/
├── config/
│   └── environment.yaml          (existing)
├── docs/
│   ├── ENV_DESIGN.md             ← this file
│   └── BUILD_REPORT.md           ← build report
├── public/
│   ├── index.html                ← NEW visual dashboard
│   ├── css/
│   │   └── env.css               ← NEW visual styles
│   └── js/
│       ├── env-renderer.js       ← NEW canvas renderer
│       └── env-client.js         ← NEW WS client
├── src/
│   ├── server.js                 (existing, extended)
│   ├── world-engine.js           ← NEW
│   ├── agent-visual.js           ← NEW
│   ├── room-visual.js            ← NEW
│   ├── activity-tracker.js       ← NEW
│   ├── agents/                   (existing)
│   ├── rooms/                    (existing)
│   ├── communication/            (existing)
│   ├── sandbox/                  (existing)
│   └── utils/                    (existing)
└── package.json                  (existing)
```

---

## 9. Implementation Order

1. ✅ Design document
2. `agent-visual.js` — Agent visual state management
3. `room-visual.js` — Room layout and positioning
4. `activity-tracker.js` — Activity tracking
5. `world-engine.js` — Main game loop
6. Extend `server.js` — New API endpoints + WS events
7. `public/css/env.css` — Visual styles
8. `public/js/env-renderer.js` — Canvas rendering
9. `public/js/env-client.js` — WebSocket client
10. `public/index.html` — New dashboard
11. Demo data + testing
12. Build report
