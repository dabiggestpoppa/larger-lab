# QL-EXEC-R4.1 — MT5 Concurrent Read Audit Plan

## Status

`mt5_concurrent_read_truth_resolved = false`

Until this audit is performed and its result recorded, G1 will NOT attach a
second Python process to the same MT5 terminal/session. The preferred
market-data path (Option B) does not require concurrent MT5 access.

## Question to resolve

Can two local Python processes safely read from the same MT5 terminal /
external session simultaneously, without:

- session ownership collision
- `initialize()` / `shutdown()` interference
- terminal binding conflict
- provider state mutation

## Audit steps (before any Option A path is ever considered)

1. Confirm how the active TB worker initializes the session (external-session
   auth vs explicit `mt5.initialize()` + `mt5.login(login, password, server)`).
   Note: multiple legacy scripts in `quant-lab/mt5/` use `mt5.initialize()`;
   the exact mechanism the *active* worker uses must be confirmed from the
   frozen worker source, not inferred.
2. Determine whether `mt5.initialize()` from a second process establishes an
   independent IPC client to the running terminal (documented behaviour) and
   whether `mt5.shutdown()` in one process affects the other process's client.
3. Verify `copy_rates_*` / `symbol_info` / `account_info` / `positions_get`
   calls are read-only with respect to broker state.
4. Verify no `order_check` / `order_send` is ever reachable from the shadow
   path (G1 excludes `order_check`).
5. Produce a written verdict:
   - `SAFE_CONCURRENT_READ` (then Option A becomes eligible), or
   - `UNSAFE_OR_UNKNOWN` (Option B / C remain the only paths).

## Explicit non-assumptions

- Concurrent access is NOT assumed safe.
- `shutdown()` in one process is NOT assumed harmless to another process.
- No terminal-binding / login-state assumptions are made.

## Default decision

Option B (`LEGACY_EXPORT_READ_ONLY_SNAPSHOT`) is the G1 default precisely
because it does not require resolving this question. The audit is scheduled,
not blocking the G1 shadow canary, because G1 does not exercise concurrent
MT5 access.
