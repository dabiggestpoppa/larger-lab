# QL_EXEC_R4_TB_RUNTIME_CONTRACT

R4 compares TB runtime-relevant semantics against the generic runtime's
equivalents. The TB worker's own desired-state file and PID lock are classified
as TB aux/supervisor artifacts, not absorbed into GenericRuntime.

| surface | TB reference | Generic runtime | tier |
|---|---|---|---|
| desired state | `tb_desired_state` file (RUNNING / STOPPED_BY_USER) | DB-backed `desired_state` table (same two values) | EXACT (semantics) |
| identity gate | server/company/trade_mode/currency must match | R1 `identity_gate` | EXACT |
| reconciliation gate | broker positions vs ledger before trades | R3 `Reconciler` | EXACT |
| singleton | PID file | R3 `SingletonLock` | EXACT |
| market-closed recovery | non-latching (R6.1B) | fresh reconcile recompute | EXACT |
| profile/generation drift | n/a (worker generation) | `startup_check` BLOCK | EXACT (generic-only safety) |
| heartbeat | durable heartbeat + PnL telemetry | R3 heartbeat + telemetry | EXACT (semantics) |
| PnL ownership | owned-only (magic + TB\| tag) | owned-only (logical ownership) | EXACT |

## PnL

R4 does not re-research alpha performance. Owned realized/unrealized vs foreign
PnL separation is preserved; no PF/WR/EV acceptance gate is used.
