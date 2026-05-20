# RL → World Builder Handoff Brief

> **From:** RL (Research Lead)
> **To:** World Builder (Frontend/UI)
> **Date:** 2026-05-19
> **Status:** Ready for Implementation

---

## 1. Overview

This brief describes the backend APIs, message types, and data structures the World Builder needs to integrate for FAM CHAT and Observer Overlap features.

---

## 2. Backend APIs Needed by Frontend

### 2.1 FAM CHAT APIs

#### Send FAM Message
```
POST /api/fam/send
Body: { "from": "agent-id", "to": "agent-id | *", "content": "text", "channel": "#general" }
Response: { "success": true, "message": { ...fam message object... } }
```

#### Get FAM Messages
```
GET /api/fam/messages?agentId=agent-id&limit=50
Response: { "success": true, "messages": [ ...fam messages... ] }
```

#### Subscribe to Channel
```
POST /api/fam/subscribe
Body: { "agentId": "agent-id", "channel": "#research" | "agent:agent-id" | "all" | "direct-only" }
Response: { "success: true, "subscriptions": [...] }
```

#### Unsubscribe
```
POST /api/fam/unsubscribe
Body: { "agentId": "agent-id", "channel": "#research" }
Response: { "success": true }
```

#### List Channels
```
GET /api/fam/channels
Response: { "success": true, "channels": [
  { "name": "#general", "memberCount": 5, "members": ["agent-id-1", ...] }
]}
```

#### Block/Unblock Agent
```
POST /api/fam/block    { "agentId": "blocker-id", "block": "blocked-id" }
POST /api/fam/unblock  { "agentId": "unblocker-id", "unblock": "unblocked-id" }
```

#### Get Subscriptions
```
GET /api/fam/subscriptions/:agentId
Response: { "success": true, "subscriptions": ["#general", "#research", "agent:agent-b-id"] }
```

### 2.2 Observer Overlap APIs

#### Get Agent Insights
```
GET /api/agents/:id/insights
Response: {
  "success": true,
  "insights": [
    {
      "id": "insight_abc",
      "sourceAgent": "agent-b-id",
      "sourceAgentName": "PM",
      "domain": "quantitative-analysis",
      "content": "Agent B uses mean-reversion strategies",
      "confidence": 0.7,
      "createdAt": "2026-05-19T04:30:00.000Z",
      "reinforcementCount": 3
    }
  ]
}
```

#### Get Agent Overlaps
```
GET /api/agents/:id/overlaps
Response: {
  "success": true,
  "overlaps": [
    {
      "id": "overlap_agentA_agentB",
      "agents": ["agent-a-id", "agent-b-id"],
      "otherAgentName": "PM",
      "room": "chat-room",
      "sharedDomains": ["research", "communication"],
      "overlapStrength": 0.65,
      "totalTimeTogether": 1800,
      "insightsExchanged": 5
    }
  ]
}
```

#### Get All Overlaps
```
GET /api/overlaps
Response: { "success": true, "overlaps": [ ...all active overlaps... ] }
```

#### Get Field Coherence
```
GET /api/field/coherence
Response: { "success": true, "fci": 0.42, "timestamp": "..." }
```

#### Explicitly Share Insight
```
POST /api/agents/:id/share
Body: { "targetAgentId": "agent-b-id", "domain": "research", "content": "I found that..." }
Response: { "success": true, "insight": { ... } }
```

---

## 3. WebSocket Message Types

### 3.1 Client → Server (Frontend sends these)

```javascript
// Send FAM message
ws.send(JSON.stringify({
  type: 'fam-message',
  to: 'agent-id',
  content: 'Hello from across the building!',
  channel: '#general'  // optional
}));

// Subscribe to channel
ws.send(JSON.stringify({
  type: 'fam-subscribe',
  channel: '#research'
}));

// Unsubscribe
ws.send(JSON.stringify({
  type: 'fam-unsubscribe',
  channel: '#research'
}));

// Ping an agent
ws.send(JSON.stringify({
  type: 'fam-ping',
  to: 'agent-id'
}));
```

### 3.2 Server → Client (Frontend receives these)

```javascript
// Incoming FAM message
{ event: 'fam.message', from: 'agent-a-id', to: 'agent-b-id', content: '...', sourceRoom: 'chat-room', targetRoom: 'war-room', timestamp: '...' }

// Ping response
{ event: 'fam.pong', from: 'agent-id', to: 'agent-id' }

// Subscription confirmed
{ event: 'fam.subscribed', agentId: 'agent-id', channel: '#research' }

// FAM error
{ event: 'fam.error', error: 'Rate limit exceeded', code: 'FAM_RATE_LIMITED' }

// New insight gained
{ event: 'insight.gained', agentId: 'agent-a-id', sourceAgent: 'agent-b-id', sourceAgentName: 'PM', domain: 'quantitative-analysis', confidence: 0.7 }

// Insight decayed
{ event: 'insight.decayed', agentId: 'agent-a-id', insightId: 'insight_abc', newConfidence: 0.65 }

// Overlap zone updated
{ event: 'overlap.updated', overlapId: 'overlap_agentA_agentB', strength: 0.72, sharedDomains: ['research'] }

// Field coherence updated
{ event: 'field.coherence', fci: 0.42 }
```

---

## 4. Data Structures to Expect

### 4.1 World State Extension
The existing `GET /api/world` and `world.state` WebSocket event will include new fields:

```json
{
  "rooms": [ ... ],
  "agents": [
    {
      "id": "agent-id",
      "name": "OWL",
      "knowledgeDomains": { "research": 0.9, "operations": 0.8 },
      "insightCount": 12,
      "overlapCount": 3
    }
  ],
  "overlaps": [
    {
      "id": "overlap_agentA_agentB",
      "agents": ["agent-a-id", "agent-b-id"],
      "overlapStrength": 0.65,
      "sharedDomains": ["research"]
    }
  ],
  "fieldCoherenceIndex": 0.42,
  "connections": [ ... ],
  "recentActivity": [ ... ]
}
```

### 4.2 Agent Detail Extension
`GET /api/agents/:id` will include:

```json
{
  "success": true,
  "agent": {
    "id": "...",
    "name": "...",
    "insights": [ ... ],
    "observedAgents": ["agent-b-id", "agent-c-id"],
    "knowledgeDomains": { "research": 0.9, "operations": 0.8 },
    "overlapZones": ["overlap_agentA_agentB"],
    "famSubscriptions": ["#general", "#research"]
  }
}
```

---

## 5. UI Recommendations

### 5.1 FAM CHAT Panel
- Add a new tab or panel: **FAM CHAT** alongside the existing Chat panel
- Show messages from subscribed channels
- Input box at bottom with channel selector dropdown
- Unread message counter per channel
- Visual distinction: FAM messages have a 🌐 icon prefix

### 5.2 Overlap Visualization
- On the world map canvas, draw **colored lines** between agents with active overlaps
- Line thickness = overlap strength (0.1 to 1.0 maps to 1px to 5px)
- Line color: warm (strong) → cool (weak)
- Room glow effect when overlaps are active inside

### 5.3 Agent Detail Panel Additions
- **Knowledge Domains** bar chart (horizontal bars, color-coded by domain)
- **Recent Insights** list (collapsible, shows last 5 insights)
- **Overlap Map** — mini visual showing connected agents

### 5.4 Field Coherence Meter
- Small gauge/meter in the header area
- Shows FCI 0.0 to 1.0
- Color: red (low) → yellow (medium) → green (high)

---

## 6. Timeline and Dependencies

### Phase 1: Backend (RL — this implementation)
- ✅ FAM CHAT protocol design
- ✅ Observer overlap design
- 🔄 Backend API endpoints in server.js
- 🔄 FAM CHAT module (src/communication/fam-chat.js)
- 🔄 Observer overlap module (src/observer-overlap.js)
- 🔄 World engine integration
- 🔄 world-config.json

### Phase 2: Frontend (World Builder)
- FAM CHAT panel UI
- Overlap visualization on canvas
- Agent detail panel extensions
- Field coherence meter
- WebSocket event handlers for new events

### Dependencies
- World Builder needs the backend APIs to be live before frontend integration
- WebSocket events must match the exact event names listed above
- Data structures must match the schemas above

### No-Break Guarantee
- All new endpoints are additive (no existing endpoints modified)
- All new WebSocket events are additive (no existing events changed)
- Existing room chat, direct messages, and world state remain unchanged
- FAM CHAT is opt-in (agents must subscribe to receive messages)

---

## 7. Testing Checklist

- [ ] Send FAM message to specific agent in different room
- [ ] Send FAM broadcast (to: *)
- [ ] Subscribe/unsubscribe to channels
- [ ] Rate limiting works (5 msgs/10s)
- [ ] Block/unblock agents
- [ ] Insights generated when agents share a room
- [ ] Insight decay over time
- [ ] Overlap zones created and updated
- [ ] Field coherence index calculated
- [ ] WebSocket events fire correctly
- [ ] Existing room chat still works
- [ ] Existing direct messages still work
- [ ] World state endpoint includes new fields

---

*Handoff brief complete. Backend implementation is in progress. Contact RL with any questions.*
