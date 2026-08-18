# QL-EXEC-R4.2 — shadowctl Contract

`quant-lab/runtime/shadowctl.py` — independent control for the generic TB
shadow. It NEVER touches tbctl semantics and controls ONLY the shadow.

## Commands

| command | behavior |
|---------|----------|
| `shadowctl start [--state-dir X] [--wait]` | spawns `runtime.tb_generic_shadow`; ALREADY_RUNNING if a live pid exists; wait polls for the child's PID lock |
| `shadowctl stop` | SIGTERM the shadow pid, verifies death (STILL_ACTIVE-aware), cleans pid file |
| `shadowctl status` | read-only report: pid, alive, telemetry, heartbeat |
| `shadowctl tail [--n N]` | tail parity.jsonl |
| `shadowctl parity` | parity counters from telemetry |

## Guarantees

- Uses only shadow state paths (default `quant-lab/shadow_state/
  tb-generic-shadow-g1/`; `QL_SHADOW_STATE_DIR` env override for isolation).
- Never writes active TB DB / PID / desired-state / logs.
- `broker_write_calls` is exposed read-only; shadowctl itself performs no
  broker operation.
- `_process_alive` uses GetExitCodeProcess on Windows so a terminated-but-
  unreaped child is reported dead truthfully (stop/status never lie).

## Rollback (from R4.1)

`shadowctl stop` + delete/retain the isolated shadow state dir. No broker
cleanup needed (shadow owns no exposure).
