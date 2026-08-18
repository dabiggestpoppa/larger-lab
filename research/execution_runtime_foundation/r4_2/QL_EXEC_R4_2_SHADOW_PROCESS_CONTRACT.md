# QL-EXEC-R4.2 — Shadow Process Contract

## Process

`quant-lab/runtime/tb_generic_shadow.py` — independent, observer only.

Owns:
- `GenericRuntime`-style shadow loop (`ShadowRuntime`: PRIMARY + CONTROL
  adapters over the canonical engine)
- shadow feed consumer (Option B)
- isolated shadow store (`shadow_state/tb-generic-shadow-g1/runtime.sqlite`, WAL)
- parity comparator + telemetry

Does NOT own:
- active broker, active worker, watcher, dashboard, supervisor

## Lifecycle

- manual start via `shadowctl start` (no Task Scheduler / logon autostart)
- `--once` mode: process available records, exit (tests/drills)
- signal stop: SIGINT/SIGTERM -> persist heartbeat, close store, release PID
- PID lock: `shadow.pid` (exclusive); second instance with same runtime_id is
  blocked (SHADOW_ALREADY_RUNNING)
- desired state: `STOPPED_BY_USER` persists; restart respects it

## Isolated state (all under shadow_state/tb-generic-shadow-g1/)

| artifact | purpose |
|----------|---------|
| runtime.sqlite | durable shadow store (WAL) |
| shadow.pid | singleton lock |
| shadow_desired_state | RUNNING / STOPPED_BY_USER |
| logs/shadow.log | shadow logs |
| heartbeat.json | heartbeat snapshot |
| telemetry.json | read-only telemetry |
| parity.jsonl / mismatches.jsonl | parity + mismatch streams |
| legacy_export.jsonl | WRITTEN BY LEGACY WORKER; shadow reads only |

## Purity (enforced by tests)

- no `MetaTrader5` / `mt5` import
- no reference to active TB paths (`tb_runtime.db`, `tb_control.db`,
  `tb_desired_state`, `tb_supervisor.pid`, `tb_worker.pid`)
- no Task Scheduler / dashboard / watcher / supervisor integration
- no plaintext secrets

## Non-interference

- shadow crash / DB corruption / stale heartbeat / feed failure: active TB
  unaffected (separate process, separate state, no shared locks)
- if legacy TB dies: shadow NEVER assumes authority (no failover/promotion)
