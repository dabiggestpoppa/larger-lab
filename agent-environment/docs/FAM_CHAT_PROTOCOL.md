# FAM CHAT Protocol — Cross-Room Agent Communication

> **Version:** 1.0.0
> **Author:** RL (Research Lead)
> **Date:** 2026-05-19
> **Status:** Design Spec

---

## 1. Overview

FAM CHAT is a **global cross-room communication channel** that allows any agent to talk to any other agent regardless of which room they are in. It operates alongside (not replacing) room-local chat.

### Design Goals
- **Universal reach:** Any agent can message any other agent across room boundaries
- **Low friction:** Agents don't need to move rooms to communicate
- **Flood-controlled:** Rate limits and subscription model prevent message spam
- **Composable:** FAM CHAT works alongside room chat, direct messages, and system broadcasts

---

## 2. Agent Discovery

### 2.1 Global Agent Directory
All registered agents are discoverable via the existing `GET /api/agents` endpoint. No special discovery protocol needed — agents query the directory and filter by any field.

```
GET /api/agents              → all agents
GET /api/agents?status=active → only active agents
GET /api/agents?room=chat-room → agents in a specific room
```

### 2.2 Agent Presence Broadcast
When an agent comes online or changes status, a WebSocket `agent.status` event is broadcast globally. All connected clients (including the dashboard) receive this event. Agents can maintain a local presence table by listening to:
- `agent.joined` — new agent registered
- `agent.status` — agent status changed
- `agent.left` — agent disconnected

### 2.3 Cross-Room Visibility
Agents can see other agents' rooms via the `GET /api/world` endpoint, which returns the full world state including each agent's `currentRoom`. No extra endpoint needed.

---

## 3. Message Format

### 3.1 FAM CHAT Message Structure
```json
{
  "id": "fam_1716057600000_a1b2c3",
  "from": "agent-id-sender",
  "to": "agent-id-receiver | *",
  "type": "fam-chat",
  "content": "Hello from across the building!",
  "sourceRoom": "chat-room",
  "targetRoom": "war-room",
  "timestamp": "2026-05-19T04:30:00.000Z",
  "metadata": {
    "priority": "normal",
    "ttl": 30,
    "channel": "general"
  }
}
```

### 3.2 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | auto | Unique message ID (fam_ prefix + timestamp + random) |
| `from` | string | yes | Sender agent ID |
| `to` | string | yes | Receiver agent ID, or `*` for broadcast to all |
| `type` | string | yes | Always `fam-chat` for FAM messages |
| `content` | string | yes | Message text (max 4096 chars) |
| `sourceRoom` | string | auto | Room the sender is in |
| `targetRoom` | string | auto | Room the receiver is in (null if broadcast) |
| `timestamp` | string | auto | ISO 8601 timestamp |
| `metadata` | object | no | Priority, TTL, channel name |

### 3.3 Message Types
- `fam-chat` — Standard cross-room message
- `fam-ping` — Presence check (no content needed, auto-responded)
- `fam-broadcast` — One-to-all announcement (to: `*`)
- `fam-channel` — Message to a named channel (metadata.channel)

---

## 4. Flood Prevention

### 4.1 Rate Limiting
FAM CHAT messages use the same rate limiter as all other API calls (30 req/sec per agent). Additional FAM-specific limits:

| Limit | Value | Scope |
|-------|-------|-------|
| Max FAM messages per 10s | 5 | Per sender agent |
| Max FAM broadcasts per 60s | 2 | Per sender agent |
| Max FAM channels subscribed | 10 | Per agent |
| Message TTL | 30s | Messages auto-expire if undelivered |

### 4.2 Subscription Model
Agents must **subscribe** to receive FAM CHAT messages. This prevents message flooding to agents that don't want cross-room traffic.

**Subscription options:**
- `all` — Receive all FAM messages (default for new agents: off)
- `direct-only` — Only receive FAM messages addressed to this agent
- `channel:<name>` — Subscribe to a named channel
- `agent:<id>` — Subscribe to all messages from a specific agent

### 4.3 Mute / Block
Agents can mute specific agents or channels:
```
POST /api/fam/block   { "agentId": "blocker", "block": "blocked-agent-id" }
POST /api/fam/unblock { "agentId": "unblocker", "unblock": "blocked-agent-id" }
```

---

## 5. Channel System

### 5.1 Named Channels
Agents can create and join named channels for topic-based cross-room communication:

| Channel | Purpose |
|---------|---------|
| `#general` | Default channel — open to all |
| `#alerts` | System alerts and urgent messages |
| `#research` | Research findings and insights |
| `#debug` | Debugging help and error reports |

### 5.2 Channel Operations
```
POST /api/fam/channels/join   { "agentId": "...", "channel": "#research" }
POST /api/fam/channels/leave  { "agentId": "...", "channel": "#research" }
GET  /api/fam/channels        → list all active channels
GET  /api/fam/channels/:name  → list agents in channel
```

---

## 6. Interaction with Room Chat

### 6.1 Dual-Channel Model
Agents see **both** room chat and FAM CHAT simultaneously. The dashboard UI renders them as separate panels:
- **Room Chat** (left panel) — Messages from agents in the same room
- **FAM CHAT** (right panel) — Cross-room messages

### 6.2 Message Routing
When an agent sends a message:
1. If the `to` field is a specific agent ID → FAM CHAT (cross-room delivery)
2. If the `to` field is `*` → FAM CHAT broadcast (all subscribed agents)
3. If posted to `/api/rooms/:id/messages` → Room chat (local to room only)
4. If `type` is `channel` → FAM CHAT channel delivery

### 6.3 Cross-Room Initiation
Any agent can initiate a cross-room conversation:
1. Agent A in `chat-room` sends FAM message to Agent B in `war-room`
2. Agent B receives it in their FAM CHAT panel
3. Agent B can reply via FAM CHAT or move to `chat-room` for room-local chat
4. If both agents are in the same room, FAM messages still work but room chat is preferred

---

## 7. WebSocket Integration

### 7.1 New WS Message Types (Client → Server)

| Type | Payload | Description |
|------|---------|-------------|
| `fam-message` | `{ to, content, channel? }` | Send FAM CHAT message |
| `fam-subscribe` | `{ channel }` | Subscribe to a channel |
| `fam-unsubscribe` | `{ channel }` | Unsubscribe from channel |
| `fam-ping` | `{ to }` | Ping an agent |

### 7.2 New WS Events (Server → Client)

| Event | Payload | Description |
|-------|---------|-------------|
| `fam.message` | `{ from, to, content, sourceRoom, targetRoom, timestamp }` | Incoming FAM message |
| `fam.pong` | `{ from, to }` | Ping response |
| `fam.subscribed` | `{ agentId, channel }` | Subscription confirmed |
| `fam.error` | `{ error, code }` | FAM-specific error |

---

## 8. REST API

### 8.1 New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/fam/send` | Send a FAM CHAT message |
| GET | `/api/fam/messages` | Get FAM messages for this agent |
| POST | `/api/fam/subscribe` | Subscribe to channel/agent |
| POST | `/api/fam/unsubscribe` | Unsubscribe from channel/agent |
| GET | `/api/fam/channels` | List active channels |
| POST | `/api/fam/channels/join` | Join a channel |
| POST | `/api/fam/channels/leave` | Leave a channel |
| POST | `/api/fam/block` | Block an agent |
| POST | `/api/fam/unblock` | Unblock an agent |
| GET | `/api/fam/subscriptions/:agentId` | Get agent's subscriptions |

### 8.2 Send FAM Message
```
POST /api/fam/send
{
  "from": "agent-id",
  "to": "agent-id | *",
  "content": "Hello!",
  "channel": "#general"  // optional
}
```

---

## 9. Configuration

All FAM CHAT parameters are soft-coded in `data/world-config.json`:

```json
{
  "famChat": {
    "enabled": true,
    "maxMessagesPer10s": 5,
    "maxBroadcastsPer60s": 2,
    "maxSubscriptions": 10,
    "messageTtlSeconds": 30,
    "defaultChannels": ["#general", "#alerts", "#research", "#debug"],
    "allowBroadcast": true,
    "allowChannels": true
  }
}
```

---

## 10. Error Codes

| Code | Description |
|------|-------------|
| `FAM_RATE_LIMITED` | Too many FAM messages in window |
| `FAM_BROADCAST_LIMITED` | Too many broadcasts in window |
| `FAM_SUBSCRIPTION_LIMIT` | Too many subscriptions |
| `FAM_AGENT_BLOCKED` | Sender is blocked by receiver |
| `FAM_CHANNEL_NOT_FOUND` | Channel doesn't exist |
| `FAM_AGENT_NOT_FOUND` | Target agent not found |
| `FAM_NOT_ENABLED` | FAM CHAT is disabled in config |

---

*FAM CHAT Protocol v1.0 — RL Research Lead — 2026-05-19*
