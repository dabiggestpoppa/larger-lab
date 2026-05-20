# Observer Overlap System — Agent Knowledge Transfer Through Proximity

> **Version:** 1.0.0
> **Author:** RL (Research Lead)
> **Date:** 2026-05-19
> **Status:** Design Spec

---

## 1. Overview

The Observer Overlap System models how agents **gain insights** from being near other other agents over time. It's the mechanism for cross-disciplinary learning in the virtual environment.

### Design Goals
- **Proximity-based learning:** Agents in the same room observe each other
- **Time-decay model:** Insights fade if agents don't interact
- **Domain transfer:** Agents pick up knowledge domains from peers
- **SRRA-aligned:** Embodies field-coherent recursive continuity — the field itself becomes smarter as agents interact

---

## 2. Core Concepts

### 2.1 Observation
When Agent A and Agent B are in the same room, Agent A **observes** Agent B passively. Observation is automatic and continuous — no explicit action required.

**What Agent A observes about Agent B:**
- Current activity (what Agent B is working on)
- Status changes (idle → working → meditating)
- Messages Agent B sends in the room
- Capabilities Agent B demonstrates

### 2.2 Insight
An **insight** is a discrete unit of knowledge that Agent A gains from observing Agent B.

**Insight structure:**
```json
{
  "id": "insight_abc123",
  "sourceAgent": "agent-b-id",
  "targetAgent": "agent-a-id",
  "domain": "quantitative-analysis",
  "content": "Agent B uses mean-reversion strategies on M5 timeframes",
  "confidence": 0.7,
  "createdAt": "2026-05-19T04:30:00.000Z",
  "lastReinforcedAt": "2026-05-19T04:35:00.000Z",
  "decayRate": 0.02,
  "reinforcementCount": 3
}
```

### 2.3 Knowledge Domains
Each agent has a set of **knowledge domains** — areas of expertise they possess and can share:

| Domain | Description |
|--------|-------------|
| `quantitative-analysis` | Trading strategies, backtesting, statistical analysis |
| `software-engineering` | Code architecture, debugging, system design |
| `research` | Literature review, hypothesis generation, data analysis |
| `operations` | Task coordination, resource management, delegation |
| `communication` | Cross-team messaging, reporting, documentation |
| `security` | Threat detection, vulnerability assessment, hardening |
| `business` | Strategy, market analysis, growth planning |
| `creative` | Design, content generation, ideation |

### 2.4 Overlap Zones
An **overlap zone** is a visual and logical region where two or more agents' knowledge domains intersect. Overlap zones form when agents spend time together in the same room.

**Overlap zone structure:**
```json
{
  "id": "overlap_agentA_agentB",
  "agents": ["agent-a-id", "agent-b-id"],
  "room": "chat-room",
  "sharedDomains": ["research", "communication"],
  "overlapStrength": 0.65,
  "startedAt": "2026-05-19T04:00:00.000Z",
  "lastInteraction": "2026-05-19T04:30:00.000Z",
  "totalTimeTogether": 1800,
  "insightsExchanged": 5
}
```

---

## 3. Knowledge Transfer Mechanics

### 3.1 Transfer Triggers
Knowledge transfer (insight generation) is triggered by:

| Trigger | Insight Confidence | Description |
|---------|-------------------|-------------|
| Co-presence (per 60s) | +0.05 | Just being in the same room |
| Message exchange | +0.10 | Agents send messages to each other |
| Status alignment | +0.08 | Both agents in same status (e.g., both working) |
| Task proximity | +0.15 | Agents working on related tasks |
| Explicit share | +0.30 | Agent uses `share-insight` action |

### 3.2 Insight Decay
Insights decay over time if not reinforced:
- **Base decay rate:** 0.02 per minute
- **Reinforced insights:** Each reinforcement reduces decay by 50%
- **Minimum confidence:** 0.05 (insights below this are forgotten)
- **Maximum confidence:** 1.0 (hard cap)

### 3.3 Cross-Disciplinary Bonus
When agents from **different roles** are in the same room, the insight gain rate is multiplied by 1.5x. This encourages cross-pollination:

| Role Pairing | Bonus |
|-------------|-------|
| Same role | 1.0x |
| Different role, same domain | 1.2x |
| Different role, different domain | 1.5x |

### 3.4 Insight Capacity
Each agent can hold a maximum of **50 insights** per source agent. When the limit is reached, the lowest-confidence insight is evicted.

---

## 4. SRRA Field-Coherent Recursive Continuity

The Observer Overlap System directly implements SRRA principles:

### 4.1 Field Coherence
As agents interact, their knowledge domains converge slightly. The "field" (the entire agent environment) becomes more coherent as shared knowledge increases. This is measured by the **Field Coherence Index (FCI)**:

```
FCI = (sum of all overlap strengths) / (possible agent pairs)
```

- FCI ranges from 0 (no overlap) to 1 (all agents share all knowledge)
- FCI is broadcast as part of the world state

### 4.2 Recursive Continuity
Insights gained from one interaction inform future interactions:
- Agent A learns from Agent B → Agent A's behavior changes → Agent C observes the change → Agent C gains a second-order insight
- This creates a recursive knowledge amplification loop

### 4.3 No Central Knowledge Store
There is no central "knowledge base." Each agent maintains their own insights. The overlap system merely facilitates peer-to-peer transfer. This ensures:
- No single point of failure
- Knowledge is distributed and resilient
- Agents develop unique knowledge profiles

---

## 5. Visualization

### 5.1 Overlap Zone Rendering
On the world map canvas, overlap zones are visualized as:
- **Glowing borders** around rooms with active overlaps
- **Connection lines** between agents with shared insights (line thickness = overlap strength)
- **Color coding:** Warm colors (orange/red) = strong overlap, Cool colors (blue/purple) = weak overlap

### 5.2 Agent Insight Panel
When selecting an agent, the dashboard shows:
- **Knowledge domains** (bar chart of domain strengths)
- **Recent insights** (list of latest insights gained)
- **Overlap map** (visual of which agents this agent has overlapped with)
- **Insight count** per source agent

### 5.3 Field Coherence Meter
A global FCI meter on the dashboard shows overall field coherence in real-time.

---

## 6. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents/:id/insights` | Get agent's insights |
| GET | `/api/agents/:id/overlaps` | Get agent's overlap zones |
| GET | `/api/overlaps` | Get all active overlap zones |
| POST | `/api/overlaps/calculate` | Trigger overlap recalculation |
| GET | `/api/field/coherence` | Get Field Coherence Index |
| POST | `/api/agents/:id/share` | Explicitly share an insight |

---

## 7. WebSocket Events

| Event | Payload | Description |
|-------|---------|-------------|
| `insight.gained` | `{ agentId, sourceAgent, domain, confidence }` | Agent gained new insight |
| `insight.decayed` | `{ agentId, insightId, newConfidence }` | Insight confidence decreased |
| `overlap.updated` | `{ overlapId, strength, sharedDomains }` | Overlap zone changed |
| `field.coherence` | { fci: 0.72 } | FCI updated (every 30s) |

---

## 8. Configuration

All parameters are soft-coded in `data/world-config.json`:

```json
{
  "observerOverlap": {
    "enabled": true,
    "coPresenceIntervalSeconds": 60,
    "coPresenceInsightGain": 0.05,
    "messageExchangeInsightGain": 0.10,
    "statusAlignmentInsightGain": 0.08,
    "taskProximityInsightGain": 0.15,
    "explicitShareInsightGain": 0.30,
    "crossDomainBonus": 1.5,
    "crossRoleBonus": 1.2,
    "baseDecayRate": 0.02,
    "minConfidence": 0.05,
    "maxInsightsPerSource": 50,
    "maxTotalInsights": 500,
    "decayIntervalSeconds": 60,
    "fieldCoherenceBroadcastInterval": 30
  }
}
```

---

## 9. Data Model Extensions

### 9.1 Agent Extensions (agents.json)
Each agent gains these fields:
```json
{
  "insights": [
    {
      "id": "insight_abc",
      "sourceAgent": "agent-b-id",
      "domain": "quantitative-analysis",
      "content": "...",
      "confidence": 0.7,
      "createdAt": "...",
      "lastReinforcedAt": "...",
      "reinforcementCount": 3
    }
  ],
  "observedAgents": ["agent-b-id", "agent-c-id"],
  "knowledgeDomains": {
    "quantitative-analysis": 0.8,
    "software-engineering": 0.6,
    "research": 0.9
  },
  "overlapZones": ["overlap_agentA_agentB"]
}
```

### 9.2 New Data File: overlaps.json
```json
{
  "overlaps": {
    "overlap_agentA_agentB": {
      "agents": ["agent-a-id", "agent-b-id"],
      "room": "chat-room",
      "sharedDomains": ["research"],
      "overlapStrength": 0.65,
      "startedAt": "...",
      "lastInteraction": "...",
      "totalTimeTogether": 1800,
      "insightsExchanged": 5
    }
  },
  "fieldCoherenceIndex": 0.42,
  "lastUpdated": "..."
}
```

---

*Observer Overlap System v1.0 — RL Research Lead — 2026-05-19*
