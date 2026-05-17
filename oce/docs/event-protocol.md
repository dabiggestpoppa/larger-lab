# OCE Event Subscription Protocol

> **Author:** Sub-OC2 (Execution & Protocol Design)
> **Date:** 2026-05-16
> **Phase:** OCE Phase 2 — Event Fabric (OCE-2.8)
> **Status:** Complete
> **Depends On:** `event-types.md` (OCE-2.7), `api-reference.md`
> **Unblocks:** OCE Phase 3 — Observer Runtime WebSocket integration

---

## Overview

The OCE Event Subscription Protocol defines how clients (frontend shells, operator tools, and internal services) connect to the Event Fabric via WebSocket, register observers, filter events, and handle errors. This is the real-time nervous system of the Operator Continuity Engine.

### Design Principles

1. **Subscribe by pattern, receive by match** — clients declare interest patterns; the server routes matching events.
2. **Observers are first-class** — every subscription is backed by an observer identity with lifecycle management.
3. **Graceful degradation** — connection loss triggers automatic reconnection with replay from last acknowledged sequence.
4. **Minimal wire format** — JSON only, no binary framing, no custom serialization.
5. **Auth before subscribe** — no events flow until the client is authenticated.

---

## 1. WebSocket Subscription Flow

### 1.1 Connection Lifecycle

```
Client                          Server
  |                                |
  |--- WebSocket handshake ------->|   (HTTP 101 Upgrade)
  |                                |
  |<--- auth_required -------------|   Server demands authentication
  |                                |
  |--- authenticate -------------->|   Client sends credentials
  |                                |
  |<--- auth_result ---------------|   Server confirms or rejects
  |                                |
  |--- subscribe ----------------->|   Client sends filter patterns
  |                                |
  |<--- subscription_ack ----------|   Server confirms subscription
  |                                |
  |<--- event -------------------->|   Server streams matching events
  |                                |
  |--- unsubscribe --------------->|   Client removes a subscription
  |                                |
  |<--- unsub_ack -----------------|   Server confirms removal
  |                                |
  |--- disconnect ---------------->|   Client closes connection
  |                                |
```

### 1.2 Connection URL

```
ws://localhost:8000/ws/events
```

For production with TLS:

```
wss://<host>/ws/events
```

### 1.3 Handshake Requirements

The WebSocket upgrade request MUST include:

| Header | Required | Description |
|--------|----------|-------------|
| `Upgrade` | Yes | Must be `websocket` |
| `Connection` | Yes | Must include `Upgrade` |
| `Sec-WebSocket-Version` | Yes | Must be `13` |
| `Origin` | Recommended | Server validates against allowlist |

### 1.4 Connection States

| State | Description | Allowed Transitions |
|-------|-------------|-------------------|
| `connecting` | TCP connected, WebSocket handshake pending | → `authenticating`, `closed` |
| `authenticating` | Handshake complete, awaiting auth message | → `connected`, `closed` |
| `connected` | Authenticated, ready for subscribe/unsubscribe | → `subscribed`, `closed` |
| `subscribed` | Has ≥1 active subscription, receiving events | → `connected`, `closed` |
| `reconnecting` | Connection lost, attempting reconnect | → `authenticating`, `closed` |
| `closed` | Connection terminated | Terminal |

### 1.5 Reconnection Strategy

Clients MUST implement exponential backoff with jitter:

```
reconnect_delay = min(base_delay * 2^attempt + random(0, jitter), max_delay)
```

Default parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_delay` | 1000 ms | Initial retry delay |
| `max_delay` | 30000 ms | Maximum retry delay |
| `jitter` | 500 ms | Random jitter range |
| `max_attempts` | 10 | Give up after this many attempts |

On reconnect, the client MUST re-authenticate and re-subscribe. The server MAY replay events from the last acknowledged sequence number (see §7.3).

---

## 2. Observer Registration

### 2.1 What Is an Observer?

An **observer** is a logical entity that watches the event stream. Every WebSocket connection maps to one or more observers. Observers:

- Have a unique `observer_id` (UUID v4)
- Carry metadata (name, role, priority)
- Maintain subscription filters
- Track health and event processing metrics

### 2.2 Implicit Registration

Observers are **implicitly registered** when a client sends its first `subscribe` message. The server assigns an `observer_id` and returns it in the `subscription_ack`.

### 2.3 Explicit Registration (Advanced)

For observers that need identity persistence across reconnections (e.g., long-running operator tools), clients can explicitly register:

**Client → Server:**
```json
{
  "type": "register_observer",
  "payload": {
    "name": "operator-console-1",
    "role": "operator",
    "persistent": true,
    "metadata": {
      "version": "1.0.0",
      "platform": "web"
    }
  }
}
```

**Server → Client:**
```json
{
  "type": "observer_registered",
  "payload": {
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "operator-console-1",
    "role": "operator",
    "registered_at": "2026-05-16T17:49:00.000Z",
    "persistent": true
  }
}
```

### 2.4 Observer Lifecycle

| Transition | Trigger | Effect |
|------------|---------|--------|
| `created` | First subscribe or explicit register | Observer exists, no subscriptions |
| `active` | Has ≥1 active subscription | Receiving events |
| `idle` | All subscriptions removed | Observer exists, no events flowing |
| `suspended` | Server-side health degradation | Events queued, not delivered |
| `destroyed` | Client disconnects (non-persistent) or explicit unregister | Observer removed, state lost |
| `expired` | Persistent observer exceeds TTL without reconnect | Observer removed after grace period |

### 2.5 Observer Heartbeat

The server sends a `ping` every 30 seconds. The client MUST respond with a `pong` within 5 seconds. After 3 missed pongs, the server marks the observer as `suspended`.

**Server → Client:**
```json
{
  "type": "ping",
  "payload": {
    "timestamp": "2026-05-16T17:49:30.000Z"
  }
}
```

**Client → Server:**
```json
{
  "type": "pong",
  "payload": {
    "timestamp": "2026-05-16T17:49:30.120Z"
  }
}
```

---

## 3. Filter Patterns

### 3.1 Pattern Syntax

Filters use a hierarchical dot-notation matching the event type taxonomy (see `event-types.md`).

| Pattern Type | Syntax | Matches |
|-------------|--------|---------|
| **Exact** | `observer.created` | Only `observer.created` |
| **Single-level wildcard** | `observer.*` | `observer.created`, `observer.destroyed`, etc. (not `observer.v2.created`) |
| **Multi-level wildcard** | `observer.#` | `observer.created`, `observer.v2.created`, `observer.v2.state_change`, etc. |
| **Domain wildcard** | `*.created` | `observer.created`, `attractor.created`, `memory.created`, etc. |
| **Negation** | `!observer.*` | Everything EXCEPT `observer.*` events |
| **List** | `[observer.*, attractor.*]` | Events matching any pattern in the list |

### 3.2 Wildcard Rules

- `*` matches exactly one level (no dots)
- `#` matches zero or more levels
- Wildcards MUST appear at a level boundary: `observer.*` is valid, `obser*er.created` is NOT
- Negation patterns are evaluated AFTER positive patterns: `[*.*, !chat.*]` means "everything except chat events"

### 3.3 Priority Filtering

Clients can filter by minimum priority level:

```json
{
  "type": "subscribe",
  "payload": {
    "patterns": ["observer.*", "entropy.*"],
    "min_priority": "high"
  }
}
```

This subscribes to all `observer.*` and `entropy.*` events with priority `high` or `critical`.

### 3.4 Source Filtering

Clients can filter by event source:

```json
{
  "type": "subscribe",
  "payload": {
    "patterns": ["*.*.*"],
    "sources": ["observer_runtime", "entropy_economics"]
  }
}
```

### 3.5 Combined Filters

All filter dimensions are ANDed together:

```
event matches IF:
  (matches ANY positive pattern)
  AND (does NOT match any negation pattern)
  AND (priority >= min_priority, if specified)
  AND (source IN sources, if specified)
```

### 3.6 Filter Examples

| Use Case | Pattern |
|----------|---------|
| All observer lifecycle events | `observer.created`, `observer.destroyed`, `observer.activated`, `observer.suspended` |
| All high-priority events across domains | `*.*` with `min_priority: "high"` |
| Everything except chat noise | `[*.*, !chat.*]` |
| Entropy budget warnings only | `entropy.budget_warning`, `entropy.budget_exhausted` |
| System startup/shutdown | `system.startup`, `system.shutdown` |
| All topology changes | `topology.#` |

---

## 4. WebSocket Message Format (Server → Client)

### 4.1 Envelope Schema

All server→client messages share this envelope:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "payload", "meta"],
  "properties": {
    "type": {
      "type": "string",
      "enum": [
        "event",
        "subscription_ack",
        "unsub_ack",
        "auth_result",
        "observer_registered",
        "observer_destroyed",
        "error",
        "ping",
        "rate_limit_warning",
        "replay_complete"
      ]
    },
    "payload": {
      "type": "object",
      "description": "Message-type-specific payload"
    },
    "meta": {
      "type": "object",
      "required": ["sequence", "timestamp"],
      "properties": {
        "sequence": {
          "type": "integer",
          "minimum": 0,
          "description": "Monotonically increasing sequence number for replay support"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of message emission"
        }
      }
    }
  }
}
```

### 4.2 Event Message

```json
{
  "type": "event",
  "payload": {
    "event_id": "evt-001",
    "event_type": "observer.created",
    "source": "observer_runtime",
    "priority": "high",
    "data": {
      "observer_id": "obs-abc-123",
      "name": "my-observer"
    }
  },
  "meta": {
    "sequence": 42,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 4.3 Subscription Acknowledgement

```json
{
  "type": "subscription_ack",
  "payload": {
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "patterns": ["observer.*", "entropy.*"],
    "min_priority": "normal",
    "estimated_match_rate": "120/sec"
  },
  "meta": {
    "sequence": 1,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 4.4 Error Message

```json
{
  "type": "error",
  "payload": {
    "code": "INVALID_PATTERN",
    "message": "Pattern 'obser*er.*' contains wildcard at non-boundary position",
    "details": {
      "pattern": "obser*er.*",
      "position": 5
    }
  },
  "meta": {
    "sequence": 2,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 4.5 Rate Limit Warning

```json
{
  "type": "rate_limit_warning",
  "payload": {
    "current_rate": 105,
    "limit": 100,
    "action": "throttle",
    "retry_after_ms": 1000
  },
  "meta": {
    "sequence": 99,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

---

## 5. Client → Server Request Format

### 5.1 Envelope Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "payload"],
  "properties": {
    "type": {
      "type": "string",
      "enum": [
        "authenticate",
        "subscribe",
        "unsubscribe",
        "query",
        "ack",
        "register_observer",
        "unregister_observer",
        "pong"
      ]
    },
    "payload": {
      "type": "object"
    },
    "request_id": {
      "type": "string",
      "description": "Client-generated ID for correlating requests/responses"
    }
  }
}
```

### 5.2 Authenticate

```json
{
  "type": "authenticate",
  "payload": {
    "token": "oce_jwt_token_here",
    "client_version": "1.0.0"
  },
  "request_id": "req-001"
}
```

### 5.3 Subscribe

```json
{
  "type": "subscribe",
  "payload": {
    "patterns": ["observer.*", "entropy.#"],
    "min_priority": "normal",
    "sources": [],
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "request_id": "req-002"
}
```

### 5.4 Unsubscribe

Remove specific patterns:

```json
{
  "type": "unsubscribe",
  "payload": {
    "patterns": ["entropy.#"],
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "request_id": "req-003"
}
```

Remove all patterns (tears down the observer's subscription set):

```json
{
  "type": "unsubscribe",
  "payload": {
    "patterns": ["*"],
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "request_id": "req-004"
}
```

### 5.5 Query

Query the event fabric for current state:

```json
{
  "type": "query",
  "payload": {
    "query": "active_observers"
  },
  "request_id": "req-005"
}
```

Supported queries:

| Query | Response |
|-------|----------|
| `active_observers` | List of currently active observer IDs and metadata |
| `subscription_count` | Total number of active subscriptions |
| `event_rate` | Current events/second across all sources |
| `my_subscriptions` | Current subscriptions for the requesting observer |

**Server response to query:**

```json
{
  "type": "query_result",
  "payload": {
    "query": "active_observers",
    "result": [
      {
        "observer_id": "obs-abc-123",
        "name": "operator-console-1",
        "role": "operator",
        "active_subscriptions": 3,
        "connected_since": "2026-05-16T17:00:00.000Z"
      }
    ]
  },
  "meta": {
    "sequence": 50,
    "timestamp": "2026-05-16T17:49:00.000Z"
  },
  "request_id": "req-005"
}
```

### 5.6 Ack (Acknowledgement)

Acknowledge receipt up to a sequence number. Used for replay support:

```json
{
  "type": "ack",
  "payload": {
    "up_to_sequence": 42
  },
  "request_id": "req-006"
}
```

### 5.7 Unregister Observer

```json
{
  "type": "unregister_observer",
  "payload": {
    "observer_id": "obs-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "request_id": "req-007"
}
```

---

## 6. Error Handling

### 6.1 Error Codes

| Code | HTTP Equivalent | Description | Client Action |
|------|-----------------|-------------|---------------|
| `AUTH_REQUIRED` | 401 | No auth token provided | Send `authenticate` message |
| `AUTH_FAILED` | 403 | Invalid or expired token | Re-authenticate with fresh token |
| `INVALID_PATTERN` | 400 | Malformed filter pattern | Fix pattern syntax, retry |
| `PATTERN_TOO_BROAD` | 400 | Pattern matches too many event types (e.g., `*` alone) | Narrow the pattern |
| `RATE_LIMITED` | 429 | Exceeded events/sec limit | Reduce subscription breadth, wait for `retry_after_ms` |
| `OBSERVER_NOT_FOUND` 404 | Observer ID does not exist | Re-register observer |
| `SUBSCRIPTION_LIMIT` | 400 | Too many subscriptions per observer (max 50) | Remove unused subscriptions |
| `INTERNAL_ERROR` | 500 | Server-side failure | Retry with backoff |
| `INVALID_MESSAGE` | 400 | Malformed JSON or unknown message type | Fix message format |
| `READONLY_MODE` | 503 | Server is in read-only mode (e.g., during failover) | Retry after `Retry-After` header |

### 6.2 Error Response Format

```json
{
  "type": "error",
  "payload": {
    "code": "INVALID_PATTERN",
    "message": "Pattern 'obser*er.*' contains wildcard at non-boundary position",
    "retryable": false,
    "details": {
      "pattern": "obser*er.*",
      "hint": "Wildcards (* and #) must appear at level boundaries: 'observer.*' or 'observer.#'"
    }
  },
  "meta": {
    "sequence": 5,
    "timestamp": "2026-05-16T17:49:00.000Z"
  },
  "request_id": "req-002"
}
```

### 6.3 Connection Loss Behavior

| Scenario | Server Behavior | Client Behavior |
|----------|----------------|-----------------|
| Clean disconnect (client closes) | Remove non-persistent observers, queue events for persistent observers (TTL: 60s) | Reconnect with backoff |
| Network timeout (no pong) | Mark observer `suspended` after 3 missed pings, queue events (TTL: 30s) | Reconnect with backoff |
| Server restart | Persist observer state if `persistent: true`, accept reconnects | Reconnect with backoff, replay from last ack |
| Auth token expiry | Send `error` with `AUTH_FAILED`, close connection | Refresh token, reconnect |

### 6.4 Event Replay After Reconnection

On reconnect, the client sends its last acknowledged sequence number:

```json
{
  "type": "authenticate",
  "payload": {
    "token": "oce_jwt_token_here",
    "last_sequence": 42
  }
}
```

The server replays all events with `sequence > 42` that the client was subscribed to, then sends:

```json
{
  "type": "replay_complete",
  "payload": {
    "replayed_count": 15,
    "first_sequence": 43,
    "last_sequence": 57
  },
  "meta": {
    "sequence": 57,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

**Replay buffer:** The server retains the last 10,000 events per source for replay. If the client's `last_sequence` is older than the buffer, the server sends an `error` with code `REPLAY_UNAVAILABLE` and the client must resubscribe without replay.

---

## 7. Rate Limiting

### 7.1 Limits Per Connection

| Resource | Limit | Window | Action on Exceed |
|----------|-------|--------|-----------------|
| Events delivered | 100/sec | 1 second | Throttle (drop lowest-priority events) |
| Subscribe requests | 10/min | 1 minute | Reject with `RATE_LIMITED` |
| Query requests | 30/min | 1 minute | Reject with `RATE_LIMITED` |
| Auth attempts | 5/min | 1 minute | Reject with `AUTH_FAILED` + 30s cooldown |
| Max subscriptions per observer | 50 | N/A | Reject with `SUBSCRIPTION_LIMIT` |
| Max connections per token | 5 | N/A | Reject new connections with `RATE_LIMITED` |
| Message size | 64 KB | N/A | Close connection with `INVALID_MESSAGE` |

### 7.2 Throttling Behavior

When the event rate exceeds 100/sec for a connection:

1. Events with priority `low` (0) are dropped first.
2. If still over limit, `normal` (1) events are dropped.
3. `high` (2) and `critical` (3) events are NEVER dropped.
4. A `rate_limit_warning` message is sent BEFORE throttling begins (at 80% capacity).

### 7.3 Rate Limit Headers (in warning messages)

```json
{
  "type": "rate_limit_warning",
  "payload": {
    "current_rate": 82,
    "limit": 100,
    "usage_percent": 82,
    "action": "throttle_imminent",
    "retry_after_ms": 0
  },
  "meta": {
    "sequence": 88,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 7.4 Burst Allowance

Clients may burst up to 150 events in a single second, provided the rolling 5-second average remains ≤ 100/sec. This accommodates event fabric bursts during topology transitions.

---

## 8. Authentication

### 8.1 Token-Based Auth (Primary)

Clients authenticate using JWT tokens issued by the OCE auth service.

**Token format:** `oce_<base64url-encoded JWT>`

**Token claims:**

```json
{
  "sub": "user-or-service-id",
  "role": "operator",
  "permissions": ["events:read", "events:subscribe"],
  "iat": 1747417740,
  "exp": 1747421340,
  "iss": "oce-auth"
}
```

### 8.2 Auth Flow

```
Client                                    Server
  |                                          |
  |--- WebSocket connect ------------------->|
  |                                          |
  |<-- {"type": "auth_required"} ------------|
  |                                          |
  |--- {"type": "authenticate", ------------>|
  |      "payload": {"token": "..."}}        |
  |                                          |
  |<-- {"type": "auth_result", --------------|
  |      "payload": {"authenticated": true,  |
  |                  "role": "operator",     |
  |                  "permissions": [...]}}  |
```

### 8.3 Auth Result (Success)

```json
{
  "type": "auth_result",
  "payload": {
    "authenticated": true,
    "role": "operator",
    "permissions": ["events:read", "events:subscribe"],
    "expires_at": "2026-05-16T18:49:00.000Z"
  },
  "meta": {
    "sequence": 0,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 8.4 Auth Result (Failure)

```json
{
  "type": "auth_result",
  "payload": {
    "authenticated": false,
    "reason": "TOKEN_EXPIRED",
    "message": "Token expired at 2026-05-16T17:00:00Z"
  },
  "meta": {
    "sequence": 0,
    "timestamp": "2026-05-16T17:49:00.000Z"
  }
}
```

### 8.5 Permission Model

| Permission | Description |
|------------|-------------|
| `events:read` | Receive events (required for any subscription) |
| `events:subscribe` | Create and manage subscriptions |
| `events:admin` | Subscribe to any event type including `system.*` internal events |
| `observers:manage` | Register/unregister persistent observers |

### 8.6 Private Events

Some event types are restricted and require specific permissions:

| Event Pattern | Required Permission |
|---------------|-------------------|
| `system.*` | `events:admin` |
| `operator.command` | `events:admin` |
| `memory.*` | `events:read` + `observers:manage` |
| All other patterns | `events:read` |

If a client subscribes to a pattern that matches private events without permission, the server returns:

```json
{
  "type": "error",
  "payload": {
    "code": "AUTH_FAILED",
    "message": "Insufficient permission for pattern 'system.*'. Required: events:admin",
    "details": {
      "pattern": "system.*",
      "required_permission": "events:admin"
    }
  }
}
```

### 8.7 Token Refresh

Tokens SHOULD be refreshed before `expiry - 60s`. On expiry:

1. Server sends `error` with code `AUTH_FAILED` / reason `TOKEN_EXPIRED`.
2. Client refreshes token via the REST API (`POST /auth/refresh`).
3. Client sends a new `authenticate` message with the fresh token.
4. Existing subscriptions are preserved during re-auth (no re-subscribe needed).

### 8.8 Anonymous Connections (Development Only)

For local development, the server MAY allow unauthenticated connections with read-only access to public events:

```json
{
  "type": "authenticate",
  "payload": {
    "token": "anonymous"
  }
```

Anonymous connections:
- Can only subscribe to `observer.*`, `attractor.*`, `topology.*` events
- Are limited to 10 events/sec
- Cannot register persistent observers
- Are rejected in production environments

---

## 9. Sequence Numbering & Ordering

### 9.1 Global Sequence

The server maintains a single monotonically increasing sequence counter across all events. Every event message includes its sequence number in `meta.sequence`.

### 9.2 Ordering Guarantees

- **Per-source ordering:** Events from the same source are delivered in sequence order.
- **Cross-source ordering:** Events from different sources MAY be delivered out of order (sequence numbers are global but delivery is parallel).
- **No total ordering guarantee:** Clients MUST NOT assume that sequence 10 happened "before" sequence 11 from a different source in wall-clock time.

### 9.3 Sequence Gaps

If a client detects a gap in sequence numbers (e.g., receives seq 5 then seq 8), it SHOULD send a `nack` (negative acknowledgement):

```json
{
  "type": "nack",
  "payload": {
    "missing_sequences": [6, 7]
  }
}
```

The server will attempt to replay the missing events if they are still in the replay buffer.

---

## 10. Example Session

Below is a complete example session from connection to first event receipt:

```
CLIENT                              SERVER
  |                                    |
  |--- WebSocket connect ------------->|
  |                                    |
  |<-- auth_required ------------------|
  |                                    |
  |--- authenticate (token) ---------->|
  |                                    |
  |<-- auth_result (success) ----------|
  |                                    |
  |--- subscribe (["observer.*"]) ---->|
  |                                    |
  |<-- subscription_ack ---------------|
  |     observer_id: obs-001           |
  |                                    |
  |--- ack (up_to_sequence: 0) ------->|
  |                                    |
  |<-- event (observer.created) -------|
  |     seq: 1                         |
  |                                    |
  |<-- event (observer.activated) -----|
  |     seq: 2                         |
  |                                    |
  |--- ack (up_to_sequence: 2) ------->|
  |                                    |
  |--- unsubscribe (["observer.*"]) -->|
  |                                    |
  |<-- unsub_ack ----------------------|
  |                                    |
  |--- disconnect -------------------->|
```

---

## Appendix A: Complete Message Type Reference

### Server → Client

| Type | Direction | Description |
|------|-----------|-------------|
| `event` | S→C | An event matching the client's subscription |
| `subscription_ack` | S→C | Subscription confirmed |
| `unsub_ack` | S→C | Unsubscription confirmed |
| `auth_result` | S→C | Authentication result (success or failure) |
| `observer_registered` | S→C | Observer registration confirmed |
| `observer_destroyed` | S→C | Observer unregistered/destroyed |
| `error` | S→C | Error notification |
| `ping` | S→C | Heartbeat ping |
| `rate_limit_warning` | S→C | Approaching or exceeding rate limit |
| `replay_complete` | S→C | Event replay finished after reconnect |

### Client → Server

| Type | Direction | Description |
|------|-----------|-------------|
| `authenticate` | C→S | Authenticate with token |
| `subscribe` | C→S | Subscribe to event patterns |
| `unsubscribe` | C→S | Remove event subscriptions |
| `query` | C→S | Query event fabric state |
| `ack` | C→S | Acknowledge receipt up to sequence |
| `nack` | C→S | Request replay of missing sequences |
| `register_observer` | C→S | Explicitly register a persistent observer |
| `unregister_observer` | C→S | Remove a persistent observer |
| `pong` | C→S | Heartbeat response |

---

## Appendix B: Error Code Quick Reference

| Code | Retryable | Typical Cause |
|------|-----------|---------------|
| `AUTH_REQUIRED` | Yes | Forgot to authenticate |
| `AUTH_FAILED` | Yes | Bad/expired token |
| `INVALID_PATTERN` | No | Syntax error in pattern |
| `PATTERN_TOO_BROAD` | No | Pattern `*` without constraints |
| `RATE_LIMITED` | Yes | Too many events or requests |
| `OBSERVER_NOT_FOUND` | No | Bad observer_id |
| `SUBSCRIPTION_LIMIT` | No | >50 subscriptions |
| `INTERNAL_ERROR` | Yes | Server bug |
| `INVALID_MESSAGE` | No | Malformed JSON |
| `READONLY_MODE` | Yes | Server failover in progress |
| `REPLAY_UNAVAILABLE` | No | Client too far behind |

---

## Appendix C: Integration with SRRA-OPH

The Event Subscription Protocol is the real-time interface to the SRRA-OPH substrate. Key integration points:

- **Observer Runtime** emits `observer.*` events that clients can subscribe to.
- **Entropy Economics** emits `entropy.*` events for budget monitoring.
- **Topology Engine** emits `topology.*` events for structural change tracking.
- **Memory System** emits `memory.*` events for snapshot/compression lifecycle.

All SRRA-OPH event types are defined in `event-types.md`. The protocol defined here is the transport layer that delivers those events to clients.
