# QL-EXEC-R3 — TB Pattern Extraction Audit

READ-ONLY reference: `quant-lab/tb_live/` (state_machine.py, persistence.py,
reconciliation.py) and `research/tb_forward/r6_1/`. TB science is NEVER copied;
only proven engineering patterns are extracted into generic equivalents.

| Pattern | TB source | Proven behavior | Generic R3 equivalent | Parity | Strategy parts excluded |
|---|---|---|---|---|---|
| Desired state | r6_1 INTENTIONAL_STOP_AUDIT / tb_runtime.db | STOPPED_BY_USER persists across restart; supervisor does not restart worker | `desired_state` table + `stop()` + startup gate | GENERIC_EQUIVALENT | tbctl/Windows task lifecycle |
| Runtime DB | tb_live/persistence.py | SQLite+WAL append-only events + materialized current state | `RuntimeStore` (SQLite+WAL) | GENERIC_EQUIVALENT | basket/leg payload semantics |
| Write-ahead intent | tb_live/persistence.py | event persisted BEFORE broker action | `create_intent` before `submit_order` | GENERIC_EQUIVALENT | basket/leg intent fields |
| Ownership | tb_live/reconciliation.py | magic + comment token + persisted linkage only | `LogicalOwnershipId` + `ownership_tag` ledger | GENERIC_EQUIVALENT | TB magic 31082026 / basket token format |
| Reconciliation | tb_live/reconciliation.py | classify vs broker; divergence -> BLOCK, never silent | `Reconciler` + `ReconciliationState` | GENERIC_EQUIVALENT | 3-leg triangle specifics |
| Restart | tb_live/reconciliation.py + persistence | reconstruct solely from durable records | `start()` reconstruction + recovery actions | GENERIC_EQUIVALENT | basket reconstruction fields |
| Heartbeat | r6_1 HEARTBEAT_AUDIT | durable liveness + blocker visibility | `Heartbeat` + `heartbeats` table | GENERIC_EQUIVALENT | operator-facing frequency |
| Market recovery | r6_1 MARKET_CLOSURE_AUDIT | fresh observation replaces stale closed status | `step()` re-reconciles each tick, no latch | GENERIC_EQUIVALENT | TB session/time rules |
| Foreign-position protection | tb_live/reconciliation.py | UNKNOWN_POSITION never altered | foreign positions reported, never touched | GENERIC_EQUIVALENT | TB basket token parsing |
| Singleton | r6_1 SINGLETON_AUDIT | PID-file lock, stale-pid reclaim, no OS primitives | `SingletonLock` (file lock + stale-pid reclaim) | GENERIC_EQUIVALENT | supervisor/worker split |
| Fleet supervisor | tb_forward r6_1 | supervisor/worker separation | NOT BUILT | DEFERRED_TO_R4/R5 | n/a |

## Statuses

- `EXACT_PATTERN` — none (TB patterns are basket/leg-specific by nature).
- `GENERIC_EQUIVALENT` — all above.
- `DEFERRED_TO_R4/R5` — supervisor/process supervision, dashboard control.
- `NOT_GENERIC` — TB strategy science (basis/z/entry/exit/weight), session/cost
  semantics, 3-leg basket mechanics.

R3 does NOT claim TB parity; that is R4.
