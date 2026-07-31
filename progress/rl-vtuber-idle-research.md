# 🟢 RL Research — PO Idle Runtime Design

> **Author:** Research Lead (RL)
> **Date:** 2026-06-05
> **For:** P3.4 — Autonomous Runtime Tick (`oce/backend/po_idle.py`)
> **Status:** DRAFT — research complete, awaiting P2.6/P2.10 dependencies

---

## 1. Vault Similarity Threshold

**Question:** What score threshold for "relevant" vault hits?

**Findings:**

The existing vault system (`core/obsidian/`) uses `VaultWriter` with category-based organization (doctrine, memory, skills, architecture, journals). The `structural_memory.py` engine uses SQLite + FTS5 for full-text search across 3 layers (WORK/LEARNED/KNOWLEDGE).

**Recommendation:**
- **FTS5 rank threshold:** 0.3 (catches partial matches, avoids noise)
- **Max hits:** 5 per query (top-5 by rank)
- **Freshness bias:** Boost entries modified within last 24h by 1.5x
- **Category filter:** Only search `memory/` and `doctrine/` by default; `skills/` and `architecture/` on explicit request

**Rationale:** FTS5 bm25 scores are unbounded and dataset-dependent. 0.3 is conservative — better to return slightly too many hits and let the LLM filter than miss critical context. The freshness bias ensures recent operational state (e.g., "Phase 2 in progress") outranks stale entries.

---

## 2. Idle Cadence

**Question:** Is 5min right? Or adaptive?

**Findings:**

`scripts/po_heartbeat.py` already uses 300s (5min) as default interval. This is proven in production — PO has been running heartbeats at this cadence for weeks without issues.

**Recommendation: Adaptive cadence with 3 tiers:**

| Session State | Cadence | Rationale |
|---------------|---------|-----------|
| Active (request in-flight or <30s since last) | 60s | Fast vault sync while user is talking |
| Warm (last request <5min ago) | 300s (5min) | Standard — matches existing heartbeat |
| Cold (idle >5min) | 900s (15min) | Save resources, still keep state fresh |

**Implementation:**
```python
def _compute_cadence(self) -> int:
    elapsed = time.time() - self._last_request_time
    if elapsed < 30:
        return 60    # active
    elif elapsed < 300:
        return 300   # warm
    else:
        return 900   # cold
```

**Why not fixed 5min?** During active VTuber conversations, vault context can change rapidly (new entries written by other agents). 60s keeps the index fresh. During idle, 15min saves API calls and CPU.

---

## 3. Telemetry Event Schema

**Question:** What events should we emit while idle?

**Findings:**

OCE already has `event_fabric.py` with `EventFabric`, `TopologicalRouter`, and `EventPersistence`. Events are persisted to SQLite. The existing PO streamer (`tools/po_streamer.py`) polls the DB and forwards to team chat + vault.

**Recommendation: Emit these idle telemetry events:**

```json
// Tick heartbeat — every cycle
{
  "event_type": "po_idle_tick",
  "source": "po_idle",
  "data": {
    "cadence_seconds": 300,
    "session_state": "warm",
    "vault_entries_total": 142,
    "memory_work_count": 23,
    "memory_learned_count": 89,
    "uptime_seconds": 86400
  }
}

// Vault sync — when re-index completes
{
  "event_type": "po_vault_sync",
  "source": "po_idle",
  "data": {
    "entries_indexed": 142,
    "entries_pruned": 3,
    "index_duration_ms": 45
  }
}

// Memory distillation — when compression runs
{
  "event_type": "po_memory_distill",
  "source": "po_idle",
  "data": {
    "work_compressed": 5,
    "learned_created": 2,
    "compression_ratio": 0.4
  }
}

// Health alert — when something is wrong
{
  "event_type": "po_health_warning",
  "source": "po_idle",
  "data": {
    "issue": "vault_index_stale",
    "details": "Last index 45min ago, expected <15min"
  }
}
```

**Why these events?** They map directly to the 4 responsibilities of the idle tick (vault sync, memory distill, telemetry, heartbeat). The `po_idle_tick` is the heartbeat — always emitted. The others are conditional — only when work was actually done.

---

## 4. Memory Distillation

**Question:** When do we compress recent messages into long-term?

**Findings:**

`structural_memory.py` has 3 layers:
- **WORK** — ephemeral, high-turnover (recent messages, scratch state)
- **LEARNED** — compressed patterns, distilled insights
- **KNOWLEDGE** — stable, rarely changes (doctrine, principles)

The existing system has `compress_trace()` in `core/obsidian/compressor.py` for trace compression.

**Recommendation: Trigger conditions + strategy:**

| Trigger | Action |
|---------|--------|
| WORK layer > 50 entries | Compress oldest 20 WORK entries → 5 LEARNED entries |
| WORK entry age > 1 hour | Move to compression queue |
| Explicit `/distill` command | Force full compression pass |

**Compression strategy:**
1. Group WORK entries by topic (tag-based clustering)
2. Summarize each cluster into 1 LEARNED entry (LLM-assisted or rule-based)
3. Preserve key facts, discard procedural details
4. Tag LEARNED entries with source WORK entry IDs for traceability

**For P3.4 (no LLM in idle tick):** Use rule-based compression — concatenate content, extract key-value pairs, compute stats. LLM-assisted distillation is a Phase 4+ enhancement.

---

## 5. P3.4 Component Design

### Interface

```python
class POIdleRuntime:
    """Autonomous idle runtime — PO never sleeps."""

    def __init__(
        self,
        state_store,       # POStateStore (from P2.10)
        session_store,     # POSessionStore (from P2.6)
        vault_path: str,   # Path to O2C-VAULT
        event_fabric=None, # OCE EventFabric (optional, for telemetry)
        cadence_seconds: int = 300,
    ):
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_request_time = 0.0
        self._tick_count = 0

    async def start(self) -> None:
        """Begin the idle loop. Non-blocking."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the loop, run final sync, exit cleanly."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._final_sync()

    async def tick(self) -> TickReport:
        """Run one cycle. Returns what was done."""
        report = TickReport(ts=time.time(), cadence=self._compute_cadence())
        report.vault_sync = await self._vault_sync()
        report.memory_distill = await self._memory_distill()
        report.telemetry = await self._emit_telemetry(report)
        report.heartbeat = await self._update_heartbeat()
        self._tick_count += 1
        return report

    def notify_request(self) -> None:
        """Call when PO handles a request (resets active timer)."""
        self._last_request_time = time.time()
```

### Dependencies

| Dependency | Source | Status |
|------------|--------|--------|
| POStateStore | P2.10 (AS) | ⏳ Not built yet |
| POSessionStore | P2.6 (AS) | ⏳ Not built yet |
| EventFabric | Existing | ✅ Available |
| StructuralMemory | Existing | ✅ Available |
| VaultWriter | Existing | ✅ Available |

### Tests (3)

1. **Single tick** — `tick()` runs vault_sync + memory_distill + telemetry + heartbeat, returns TickReport with all fields populated
2. **Cadence** — `start()` → sleep 1.5× cadence → verify 2 ticks observed via tick_count
3. **Stop cleanly** — `stop()` → no orphan asyncio.Tasks, no leaked state, final_sync ran

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Vault re-index is slow (>1s) | Low | Tick takes too long | Cache index; only re-index on file watch events |
| Memory distillation OOM | Low | Crash | Limit WORK entries processed per tick (max 50) |
| Event fabric unavailable | Medium | No telemetry | Graceful degradation — log locally, retry next tick |
| Tick overlaps (slow tick + fast cadence) | Low | Duplicate work | Use asyncio.Lock per tick; skip if previous tick still running |
| Stale state after long idle | Medium | Outdated context | Cold cadence (15min) still runs; vault sync refreshes |

---

## 7. Relationship to Existing PO Infrastructure

**Key insight:** `scripts/po_heartbeat.py` already does 80% of what P3.4 needs. The difference:

| Feature | po_heartbeat.py | po_idle.py (P3.4) |
|---------|-----------------|-------------------|
| Runtime | sync subprocess loop | async (FastAPI native) |
| Cadence | Fixed 300s | Adaptive (60/300/900s) |
| Vault sync | No | Yes (re-index + prune) |
| Memory distill | No | Yes (WORK → LEARNED) |
| Telemetry | Team chat + Telegram | OCE event fabric |
| State store | JSON file | POStateStore (SQLite) |
| Session awareness | No | Yes (via POSessionStore) |

**Migration path:** Once `po_idle.py` is built and tested, `po_heartbeat.py` can be deprecated. The launcher (`po_launcher.py`) would no longer need to start it as a separate process.

---

**Next step:** Wait for AS to deliver POStateStore (P2.10) and POSessionStore (P2.6), then build P3.4.
