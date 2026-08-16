# TB-R1 — PERSISTENCE / RESTART GAP ANALYSIS

## What the prior stack persists

| Layer | Persistence | Coverage |
|---|---|---|
| `triangular_basis_executor.py` | `state/…/state.json` (+ `.tmp` atomic replace) | last_processed_timestamp, active basket ids + direction + entry_basis/z/time + **empty `leg_tickets`** |
| `triangular_basis_live.py` | none (in-memory `_active_baskets`, `_tri_bars`, `_basis_history`) | runtime only |
| `triangular_execution_layer.py` | none (in-memory `_active_baskets` with `LegExecutionRecord` incl. position/order/deal tickets) | runtime only |
| trade log | `trades/…/forward_baskets.csv` (append) | basket_id, decision, timestamp, direction, basis, z (no tickets/fills/PnL) |
| heartbeat | `state/…/heartbeat.json` | operational telemetry only |

## Critical gap

The **actual broker truth** (per-leg order/deal/position tickets, fill prices, fill volumes)
lives only in the execution layer's in-memory `LegExecutionRecord`. `state.json` records the
basket id/direction but its `leg_tickets` dict is **never populated** by the wrapper.

**Answer to the R1.8 question — can an OPEN basket be reconstructed from broker positions +
persisted records?** **NO, not fully:** after a Python/terminal/OS crash, the persisted state
has basket ids but no filled tickets, so reconciliation must re-derive ownership by scanning
`positions_get` for the magic number + `TB|{basket_id}` comment. That is *recoverable in
principle* (magic+comment tagging exists), but the event ledger that proves what was submitted
vs filled is not persisted. There is no append-only event log (JSONL/SQLite), no order-plan
persistence, and no state-transition ledger.

## Classification

**persistence_layer = REPLACE / MISSING.** R6 (append-only ledger + startup reconciliation)
is required; the execution layer's in-memory records must be emitted to the ledger at each
state transition and reloaded on startup.
