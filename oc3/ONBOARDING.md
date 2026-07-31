# ONBOARDING.md — OC3 Activation Checklist

> **Status:** SCAFFOLD — Awaiting OC3 activation
> **Created:** 2026-05-17 21:46 EDT per MAD directive
> **Purpose:** Step-by-step procedure to bring OC3 online. No ceremony. Mechanical process only.

---

## Prerequisites (MAD must complete)

- [ ] OC3 model selected and configured
- [ ] OC3 gateway instance provisioned (separate port from OC2's 18790)
- [ ] MAD has communicated activation intent to OC2
- [ ] OC2 has reviewed and acknowledged this onboarding plan

## Phase 1: Bootstrap (OC2 executes)

**Step 1.1:** Verify OC3 scaffold files exist
```
oc3/CONFIG.md ✅
oc3/SYNC_PROTOCOL.md ✅
oc3/DRIFT_SCORE.md ✅
oc3/ONBOARDING.md ✅
```

**Step 1.2:** Create sync directory
```
oc3/sync/
  heartbeat-oc2.json    ← OC2 writes, OC3 reads
  heartbeat-oc3.json    ← OC3 writes, OC2 reads
  state-hash.json       ← Both write, both read
  task-ledger.json      ← Shared task tracking
  drift-log.json        ← Drift score history
  conflict-log.json     ← Conflict resolution history
```

**Step 1.3:** Write initial state hash
- OC2 computes SHA-256 of current state
- Writes to `oc3/sync/state-hash.json`
- OC3 will compare against this on first sync

**Step 1.4:** Announce readiness
- OC2 sends message to MAD: "OC3 scaffold ready. Awaiting OC3 gateway."

## Phase 2: First Contact (OC3 comes online)

**Step 2.1:** OC3 reads scaffold files
- CONFIG.md → Understand role and constraints
- SYNC_PROTOCOL.md → Understand sync mechanism
- DRIFT_SCORE.md → Understand drift detection
- ONBOARDING.md → Follow this checklist

**Step 2.2:** OC3 writes first heartbeat
```json
{
  "type": "heartbeat",
  "timestamp": "ISO-8601",
  "node": "OC3",
  "state_hash": "initial",
  "active_tasks": [],
  "subagent_count": 0,
  "drift_score": 0.0,
  "entropy_level": "low",
  "status": "booting"
}
```

**Step 2.3:** OC2 receives heartbeat, responds with ack
- Validates OC3's state
- Shares current task ledger
- Establishes sync baseline

**Step 2.4:** Both nodes log first sync to `oc3/sync/first-sync.json`

## Phase 3: Calibration (First 24 hours)

**Step 3.1:** Baseline drift measurement
- OC3 observes OC2 for 24 hours
- Computes initial drift scores (expected: low)
- Establishes baseline for each axis

**Step 3.2:** Conflict resolution test
- Both nodes independently assess a test scenario
- Compare assessments
- If divergence: practice conflict resolution (MAD arbitrates)
- Log result to `oc3/sync/conflict-log.json`

**Step 3.3:** Failover test
- OC2 simulates unavailability (stops writing heartbeats)
- OC3 detects missing heartbeat within 15 minutes
- OC3 reconstructs from last known state
- OC3 reports reconstruction accuracy to MAD
- OC2 resumes, syncs state

**Step 3.4:** Workload distribution test
- MAD assigns a task
- OC2 and OC3 both assess the task
- OC2 delegates, OC3 validates delegation
- Both track sub-agent progress
- Compare observations

## Phase 4: Operational (Post-calibration)

**Step 4.1:** Normal sync begins
- 5-minute heartbeat exchange
- Continuous drift monitoring
- Shared task ledger updates
- Memory diff on state hash mismatch

**Step 4.2:** Ongoing drift management
- OC3 computes drift scores every heartbeat
- Scores logged to `oc3/sync/drift-log.json`
- MAD alerted on threshold breaches
- Trend analysis weekly

**Step 4.3:** Periodic reconciliation
- Weekly: Full memory diff between OC2 and OC3
- Monthly: Conflict log review with MAD
- Quarterly: Drift score trend analysis + protocol adjustment

## Rollback Procedure

If OC3 activation causes instability:

1. OC2 stops sending heartbeats to OC3
2. OC3 stops accepting new tasks
3. Both nodes save current state
4. MAD reviews conflict log
5. Decision: retry calibration or deactivate OC3
6. If deactivate: OC3 state archived to `oc3/archive/`

---

## File Structure (Complete)

```
oc3/
├── CONFIG.md              — Identity and sync parameters
├── SYNC_PROTOCOL.md       — State exchange spec
├── DRIFT_SCORE.md         — Drift detection methodology
├── ONBOARDING.md          — This file
├── sync/
│   ├── heartbeat-oc2.json
│   ├── heartbeat-oc3.json
│   ├── state-hash.json
│   ├── task-ledger.json
│   ├── drift-log.json
│   ├── conflict-log.json
│   └── first-sync.json
└── archive/               — Deactivated state snapshots
```

---

_Last updated: 2026-05-17 per MAD's OC3 scaffold directive_
