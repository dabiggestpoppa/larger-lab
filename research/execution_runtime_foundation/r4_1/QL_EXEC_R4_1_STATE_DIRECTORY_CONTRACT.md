# QL-EXEC-R4.1 — State Directory Contract

## Rule

All generic shadow mutable state is isolated by `runtime_id =
tb-generic-shadow-g1`. No shadow path may alias any active TB path.

```
shadow_state/
  tb-generic-shadow-g1/
    runtime.sqlite           # WAL, schema_versioned (R3 store contract)
    shadow.pid               # singleton lock (separate from active TB pids)
    shadow_desired_state     # RUNNING | STOPPED_BY_USER
    logs/
      shadow.log
    heartbeat.json
    telemetry.json
```

## Explicitly forbidden paths (write)

- `quant-lab/state/tb_runtime.db`
- `quant-lab/state/tb_control.db`
- `quant-lab/state/tb_supervisor.pid`
- `quant-lab/state/tb_worker.pid`
- `quant-lab/state/tb_desired_state`
- `quant-lab/logs/tb_*.log`
- any active TB PID file or desired-state file

## Singleton + desired state (shadow-scoped)

- shadow PID lock: `shadow_state/tb-generic-shadow-g1/shadow.pid`
- shadow desired state: `shadow_state/tb-generic-shadow-g1/shadow_desired_state`
  with values `RUNNING` / `STOPPED_BY_USER`
- restart respects shadow desired state; unexpected crash does not change it

## Boot

G1 is NOT auto-started at Windows logon. First deployment is manual via
`shadowctl start`. Task Scheduler / service auto-start is considered only
after stable evidence.
