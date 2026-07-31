# OCE Continuity Core — API Reference

> **Author:** AS (Assistant Manager)
> **Date:** 2026-05-16
> **Base URL:** `http://localhost:8000`
> **Version:** 1.0.0

## Health

### `GET /health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "oce-continuity-core"
}
```

---

## Chat

### `POST /chat`

Continuity-aware chat endpoint. Preserves goals, trajectories, observer state, and operational context across sessions.

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "context": { "key": "value" }
}
```

**Response:**
```json
{
  "response": "string",
  "session_id": "string",
  "continuity_preserved": true
}
```

**SRRA-OPH Integration:** `continuity_collars.py`, `operator_continuity.py`

---

## Observers

### `GET /observers`

Live observer status panel. Returns all active observers with current state.

**Response:**
```json
[
  {
    "observer_id": "string",
    "state": "active | idle | monitoring",
    "entropy": 0.0,
    "task": "string"
  }
]
```

**SRRA-OPH Integration:** `observer_mesh.py`, `reconstruction_synthesizer.py`

---

## Events

### `GET /events`

Live event feed from the event fabric.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Max events to return |

**Response:**
```json
[
  {
    "event_type": "string",
    "timestamp": "ISO-8601",
    "payload": {}
  }
]
```

**SRRA-OPH Integration:** `event_fabric.py`

---

## Attractor

### `GET /attractor`

Current operational goals and convergence state.

**Response:**
```json
{
  "goal": "string",
  "confidence": 0.0,
  "entropy_pressure": 0.0,
  "convergence": 0.0
}
```

**SRRA-OPH Integration:** `attractor_reasoning.py`

---

## Memory

### `GET /memory`

Trajectory memory, structural memory, and repair memory view.

**Response:**
```json
{
  "trajectory_memory": [],
  "structural_memory": [],
  "repair_memory": []
}
```

**SRRA-OPH Integration:** `trajectory_fields.py`, `structural_memory.py`

---

## WebSocket

### `WS /ws/events`

Real-time event stream via WebSocket. Sends heartbeat every 5 seconds.

**Connection:** `ws://localhost:8000/ws/events`

**Message Format:**
```json
{
  "type": "heartbeat | event | observer_update",
  "timestamp": "ISO-8601",
  "data": {}
}
```

**SRRA-OPH Integration:** `event_fabric.py` (stream bridge)

---

## Error Format

All errors follow this format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Observer Runtime (Phase 3)

### `POST /observers`

Create a new observer.

**Request Body:**
```json
{
  "observer_type": "trading | repair | entropy | content | system",
  "name": "string",
  "config": {
    "event_types": ["observer.state_change", "attractor.update"],
    "priority_threshold": 1,
    "entropy_limit": 0.8
  }
}
```

**Response:**
```json
{
  "observer_id": "string",
  "status": "created",
  "observer_type": "trading",
  "created_at": "ISO-8601"
}
```

---

### `GET /observers`

List all observers with status and health summary.

**Response:**
```json
{
  "observers": [
    {
      "observer_id": "string",
      "name": "string",
      "observer_type": "trading",
      "status": "active | suspended | created | destroyed",
      "health": {
        "entropy": 0.32,
        "drift": 0.05,
        "budget_remaining": 450.0
      },
      "last_activity": "ISO-8601"
    }
  ],
  "total": 5,
  "active": 3
}
```

---

### `GET /observers/{id}`

Get full observer details.

**Response:**
```json
{
  "observer_id": "string",
  "name": "string",
  "observer_type": "trading",
  "status": "active",
  "config": {},
  "health": {
    "entropy": 0.32,
    "drift": 0.05,
    "budget_remaining": 450.0,
    "events_processed": 1523,
    "last_repair": null
  },
  "state": {
    "last_snapshot": "ISO-8601",
    "snapshot_count": 42
  },
  "subscriptions": ["observer.state_change", "attractor.update"],
  "created_at": "ISO-8601"
}
```

---

### `GET /observers/{id}/health`

Detailed health metrics for an observer.

**Response:**
```json
{
  "observer_id": "string",
  "entropy": {
    "current": 0.32,
    "trend": "stable",
    "history": [0.30, 0.31, 0.32]
  },
  "drift": {
    "current": 0.05,
    "threshold": 0.15,
    "direction": "positive"
  },
  "budget": {
    "total": 500.0,
    "consumed": 50.0,
    "remaining": 450.0
  },
  "events": {
    "processed": 1523,
    "errors": 2,
    "last_event": "ISO-8601"
  }
}
```

---

### `POST /observers/{id}/activate`

Activate an observer (start processing events).

**Response:**
```json
{
  "observer_id": "string",
  "status": "activated",
  "activated_at": "ISO-8601"
}
```

---

### `POST /observers/{id}/suspend`

Suspend an observer (pause event processing).

**Response:**
```json
{
  "observer_id": "string",
  "status": "suspended",
  "suspended_at": "ISO-8601"
}
```

---

### `DELETE /observers/{id}`

Destroy an observer permanently.

**Response:**
```json
{
  "observer_id": "string",
  "status": "destroyed"
}
```

---

### `POST /observers/{id}/subscribe`

Subscribe an observer to event types.

**Request Body:**
```json
{
  "event_types": ["observer.state_change", "entropy.budget_warning"]
}
```

**Response:**
```json
{
  "observer_id": "string",
  "subscriptions": ["observer.state_change", "entropy.budget_warning"]
}
```

---

### `WS /ws/observers`

Real-time observer updates via WebSocket.

**Connection:** `ws://localhost:8000/ws/observers`

**Message Format:**
```json
{
  "type": "observer.status_change | observer.health_update | observer.event_processed",
  "timestamp": "ISO-8601",
  "data": {
    "observer_id": "string",
    "status": "active",
    "health": {}
  }
}
```

---

## Future Endpoints (Planned)

| Endpoint | Phase | Purpose |
|----------|-------|---------|
| `GET /topology` | 4 | Current topology graph |
| `POST /memory/compress` | 4 | Trigger memory compression |
| `GET /metrics` | 5 | Observability metrics |
| `GET /cost` | 5 | Cost/entropy budget status |
| `POST /execute` | 6 | Execute tool via capability fields |
| `GET /goals` | 7 | List active goals |
| `POST /goals` | 7 | Set new goal |
| `GET /self-model` | 9 | Current self-model state |
| `GET /cost` | 5 | Cost/entropy budget status |
| `POST /execute` | 6 | Execute tool via capability fields |
| `GET /goals` | 7 | List active goals |
| `POST /goals` | 7 | Set new goal |
| `GET /self-model` | 9 | Current self-model state |
