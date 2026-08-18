# QL-EXEC-R3 — Generic Single-Instance Runtime Protocol

Checkpoint: `QL-EXEC-R3-GENERIC-SINGLE-INSTANCE-RUNTIME`
Base: `52e39b13f37812221cab7c283afc302623a61bc6`

## Purpose

Build the FIRST generic, persistent, single-instance execution runtime over the
R0-R2.1 contracts. R3 proves the lifecycle, not any trading strategy.

## Non-negotiable boundaries

- NO TB migration, NO real MT5 canary, NO multi-account, NO FleetSupervisor.
- Simulation/fake/replay broker truth only (`SimBrokerSession`).
- `StrategyAdapter` / `CapitalPolicyAdapter` / `CapitalTranslationAdapter` /
  `BrokerSession` are ALL injected. No hidden globals, no strategy imports, no
  Capital Routing math, no MetaTrader5.

## Lifecycle proven

START -> load durable state -> validate identity -> connect broker -> verify
account truth -> reconstruct local state -> reconcile broker truth -> warm
strategy -> observe deterministic events -> admit capital -> translate ->
write-ahead intent -> execute (Sim broker) -> verify broker truth -> persist ->
survive restart -> dedup -> heartbeat/telemetry -> intentional stop.

## Test basis

- `python -m pytest quant-lab/execution_runtime/tests/ -q` => 309 passed.
- 226 prior (R1/R1.1/R2/R2.1) + 83 new R3 tests, all Fake/Sim/Replay only.
- Crash windows injected via `CrashPoint` + `SimulatedCrash` (no real process
  death).

## Result

R3 PASS. R4 (TB full nonregression migration harness) is recommended but NOT
auto-authorized.
