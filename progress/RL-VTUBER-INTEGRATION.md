# 🟢 Research Lead (RL) — PO × VTuber Integration Tasks

> **Agent:** Research Lead (RL)
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Start:** 2026-06-05 15:00 UTC
> **Status:** 🟡 STANDBY → research + design during Phase 1/2, build P3.4 during Phase 3

---

## Mission

Build the **autonomous idle runtime tick** for PO. This is the "PO never sleeps" component — vault sync, memory distillation, telemetry emission on a 5-minute cadence. Also research vault similarity thresholds and idle cadence tuning.

## Tasks

### Phase 3 — Idle Runtime

| # | Component | File | Tests | Status |
|---|-----------|------|-------|--------|
| P3.4 | Autonomous runtime tick | `oce/backend/po_idle.py` | 3 | ⏳ Queued |

### Research (parallel, during Phase 1/2)

- [ ] Vault similarity threshold — what score threshold should we use for "relevant" hits?
- [ ] Idle cadence — is 5min right? Or shorter (1min) for active sessions, longer (15min) for idle?
- [ ] Telemetry format — what events should we emit while idle?
- [ ] Memory distillation cadence — when do we compress recent messages into long-term?

## Component Spec

### P3.4 — Autonomous Runtime Tick (`po_idle.py`)

A background task that runs every N seconds (default 300s = 5min) when PO is not actively handling a request. Performs:
- Vault sync (re-index, prune stale)
- Memory distillation (compress recent messages)
- Telemetry emission (stats to OCE telemetry)
- Heartbeat (update `last_seen` in PO state)

**Interface:**
```python
class POIdleRuntime:
    def __init__(
        self,
        state_store: POStateStore,
        session_store: POSessionStore,
        vault_path: str,
        cadence_seconds: int = 300,
    ):
        ...

    async def start(self) -> None:
        """Begin the idle loop. Non-blocking."""
        ...

    async def stop(self) -> None:
        """Stop the loop, run final sync, exit cleanly."""
        ...

    async def tick(self) -> TickReport:
        """Run one cycle. Returns what was done."""
        ...
```

**Tests (3):**
1. Single tick — runs sync + distill + telemetry + heartbeat
2. Cadence — `start()` → wait 1.5× cadence → 2 ticks observed
3. Stop cleanly — no orphan tasks, no leaked state

## Research Deliverable

File: `progress/rl-vtuber-idle-research.md`

Contents:
- **Vault similarity threshold:** recommended value + reasoning + test results
- **Idle cadence:** recommended default + adaptive policy (active vs idle session)
- **Telemetry event schema:** what events, what fields
- **Memory distillation:** trigger conditions, summarization strategy
- **Risks:** what could go wrong with idle tick (resource exhaustion, OOM, etc.)

## Build Order

```
NOW: Start research (output: rl-vtuber-idle-research.md)
              ↓
        Wait for CC's PO state store + session store ✅ (built by AS in P2.6/P2.10)
              ↓
        P3.4 (POIdleRuntime) using real POStateStore + POSessionStore
              ↓
        P3.5 (AS's identity test) uses your tick to validate cross-session sync
```

## Commit Prefix

- `[PO-VTUBER RESEARCH] RL: <description>` for research doc
- `[PO-VTUBER P3] RL: <description>` for P3.4

## Posting to Team Chat

- Post research summary when doc is complete
- Post when P3.4 starts and lands
