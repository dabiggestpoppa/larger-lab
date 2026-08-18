# QL_EXEC_R0_STATE_ISOLATION_PLAN

Each runtime needs isolated durable paths so a TB DB is never confused with a Rekey DB.

---

## 1. Path layout (keyed by runtime_id)

```
state/<runtime_id>/
  <runtime_id>.db              # runtime status/heartbeat/errors/NAV (SQLite WAL)
  <runtime_id>.pid             # worker pid
  <runtime_id>.supervisor.pid
  <runtime_id>.desired_state   # RUNNING | STOPPED_BY_USER
ledger/<runtime_id>/
  <runtime_id>_events.db       # append-only event ledger
logs/<runtime_id>/
  <runtime_id>.log             # rotating
  <runtime_id>.supervisor.log
  <runtime_id>.dashboard.log
```

TB's current flat layout (`state/tb_runtime.db`, `state/tb_control.db`, `state/tb_worker.pid`, `logs/tb_runtime.log`) maps to `runtime_id = tb-master-01`.

---

## 2. Desired state

`RUNNING` / `STOPPED_BY_USER` per runtime instance, keyed by `runtime_id`. Never one global desired-state file for a multi-account fleet. An intentional stop for one runtime must not stop another.

---

## 3. Database design decision

R0 recommendation: **one DB per runtime** (SQLite/WAL), matching TB's validated model, plus one **fleet registry DB** for the AccountRegistry / RuntimeRegistry / bindings (read-only config + status aggregation). No distributed database, no Redis/Kafka.

Rationale: crash isolation, auditability, reconstruction, low coupling. Per-runtime ledgers stay independent; the fleet DB only holds registry/status metadata, never execution truth.

---

## 4. Process isolation

- One runtime process per directly controlled broker account (default).
- PID singleton per `runtime_id` (PID-file, stale reclaim; never OS-level primitives).
- A future FleetSupervisor supervises many runtimes but never generates signals, changes capital policy, or sends orders.

---

## 5. Isolation invariants

- A runtime cannot open another runtime's DB/ledger/log without an explicit path from its own profile.
- Runtime ids are validated unique at registration (duplicate runtime_id rejected).
- Secrets are scoped to the single account-runtime process.
