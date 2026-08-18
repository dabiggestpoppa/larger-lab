# QL_EXEC_R0_FLEET_SUPERVISOR_PLAN

Long-term target: a FleetSupervisor that manages process lifecycle across many runtime profiles, above the per-runtime supervisor/worker split.

---

## 1. Responsibilities (allowed)

- discover enabled runtime profiles;
- start runtime;
- stop runtime (intentional);
- restart failed runtime with bounded backoff;
- heartbeat audit;
- singleton enforcement per `runtime_id`;
- aggregate status (online/offline/degraded/blocked/reconciling).

## 2. Non-responsibilities (never)

- generate signals;
- change capital policy;
- send strategy orders directly;
- touch broker sessions or accounts.

---

## 3. Layering

```
FleetSupervisor  (many runtime profiles)
  -> per-runtime Supervisor  (one worker process lifecycle)
      -> generic_worker (strategy adapter + broker session + capital policy)
```

The existing TB supervisor stays the per-runtime supervisor. It is genericized only after proving TB equivalence (R3/R4).

---

## 4. Singleton and isolation

- PID-file singleton per `runtime_id` (never OS-level primitives).
- FleetSupervisor itself is a singleton (PID file).
- Desired state is keyed by `runtime_id`.

---

## 5. Local-first

The fleet supervisor runs on the local Windows machine (or a future Windows VPS). No Railway/Linux-cloud relocation, no Kubernetes, no service mesh. Windows Task Scheduler-style boot start stays the operator's domain; this workstream proposes PID-file supervision, not new OS-level persistent artifacts.
