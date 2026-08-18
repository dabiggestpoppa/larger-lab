# QL-EXEC-R4.1 — Process Isolation

## Active TB mutable artifacts (READ ONLY for shadow)

From `quant-lab/runtime/tb_runtime_config.py` (frozen at R4 authority):

| Path | Owner | Shadow policy |
|------|-------|---------------|
| `quant-lab/state/tb_runtime.db` | active TB worker/supervisor | NEVER open for write |
| `quant-lab/state/tb_control.db` | active TB worker | NEVER open for write |
| `quant-lab/state/tb_supervisor.pid` | active supervisor | never create/touch |
| `quant-lab/state/tb_worker.pid` | active worker | never create/touch |
| `quant-lab/state/tb_desired_state` | active desired state | never read-for-write / never write |
| `quant-lab/logs/tb_supervisor.log` | active supervisor | never append |
| `quant-lab/logs/tb_runtime.log` | active worker | never append |
| `quant-lab/logs/tb_dashboard.log` | active dashboard | never append |

## Generic shadow mutable artifacts (ISOLATED)

| Path | Purpose |
|------|---------|
| `shadow_state/tb-generic-shadow-g1/runtime.sqlite` | durable store (WAL) |
| `shadow_state/tb-generic-shadow-g1/shadow.pid` | singleton lock |
| `shadow_state/tb-generic-shadow-g1/shadow_desired_state` | RUNNING / STOPPED_BY_USER |
| `shadow_state/tb-generic-shadow-g1/logs/shadow.log` | shadow logs |
| `shadow_state/tb-generic-shadow-g1/heartbeat.json` | shadow heartbeat |
| `shadow_state/tb-generic-shadow-g1/telemetry.json` | shadow telemetry |

- `runtime_id = "tb-generic-shadow-g1"` (distinct from any active TB id)
- deployment generation distinct from active TB generation
- SQLite path is derived from `runtime_id` only; no path aliasing to
  `quant-lab/state/`.

## Failure isolation requirements

Each of the following MUST leave the active TB stack running and unchanged:

1. generic shadow crash (any point in lifecycle)
2. generic shadow SQLite corruption
3. generic shadow stale heartbeat
4. generic shadow broker-read failure
5. generic shadow market-data mismatch
6. generic shadow CPU spike
7. generic shadow disk-write failure / disk full

Mechanism: the shadow is a separate OS process with no shared lock, no shared
DB connection, no shared memory, no signal handler registration against active
TB PIDs. `shadowctl stop` / `taskkill` of the shadow PID does not touch active
TB PIDs.
