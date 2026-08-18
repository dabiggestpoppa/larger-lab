# QL-EXEC-R4.1 — Active TB Non-Interference

## Proved by plan

The shadow does not open for write:

- `quant-lab/state/tb_runtime.db`
- `quant-lab/state/tb_control.db`
- `quant-lab/state/tb_supervisor.pid`
- `quant-lab/state/tb_worker.pid`
- `quant-lab/state/tb_desired_state`
- `quant-lab/logs/tb_*.log`

## Proved by authority model

- active TB remains sole operational authority
- no automatic failover / promotion
- legacy PRIMARY (z3 / ±0.25) stays shadow: broker orders = 0
- legacy CONTROL keeps its existing executable canary behaviour, unchanged

## Active TB write audit (to run at R4.2 deploy)

At the end of the live shadow canary, assert via file mtimes + OS-level
access logging that no active-TB path was written by the shadow PID. This is
recorded in the R4.2 close-out, not R4.1.

## R4.1 checkpoint truth

| Field | Value |
|-------|-------|
| active_tb_modified | false |
| active_tb_state_written | false |
| task_scheduler_modified | false |
| active_dashboard_modified | false |
| watcher_absorbed | false |
| dashboard_absorbed | false |

Nothing in this checkpoint modifies the active stack; it only writes plan
artifacts under `research/execution_runtime_foundation/r4_1/`.
