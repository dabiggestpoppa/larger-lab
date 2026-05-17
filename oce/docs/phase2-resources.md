# OCE Phase 2 — Resource Assessment: Event Fabric

> **Author:** Sub-AS (Assistant Manager)
> **Date:** 2026-05-16
> **Scope:** External resources needed for Event Fabric production readiness

## Current State

The Event Fabric (`event_fabric.py`) is **in-memory only**. All events are stored in Python lists and dicts. Events are lost on restart. This is acceptable for Phase 2 development but not for production.

## Resource Requirements by Category

### 1. Event Store (Persistence Layer)

**Requirement:** Durable event storage that survives restarts and enables trajectory reconstruction.

#### Option A: SQLite (Recommended for Phase 2)
- **Pros:** Zero configuration, single file, no server needed, Python stdlib support
- **Cons:** Single-writer, limited concurrency, not suitable for high-throughput distributed systems
- **Capacity:** Handles 10K+ events easily on local disk
- **Schema:**
  ```sql
  CREATE TABLE events (
      event_id TEXT PRIMARY KEY,
      event_type TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      source TEXT NOT NULL,
      priority INTEGER DEFAULT 0,
      payload TEXT,  -- JSON
      created_at TEXT DEFAULT (datetime('now'))
  );
  CREATE INDEX idx_events_type ON events(event_type);
  CREATE INDEX idx_events_source ON events(source);
  CREATE INDEX idx_events_timestamp ON events(timestamp);
  CREATE INDEX idx_events_priority ON events(priority);
  ```
- **Effort:** ~2 hours to implement (replace in-memory lists with SQLite backend)
- **Decision:** ✅ **Use SQLite for Phase 2.** Zero external dependencies, fast enough for single-instance OCE.

#### Option B: PostgreSQL (Future — Phase 5+)
- **Pros:** Full ACID, concurrent writes, JSONB for payload, excellent query performance
- **Cons:** Requires server setup, migration effort
- **When to migrate:** When OCE runs multi-instance or needs >100K events
- **Decision:** Defer to Phase 5 (Observability) when metrics and audit trails need durable storage

#### Option C: EventStoreDB (Future — Phase 9+)
- **Pros:** Purpose-built for event sourcing, built-in projections, stream-based model
- **Cons:** Significant operational overhead, .NET ecosystem (has gRPC API)
- **When to migrate:** When OCE needs full event sourcing with projections and catch-up subscriptions
- **Decision:** Defer to Phase 9 (Entropy Economics) if event sourcing becomes core architecture

### 2. Message Queue (Event Streaming)

**Requirement:** Decouple event producers from consumers, enable backpressure handling.

#### Option A: In-Memory asyncio.Queue (Current)
- **Pros:** Zero dependencies, fast, sufficient for single-instance
- **Cons:** Lost on restart, no persistence, no cross-process communication
- **Decision:** ✅ **Keep for Phase 2.** Works for current single-instance architecture.

#### Option B: Redis Streams (Recommended for Phase 3+)
- **Pros:** Persistent streams, consumer groups, backpressure, XREAD/XADD API maps well to event model
- **Cons:** Requires Redis server (~100MB RAM), additional operational dependency
- **Capacity:** Millions of events, sub-millisecond latency
- **When to add:** When Observer Runtime needs reliable event delivery across restarts
- **Decision:** Add in Phase 3 if observer state persistence requires event replay. Otherwise defer to Phase 5.

#### Option C: RabbitMQ (Alternative)
- **Pros:** Mature, flexible routing, dead letter queues, management UI
- **Cons:** Heavier than Redis, more complex configuration
- **Decision:** Not recommended. Redis Streams is lighter and sufficient for OCE's event model.

### 3. Cache Layer

**Requirement:** Fast access to recent events, observer state, health metrics.

#### Option A: In-Memory Dict (Current)
- **Pros:** Fastest possible, zero dependencies
- **Cons:** No sharing across processes, lost on restart
- **Decision:** ✅ **Keep for Phase 2.**

#### Option B: Redis (Future — Phase 5+)
- **Pros:** Shared cache, TTL support, pub/sub for real-time updates
- **Cons:** Additional dependency
- **When to add:** When frontend needs shared state across multiple OCE instances
- **Decision:** Bundle with Redis Streams adoption (Phase 3+ or Phase 5)

### 4. Search & Query

**Requirement:** Full-text search across event payloads, time-range queries, complex filtering.

#### Option A: Python List Filtering (Current)
- **Pros:** Simple, no dependencies
- **Cons:** O(n) filtering, no full-text search, no indexing
- **Decision:** ✅ **Acceptable for Phase 2** (event volume is low)

#### Option B: SQLite FTS5 (Phase 2+)
- **Pros:** Built into SQLite, full-text search, no additional dependency
- **Cons:** Basic search only (no fuzzy matching, no relevance scoring)
- **Decision:** Add when event volume exceeds 10K or full-text search is needed

#### Option C: Elasticsearch (Future — Phase 5+)
- **Pros:** Full-text search, aggregations, time-series, Kibana dashboards
- **Cons:** Heavy resource usage (~1GB RAM), operational complexity
- **Decision:** Defer to Phase 5 (Observability) when metrics dashboards are needed

### 5. Monitoring & Observability

**Requirement:** Track event throughput, latency, error rates, subscriber health.

#### Option A: In-Memory Stats (Current)
- **Pros:** Simple counters in `get_stats()`
- **Cons:** No history, no alerting, no visualization
- **Decision:** ✅ **Acceptable for Phase 2**

#### Option B: Prometheus + Grafana (Phase 5)
- **Pros:** Industry standard, excellent for time-series, Grafana dashboards
- **Cons:** Additional infrastructure
- **Decision:** Phase 5 (Observability) — this is the observability phase

## Recommended Resource Plan

### Phase 2 (Current) — In-Memory Only
| Resource | Choice | Rationale |
|----------|--------|-----------|
| Event Store | In-memory lists | Zero deps, fast iteration |
| Message Queue | asyncio.Queue | Sufficient for single instance |
| Cache | In-memory dict | Fastest, no deps |
| Search | Python list filtering | Low volume, simple |
| Monitoring | In-memory counters | Basic stats sufficient |

**External dependencies:** None (pure Python + FastAPI)

### Phase 3 (Observer Runtime) — Add Persistence
| Resource | Choice | Rationale |
|----------|--------|-----------|
| Event Store | SQLite | Observer state must survive restarts |
| Message Queue | asyncio.Queue | Still sufficient (single instance) |
| Cache | In-memory dict | No change needed |
| Search | SQLite FTS5 | If event volume grows |
| Monitoring | In-memory counters | Add Prometheus metrics endpoint |

**External dependencies:** None (SQLite is stdlib)

### Phase 5 (Observability) — Add Production Infrastructure
| Resource | Choice | Rationale |
|----------|--------|-----------|
| Event Store | PostgreSQL | Multi-instance, concurrent writes |
| Message Queue | Redis Streams | Reliable delivery, consumer groups |
| Cache | Redis | Shared state, TTL |
| Search | Elasticsearch | Full-text search, aggregations |
| Monitoring | Prometheus + Grafana | Metrics, alerting, dashboards |

**External dependencies:** PostgreSQL, Redis, Elasticsearch, Prometheus, Grafana

## Capacity Planning

### Current Load (Phase 2)
- Events: ~100-1000 per session
- Observers: 4-8 active
- Subscribers: 5-10
- WebSocket clients: 1-3
- **In-memory is more than sufficient**

### Expected Load (Phase 3-4)
- Events: ~10K-100K per day
- Observers: 10-50 active
- Subscribers: 20-50
- WebSocket clients: 5-10
- **SQLite persistence needed, in-memory cache still sufficient**

### Future Load (Phase 5+)
- Events: ~1M+ per day
- Observers: 100+ active
- Subscribers: 200+
- WebSocket clients: 50+
- **PostgreSQL + Redis needed**

## Cost Estimate

| Phase | Infrastructure | Monthly Cost |
|-------|---------------|-------------|
| Phase 2 | None (local only) | $0 |
| Phase 3 | SQLite (local file) | $0 |
| Phase 5 | PostgreSQL + Redis + Elasticsearch | ~$50-200/mo (cloud) or $0 (self-hosted) |

## Decision Summary

**For Phase 2:** No external resources needed. In-memory is correct for the current development phase.

**For Phase 3:** Add SQLite for event persistence (observer state must survive restarts). This is the only change needed.

**For Phase 5:** Evaluate PostgreSQL + Redis when multi-instance deployment and observability dashboards are required.

**Key principle:** Don't add infrastructure until the architecture requires it. Every external dependency is an operational cost and a potential failure point. The current in-memory design is correct for Phase 2.
