# OCE Integration Contract

> Version: 0.1.0  
> Date: 2026-08-23

## Overview

This document defines the integration boundary between the OCE MCP Facade and the OCE Backend. The facade is the **only** component that communicates with OCE.

## Authentication

### Service Token

- The facade authenticates to OCE using a **read-only service token**
- Token is loaded from `OCE_SERVICE_TOKEN` environment variable
- Token is **never** logged, displayed in Telegram, or committed to git
- Token scope: read-only observer endpoints only
- If token is missing or invalid, facade returns `BLOCKED` state

### Token Format

```
OCE_SERVICE_TOKEN=oce-read-<random-hex>
```

## Endpoint Contract

### Request Format

All OCE requests from the facade follow:

```
GET {OCE_BACKEND_URL}{endpoint}
Authorization: Bearer {OCE_SERVICE_TOKEN}
Accept: application/json
X-Request-ID: {uuid}
X-Facade-Version: 0.1.0
```

### Response Contract

Every MCP tool response must include:

```json
{
  "state": "PASS | DEGRADED | BLOCKED | OFFLINE | ERROR",
  "request_id": "uuid-v4",
  "timestamp": "2026-08-23T12:00:00Z",
  "backend_version": "1.0.0",
  "tool": "oce_health",
  "data": { ... },
  "error": null | "error message",
  "latency_ms": 42
}
```

## Health Check

```
Endpoint: GET /health
Expected: { "status": "healthy", "service": "oce-continuity-core" }
Timeout:  5 seconds
State:    PASS if status=healthy, OFFLINE if unreachable, ERROR if unexpected
```

## System Status

```
Endpoint: GET /
Expected: { "message": "OCE Continuity Core API", "version": "1.0.0" }
Timeout:  10 seconds
State:    PASS if response received, OFFLINE if unreachable
```

## Component Status

```
Endpoint: GET /observers
Expected: List of { observer_id, state, entropy, task }
Timeout:  10 seconds
State:    PASS if list received, DEGRADED if partial, OFFLINE if unreachable
```

## List Jobs

```
Endpoint: GET /execution/tasks
Expected: List of execution tasks
Timeout:  10 seconds
State:    PASS if list received, OFFLINE if unreachable
```

## Get Job

```
Endpoint: GET /execution/tasks/{task_id}
Expected: Task details object
Timeout:  10 seconds
State:    PASS if found, ERROR if not found, OFFLINE if unreachable
```

## Get Recent Events

```
Endpoint: GET /events?limit=20
Expected: List of EventResponse objects
Timeout:  10 seconds
State:    PASS if list received, OFFLINE if unreachable
```

## Get Evidence Status

```
Endpoint: GET /execution/stats
Expected: Execution statistics including validation metrics
Timeout:  10 seconds
State:    PASS if stats received, OFFLINE if unreachable
```

## Get Cost Status

```
Endpoint: GET /execution/analytics
Expected: Analytics data with cost information
Timeout:  10 seconds
State:    PASS if analytics received, OFFLINE if unreachable
```

## Get Capability Manifest

```
Endpoint: GET /evolution/status
Expected: Evolution/capability status
Timeout:  10 seconds
State:    PASS if status received, OFFLINE if unreachable
```

## Get Backend Version

```
Endpoint: GET /
Expected: { "version": "x.y.z" }
Timeout:  5 seconds
State:    PASS if version received, OFFLINE if unreachable
```

## Redaction Rules

The facade applies these redaction rules to all OCE responses before returning to Hermes:

1. **Token patterns:** `oce-*`, `Bearer *`, API keys → `[REDACTED]`
2. **File paths:** Absolute paths → basename only
3. **Database URLs:** Full connection strings → `[DB_REDACTED]`
4. **IP addresses:** Non-localhost IPs → `[IP_REDACTED]`
5. **Environment variables:** Values of sensitive env vars → `[ENV_REDACTED]`

## Error Handling

| Condition | Behavior |
|-----------|----------|
| OCE unreachable | Return OFFLINE, never fabricate data |
| OCE timeout (>30s) | Return DEGRADED with partial data if available |
| OCE auth failure | Return BLOCKED, log security event |
| Malformed response | Return ERROR, log raw response (redacted) |
| Rate limit exceeded | Return BLOCKED with retry-after hint |

## Mock Backend (Phase 0)

When `OCE_BACKEND_URL` is not configured or OCE is offline, the facade uses a mock adapter:

```python
MOCK_RESPONSES = {
    "/health": {"status": "healthy", "service": "oce-continuity-core-mock"},
    "/": {"message": "OCE Continuity Core API (MOCK)", "version": "0.0.0-mock"},
    "/observers": [],
    "/execution/tasks": [],
    "/events": [],
    "/execution/stats": {"total_tasks": 0, "success_rate": 0},
    "/execution/analytics": {"total_cost": 0, "period": "mock"},
    "/evolution/status": {"status": "mock", "capabilities": []},
}
```

All mock responses include `"mock": true` in the data and state `PASS` with explicit mock indicator.
