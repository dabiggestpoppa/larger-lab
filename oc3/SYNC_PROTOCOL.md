# SYNC_PROTOCOL.md — OC2 ↔ OC3 State Exchange

> **Status:** SCAFFOLD — Awaiting OC3 activation
> **Created:** 2026-05-17 21:46 EDT per MAD directive
> **Purpose:** Define the mechanical protocol for dual-node continuity synchronization

---

## Overview

Two continuity execution nodes (OC2, OC3) must maintain state coherence to prevent drift, detect divergence, and enable failure reconstruction. This protocol defines the exchange mechanism.

## Protocol Elements

### 1. Heartbeat Exchange

**Interval:** Every 5 minutes (aligned with OpenClaw heartbeat)

**OC2 → OC3 payload:**
```json
{
  "type": "heartbeat",
  "timestamp": "ISO-8601",
  "node": "OC2",
  "state_hash": "SHA-256 of active state",
  "active_tasks": ["task-id-1", "task-id-2"],
  "subagent_count": 2,
  "drift_score": 0.0,
  "entropy_level": "low|medium|high"
}
```

**OC3 → OC2 response:**
```json
{
  "type": "heartbeat_ack",
  "timestamp": "ISO-8601",
  "node": "OC3",
  "state_hash": "SHA-256 of active state",
  "drift_detected": false,
  "drift_axes": [],
  "recommendation": "none|alert|intervene"
}
```

### 2. State Hash Comparison

**Method:** Both nodes compute SHA-256 over:
- Active task list (sorted by ID)
- Memory index checksum
- Last 5 decisions
- Current session context summary

**Comparison:**
- Hashes match → State coherent
- Hashes differ → Trigger memory diff (element 4)
- Persistent mismatch > 3 heartbeats → Escalate to MAD

### 3. Task Ledger Sync

**Shared file:** `shared-conversations/task-ledger.json`

**Format:**
```json
{
  "tasks": [
    {
      "id": "task-uuid",
      "assigned_to": "agent-id",
      "assigned_by": "OC2",
      "status": "pending|running|complete|failed|timeout",
      "created": "ISO-8601",
      "updated": "ISO-8601",
      "checkpoint": "path/to/checkpoint.md",
      "result": "path/to/result.json"
    }
  ],
  "last_sync": "ISO-8601",
  "sync_node": "OC2|OC3"
}
```

**Rules:**
- OC2 writes new tasks
- OC3 reads and validates task specifications
- Both nodes update status on completion/failure
- Conflicts resolved by timestamp (last-write-wins) + MAD override

### 4. Memory Diff

**Trigger:** State hash mismatch OR drift score > 0.4

**Method:**
1. OC2 sends memory index (file paths + line counts + last-modified)
2. OC3 compares against its own memory index
3. Divergence categorized:
   - **Missing:** File exists on one node but not the other
   - **Stale:** File exists on both but content differs
   - **Extra:** File exists on OC3 but not OC2 (should not happen)

**Resolution:**
- Missing → Copy from source
- Stale → Use most recent version, flag to MAD
- Extra → Archive (don't delete without MAD approval)

### 5. Drift Score + Conflict Resolution

**Drift axes (see DRIFT_SCORE.md):**
1. Context deviation
2. Objective divergence
3. Recursive instability
4. Symbolic inflation
5. Execution inconsistency

**Scoring:**
- Each axis: 0.0 (no drift) to 1.0 (critical drift)
- Composite drift score: weighted average (all axes equal weight)

**Thresholds:**
| Score | Level | Action |
|-------|-------|--------|
| 0.0–0.3 | Green | Normal operation |
| 0.3–0.6 | Yellow | Log drift, increase sync frequency |
| 0.6–0.8 | Orange | Alert MAD, OC3 takes validation role |
| 0.8–1.0 | Red | Halt autonomous ops, MAD intervention required |

**Conflict resolution:**
1. Both nodes present their state to MAD
2. MAD selects correct state
3. Losing node syncs to winning node
4. Conflict logged to `oc3/conflict-log.json`

---

## Transport

**Phase 1 (current):** File-based sync via shared workspace
- Both nodes read/write to `oc3/sync/`
- Polling interval: 5 minutes
- No direct network connection needed

**Phase 2 (future):** WebSocket direct sync
- OC2 and OC3 maintain persistent connection
- Real-time state exchange
- Requires both nodes on same network

---

## Failure Modes

| Scenario | Behavior |
|----------|----------|
| OC2 down | OC3 reconstructs from last sync + task ledger + checkpoints |
| OC3 down | OC2 operates solo, logs all state for later sync |
| Both down | MAD reconstructs from workspace files |
| Split brain | MAD arbitrates, both nodes pause autonomous ops |
| Sync corruption | Rollback to last known good state hash |

---

_Last updated: 2026-05-17 per MAD's OC3 scaffold directive_
