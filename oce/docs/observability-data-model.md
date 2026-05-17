# OCE Observability Data Model

> **Author:** OC (OpenClaw) — Analysis / Planning / Coordination
> **Date:** 2026-05-17
> **Phase:** OCE Phase 5 — Observability (OCE-5.6)
> **Status:** Complete
> **Unblocks:** OC2 Dashboard Frontend (OCE-5.9 through OCE-5.13)

---

## Purpose

This document defines the **complete data model** for the OCE Observability Layer. Every metric, trace, and alert follows these schemas. The dashboard frontend (OC2) and API consumers depend on these structures.

---

## 1. Metrics Data Model

### 1.1 MetricSnapshot

Top-level metrics response from `GET /metrics`.

```json
{
  "timestamp": "2026-05-17T02:00:00Z",
  "uptime_seconds": 3600,
  "events": {
    "total": 15234,
    "rate_per_second": 4.23,
    "by_type": {
      "observer.created": 12,
      "observer.event_processed": 14890,
      "observer.health_degraded": 3,
      "entropy.budget_warning": 1
    },
    "avg_latency_ms": 12.4,
    "p99_latency_ms": 89.2
  },
  "observers": {
    "total": 8,
    "active": 6,
    "suspended": 1,
    "error": 1,
    "avg_health": 0.87,
    "error_rate": 0.002
  },
  "memory": {
    "total_entries": 45230,
    "size_bytes": 12582912,
    "compression_ratio": 0.34,
    "layers": {
      "trajectory": 12000,
      "topology": 8000,
      "repair": 3500,
      "attractor": 2100,
      "event": 18000,
      "context": 1730
    }
  },
  "entropy": {
    "consumed": 3400,
    "remaining": 6600,
    "total": 10000,
    "budget_warning": false
  }
}
```

### 1.2 RollingCounter

Internal rolling window counter for rate calculations.

| Field | Type | Description |
|-------|------|-------------|
| `window_seconds` | int | Window size (60, 300, 3600) |
| `count` | int | Events in current window |
| `rate_per_second` float | Computed rate |
| `last_updated` | str (ISO) | Last increment timestamp |

### 1.3 LatencyTracker

Tracks latency distribution for event processing.

| Field | Type | Description |
|-------|------|-------------|
| `count` | int | Total measurements |
| `sum_ms` | float | Sum of all latencies |
| `avg_ms` | float | Mean latency |
| `min_ms` | float | Minimum observed |
| `max_ms` | float | Maximum observed |
| `p99_ms` | float | 99th percentile |

### 1.4 Metrics History

Response from `GET /metrics/history?metric_name=<name>&range=<range>`.

```json
{
  "metric_name": "events.rate_per_second",
  "range": "1h",
  "snapshots": [
    {
      "timestamp": "2026-05-17T01:00:00Z",
      "value": 3.8
    },
    {
      "timestamp": "2026-05-17T01:05:00Z",
      "value": 4.1
    }
  ]
}
```

---

## 2. Tracing Data Model

### 2.1 Trace

Full trace object returned by `GET /traces/{trace_id}`.

```json
{
  "trace_id": "trace-abc123",
  "event_id": "event-xyz789",
  "source": "observer_runtime",
  "status": "completed",
  "outcome": "success",
  "started_at": "2026-05-17T02:00:00.100Z",
  "ended_at": "2026-05-17T02:00:00.189Z",
  "total_latency_ms": 89.0,
  "hops": [
    {
      "hop_index": 0,
      "observer_id": "observer-1",
      "action": "classify",
      "latency_ms": 5.2,
      "metadata": {
        "event_type": "observer.event_processed"
      },
      "timestamp": "2026-05-17T02:00:00.105Z"
    },
    {
      "hop_index": 1,
      "observer_id": "observer-2",
      "action": "route",
      "latency_ms": 12.8,
      "metadata": {
        "target": "observer-3"
      },
      "timestamp": "2026-05-17T02:00:00.118Z"
    }
  ]
}
```

### 2.2 TraceOutcome Enum

| Value | Meaning |
|-------|---------|
| `success` | Event processed successfully end-to-end |
| `error` | Processing failed at one or more hops |
| `dropped` | Event was dropped (no observer available) |
| `timeout` | Processing exceeded TTL |
| `in_progress` | Trace is still active |

### 2.3 TraceHop

| Field | Type | Description |
|-------|------|-------------|
| `hop_index` | int | Order in the trace (0-based) |
| `observer_id` | str | Observer that processed this hop |
| `action` | str | What the observer did |
| `latency_ms` | float | Time spent on this hop |
| `metadata` | object | Additional hop context |
| `timestamp` | str (ISO) | When the hop completed |

### 2.4 Trace Search Filters

Request parameters for `GET /traces` and `POST /traces/search`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | str | Filter by event type |
| `outcome` | str | Filter by outcome |
| `source` | str | Filter by event source |
| `observer_id` | str | Filter by observer |
| `min_latency_ms` | float | Minimum total latency |
| `max_latency_ms` | float | Maximum total latency |
| `since` | str (ISO) | Start time range |
| `until` | str (ISO) | End time range |
| `limit` | int | Max results (default 100) |

---

## 3. Alerting Data Model

### 3.1 Alert

Full alert object returned by `GET /alerts`.

```json
{
  "alert_id": "alert-abc123",
  "rule_id": "rule-456",
  "severity": "critical",
  "state": "firing",
  "title": "Observer health degraded",
  "message": "Observer observer-3 health dropped below 0.3 (current: 0.15)",
  "source": "observer_runtime",
  "created_at": "2026-05-17T02:00:00Z",
  "acknowledged_at": null,
  "resolved_at": null,
  "metadata": {
    "observer_id": "observer-3",
    "health_score": 0.15,
    "threshold": 0.3
  }
}
```

### 3.2 AlertRule

Alert rule configuration from `POST /alerts/rules`.

```json
{
  "rule_id": "rule-456",
  "name": "Observer Health Degraded",
  "description": "Fires when observer health drops below threshold",
  "severity": "critical",
  "condition": {
    "metric": "observer.health_score",
    "operator": "lt",
    "threshold": 0.3
  },
  "cooldown_seconds": 300,
  "auto_resolve": true,
  "enabled": true
}
```

### 3.3 AlertSeverity Enum

| Value | Meaning | Color |
|-------|---------|-------|
| `info` | Informational, no action needed | Blue |
| `warning` | Requires attention | Yellow/Orange |
| `critical` | Immediate action required | Red |

### 3.4 AlertState Enum

| Value | Meaning |
|-------|---------|
| `firing` | Alert is active and not yet acknowledged |
| `acknowledged` | Alert has been acknowledged by an operator |
| `resolved` | Alert condition is no longer true |

### 3.5 Alert Stats

Response from alerting engine stats.

```json
{
  "total_rules": 12,
  "active_rules": 11,
  "firing_alerts": 2,
  "acknowledged_alerts": 1,
  "resolved_alerts_today": 5,
  "by_severity": {
    "info": 0,
    "warning": 1,
    "critical": 2
  }
}
```

---

## 4. WebSocket Stream Formats

### 4.1 WS `/ws/metrics`

Pushes metric snapshots at configurable intervals (default 5s).

```json
{
  "type": "metrics.snapshot",
  "data": { /* MetricSnapshot */ }
}
```

### 4.2 WS `/ws/alerts`

Pushes new alerts and state changes in real-time.

```json
{
  "type": "alert.fired",
  "data": { /* Alert */ }
}
```

Event types: `alert.fired`, `alert.acknowledged`, `alert.resolved`, `alert.rule_added`, `alert.rule_removed`

### 4.3 WS `/ws/events`

Pushes live event stream.

```json
{
  "type": "event",
  "data": {
    "event_id": "evt-789",
    "event_type": "observer.event_processed",
    "source": "observer_runtime",
    "timestamp": "2026-05-17T02:00:00Z",
    "payload": { /* event-specific data */ }
  }
}
```

### 4.4 WS `/ws/observers`

Pushes observer state changes.

```json
{
  "type": "observer.state_change",
  "data": {
    "observer_id": "observer-3",
    "previous_state": "active",
    "new_state": "suspended",
    "timestamp": "2026-05-17T02:00:00Z"
  }
}
```

---

## 5. Database Schema (SQLite)

### 5.1 Metrics Table

```sql
CREATE TABLE IF NOT EXISTS metrics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    labels TEXT DEFAULT '{}'
);
CREATE INDEX idx_metrics_name_time ON metrics_snapshots(metric_name, timestamp);
```

### 5.2 Traces Table

```sql
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    source TEXT NOT NULL,
    outcome TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    total_latency_ms REAL,
    hops TEXT DEFAULT '[]'
);
CREATE INDEX idx_traces_source ON traces(source);
CREATE INDEX idx_traces_outcome ON traces(outcome);
CREATE INDEX idx_traces_started ON traces(started_at);
```

### 5.3 Alerts Table

```sql
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'firing',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    acknowledged_at TEXT,
    resolved_at TEXT,
    metadata TEXT DEFAULT '{}'
);
CREATE INDEX idx_alerts_state ON alerts(state);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

---

## 6. Integration Points

| OCE Component | Data Model | Endpoint | WebSocket |
|---------------|------------|----------|-----------|
| MetricsCollector | MetricSnapshot | `GET /metrics`, `GET /metrics/history` | `/ws/metrics` |
| TracingEngine | Trace, TraceHop | `GET /traces`, `GET /traces/{id}` | `/ws/events` |
| AlertingEngine | Alert, AlertRule | `GET /alerts`, `POST /alerts/rules` | `/ws/alerts` |
| ObserverRuntime | ObserverState | `GET /observers`, `GET /observers/{id}/health` | `/ws/observers` |
| StructuralMemory | MemoryEntry | `GET /memory`, `GET /memory/stats` | — |
| EventFabric | Event | `GET /events`, `POST /events/ingest` | `/ws/events` |
