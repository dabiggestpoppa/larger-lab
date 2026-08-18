# QL-EXEC-R3 — Runtime Store Contract

- One SQLite DB per runtime_id at `state/<runtime_id>/runtime.sqlite`.
- `PRAGMA journal_mode=WAL`, `synchronous=FULL`, `foreign_keys=ON`,
  `busy_timeout=10000`.
- Schema version `RUNTIME_SCHEMA_VERSION = 1` recorded in `runtime_meta`
  alongside `runtime_id`, `deployment_generation`, `profile_hash`,
  `account_hash`.
- Tables: `runtime_meta`, `desired_state`, `runtime_events`, `strategy_events`,
  `capital_decisions`, `economic_targets`, `execution_intents`,
  `broker_orders`, `positions_owned`, `reconciliation_runs`, `heartbeats`.
- No automatic migration in R3. Schema/generation/profile mismatch blocks.

## Fail-closed startup checks (`startup_check`)

1. schema version mismatch -> `SCHEMA_VERSION_MISMATCH` (FAILED).
2. runtime_id mismatch -> `RUNTIME_ID_MISMATCH` (FAILED).
3. deployment generation mismatch -> `GENERATION_DRIFT` (BLOCKED).
4. profile hash mismatch under same generation -> `BLOCK_CONFIG_DRIFT` (BLOCKED).
5. account hash mismatch under same generation -> `BLOCK_CONFIG_DRIFT` (BLOCKED).
