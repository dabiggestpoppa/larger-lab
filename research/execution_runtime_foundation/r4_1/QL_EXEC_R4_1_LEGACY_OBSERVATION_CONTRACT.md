# QL-EXEC-R4.1 — Legacy Observation Contract

## Purpose

Least-invasive read-only observation of legacy TB decisions, so the shadow can
compare live decisions against generic decisions.

## Preferred sources (READ ONLY)

1. `quant-lab/state/tb_runtime.db` — `RuntimeDB` tables:
   - `runtime_status` (desired_state, NAV baselines)
   - `runtime_heartbeat` (last_closed_bar, last_signal_time, open_basket_id,
     today_pnl, open_pnl, account_equity, market_open, last_error)
   - `runtime_errors`
2. Existing logs: `quant-lab/logs/tb_runtime.log`, `tb_supervisor.log`
3. Existing telemetry / watcher output (JSON) if present.

The dashboard already reads `tb_runtime.db` only (no MT5, no log scraping);
the shadow uses the same read-only DB source.

## If a richer decision export is required

The continuous market-data + decision export (Option B) supplies the precise
per-bar decision surface (basis, z, direction, weights, lots, basket state,
blocker). It is an **additive read-only side-channel** planned here; if the
existing DB/log surface is insufficient, a minimal read-only exporter is
implemented ONLY under R4.2 review. R4.1 does NOT implement it.

## Prohibitions

- No modification of active TB engine to emit parity data.
- No write to `tb_runtime.db` / `tb_control.db` / logs / desired-state.
- No reading of active TB with the intent to mutate or lock it.

## Normalization

Non-semantic fields (row IDs, log timestamps, PID) are normalized away.
Semantic fields (bar key, basis, z, decision, direction, weights, lots, basket
state, blocker) are compared per PARITY_SCHEMA.
