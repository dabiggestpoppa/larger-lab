# OCE Observability System Map

> **Author:** OC (OpenClaw) — Analysis / Planning / Coordination
> **Date:** 2026-05-17
> **Phase:** OCE Phase 5 — Observability (OCE-5.7)
> **Status:** Complete
> **Purpose:** What to monitor per layer, what alerts to configure, what traces to capture

---

## Purpose

This document is the **operator's guide** to what matters in each OCE layer. It maps every subsystem to its key metrics, alert conditions, and trace points. Use this to configure dashboards and alert rules.

---

## Layer 1: OCE Continuity Core (FastAPI)

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Request latency (p99) | Middleware | > 200ms | > 1000ms |
| Error rate | Middleware | > 1% | > 5% |
| Active WebSocket connections | ConnectionManager | > 80% capacity | 100% capacity |
| Chat response time | `/chat` endpoint | > 2s | > 10s |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| API High Latency | warning | p99 > 200ms for 5min |
| API Critical Latency | critical | p99 > 1000ms for 2min |
| API Error Rate High | critical | Error rate > 5% for 2min |
| WebSocket Saturation | warning | Connections > 80% capacity |

### Trace Points

- `chat.request_received` → `chat.response_sent` (full chat pipeline)
- `ws.connection_opened` → `ws.connection_closed` (WebSocket lifecycle)

---

## Layer 2: Event Fabric

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Event ingestion rate | EventFabric | < 100/s sustained | 0 for > 30s |
| Event processing latency | EventFabric | > 50ms avg | > 500ms avg |
| Event drop rate | EventFabric | > 0.1% | > 1% |
| Subscriber count | EventFabric | < expected | 0 |
| Persistence queue depth | EventPersistence | > 1000 | > 10000 |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| Event Ingestion Drop | critical | Rate drops to 0 for > 30s |
| Event Processing Slow | warning | Avg latency > 50ms for 5min |
| Event Drop Rate High | critical | Drop rate > 1% for 2min |
| Persistence Backlog | warning | Queue depth > 1000 for 5min |
| No Subscribers | critical | Subscriber count = 0 for any event type |

### Trace Points

- `event.ingested` → `event.classified` → `event.routed` → `event.persisted` (full event lifecycle)
- Per-hop: observer processing time, routing decisions

---

## Layer 3: Observer Runtime

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Active observers | ObserverRuntime | < expected count | 0 |
| Observer health score | ObserverHealth | < 0.7 | < 0.3 |
| Observer entropy consumption | ObserverHealth | > 70% of budget | > 90% of budget |
| Observer error rate | ObserverRuntime | > 1% | > 5% |
| Event processing time per observer | ObserverRuntime | > 100ms avg | > 1s avg |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| Observer Health Degraded | warning | Health < 0.7 for 5min |
| Observer Health Critical | critical | Health < 0.3 for 2min |
| Observer Entropy Exhaustion | critical | Entropy > 90% of budget |
| Observer Error Rate High | critical | Error rate > 5% for 2min |
| All Observers Down | critical | Active count = 0 |
| Observer Stuck | warning | No events processed for 10min |

### Trace Points

- `observer.event_received` → `observer.event_processed` (per-event processing)
- `observer.state_change` (lifecycle transitions: created → active → suspended → destroyed)
- `observer.repair_triggered` → `observer.repair_completed` (repair cycle)

---

## Layer 4: Structural Memory

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Total memory entries | StructuralMemory | > 100K | > 500K |
| Memory size (bytes) | StructuralMemory | > 50MB | > 200MB |
| Compression ratio | StructuralMemory | < 0.3 | < 0.1 |
| Search query latency | StructuralMemory | > 500ms | > 2s |
| Reconstruction success rate | StructuralMemory | < 95% | < 80% |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| Memory Size Warning | warning | Size > 50MB |
| Memory Size Critical | critical | Size > 200MB |
| Compression Degraded | warning | Ratio < 0.3 for 1hr |
| Search Latency High | warning | P99 > 500ms for 5min |
| Reconstruction Failures | critical | Success rate < 80% |

### Trace Points

- `memory.store_requested` → `memory.store_completed` (write path)
- `memory.search_requested` → `memory.search_completed` (query path)
- `memory.compression_started` → `memory.compression_completed` (compression cycle)
- `memory.reconstruction_started` → `memory.reconstruction_completed` (rebuild)

---

## Layer 5: SRRA-OPH Substrate

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| SRRS adapter health | SRRSAdapter | Degraded | Unavailable |
| Patch sync success rate | SRRA-OPH | < 99% | < 95% |
| Topology convergence time | SRRA-OPH | > 5s | > 30s |
| Entropy budget remaining | EntropyEconomics | < 30% | < 10% |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| SRRS Adapter Degraded | warning | Health check fails 2/3 |
| SRRS Adapter Down | critical | Health check fails 3/3 |
| Patch Sync Failures | critical | Sync rate < 95% for 5min |
| Topology Divergence | warning | Convergence > 30s |
| Entropy Budget Low | warning | Remaining < 30% |
| Entropy Budget Exhausted | critical | Remaining < 10% |

### Trace Points

- `srra.patch_sync_started` → `srra.patch_sync_completed`
- `srra.topology_update` (topology changes)
- `srra.entropy_consumed` (entropy accounting)

---

## Layer 6: DSPy Pipelines

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Pipeline success rate | OCEPipelineManager | < 90% | < 70% |
| Classification accuracy | EventClassifier | < 85% | < 70% |
| Routing accuracy | EventRouter | < 90% | < 75% |
| Pipeline latency | OCEPipelineManager | > 500ms | > 2s |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| Pipeline Degraded | warning | Success rate < 90% for 10min |
| Pipeline Failure | critical | Success rate < 70% for 5min |
| Classification Accuracy Low | warning | Accuracy < 85% for 15min |

---

## Layer 7: Frontend Dashboard

### What to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Page load time | Browser | > 3s | > 10s |
| WebSocket reconnect rate | Browser | > 1/min | > 5/min |
| Render frame drops | Browser | > 5% | > 20% |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| Dashboard WS Disconnected | warning | Reconnect rate > 1/min |
| Dashboard Unresponsive | critical | Page unresponsive > 30s |

---

## Recommended Default Alert Rules

These should be pre-configured when OCE starts:

```json
[
  {
    "name": "API High Latency",
    "severity": "warning",
    "condition": {"metric": "api.latency_p99", "operator": "gt", "threshold": 200},
    "cooldown_seconds": 300
  },
  {
    "name": "Observer Health Critical",
    "severity": "critical",
    "condition": {"metric": "observer.health_score", "operator": "lt", "threshold": 0.3},
    "cooldown_seconds": 120
  },
  {
    "name": "Event Ingestion Stopped",
    "severity": "critical",
    "condition": {"metric": "events.rate_per_second", "operator": "eq", "threshold": 0},
    "cooldown_seconds": 60
  },
  {
    "name": "Entropy Budget Exhausted",
    "severity": "critical",
    "condition": {"metric": "entropy.remaining_pct", "operator": "lt", "threshold": 10},
    "cooldown_seconds": 300
  },
  {
    "name": "Memory Size Critical",
    "severity": "critical",
    "condition": {"metric": "memory.size_bytes", "operator": "gt", "threshold": 209715200},
    "cooldown_seconds": 600
  },
  {
    "name": "SRRS Adapter Down",
    "severity": "critical",
    "condition": {"metric": "srra.health", "operator": "eq", "threshold": 0},
    "cooldown_seconds": 120
  }
]
```

---

## Dashboard Panel Layout

Recommended layout for the observability dashboard (OC2 frontend):

```
┌─────────────────────────────────────────────────────────────┐
│  OCE Observability Dashboard                    [Live 🟢]   │
├──────────────────┬──────────────────┬───────────────────────┤
│  MetricsPanel    │  SystemMap       │  AlertPanel           │
│  ─────────────   │  ────────────    │  ───────────          │
│  Event Rate      │  Topology Graph  │  🔴 Critical (2)     │
│  Observer Health │  Health Colors   │  🟡 Warning (1)      │
│  Memory Usage    │  Active Links    │  ℹ️ Info (0)         │
│  Entropy Budget  │                  │  [Ack] [Resolve]      │
├──────────────────┴──────────────────┴───────────────────────┤
│  TraceView                                                    │
│  ─────────                                                   │
│  [Trace Timeline] [Filter: event_type ▾] [Filter: outcome ▾] │
│  trace-abc123 ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✅ 89ms           │
│  trace-def456 ━━━━━━━━━━━━━━━╸──────────── ❌ 234ms         │
│  trace-ghi789 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ⏳ in_progress   │
└──────────────────────────────────────────────────────────────┘
```
