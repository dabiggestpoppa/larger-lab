# QL_EXEC_R4_TB_SUPERVISION_CLASSIFICATION

R6.1D full-stack supervision is classified, not absorbed. Proven engineering is
kept; only what belongs in the generic runtime core is mapped there.

| TB component | classification | rationale |
|---|---|---|
| tb_worker lifecycle | GENERIC_RUNTIME_CORE | single-instance lifecycle -> GenericRuntime / future RuntimeRunner |
| tb_supervisor | GENERIC_PROCESS_SUPERVISOR_FUTURE | full-stack process supervision -> R5+ FleetSupervisor |
| tb_basket_watcher | TB_AUX_SERVICE | auxiliary basket watcher; NOT strategy parity |
| tb_dashboard | TB_AUX_SERVICE | read-only dashboard; NOT strategy parity |
| tb_probe_market | TB_AUX_SERVICE | monitoring probe |
| tb_telegram | TB_AUX_SERVICE | alerting |

## R6.1D behaviors (preserved as classification, not ported)

- adopt already-live watcher/dashboard, no duplicate
- bounded restart backoff, reset failure counter after stable runtime
- stop all children on STOPPED_BY_USER / supervisor shutdown
- dashboard singleton, watcher singleton

These belong to the future process supervisor (R5+), NOT the generic runtime
core. `watcher_absorbed_into_runtime_core = false`,
`dashboard_absorbed_into_runtime_core = false`.
