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

## Future Endpoints (Planned)

| Endpoint | Phase | Purpose |
|----------|-------|---------|
| `POST /observers` | 3 | Create new observer |
| `DELETE /observers/{id}` | 3 | Destroy observer |
| `POST /observers/{id}/repair` | 3 | Trigger repair |
| `GET /topology` | 4 | Current topology graph |
| `POST /memory/compress` | 4 | Trigger memory compression |
| `GET /metrics` | 5 | Observability metrics |
| `GET /cost` | 5 | Cost/entropy budget status |
| `POST /execute` | 6 | Execute tool via capability fields |
| `GET /goals` | 7 | List active goals |
| `POST /goals` | 7 | Set new goal |
| `GET /self-model` | 9 | Current self-model state |
