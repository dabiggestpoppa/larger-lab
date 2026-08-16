# TB-R3 — Persistence / Reconciliation Protocol

**Checkpoint:** TB-R3-PERSISTENCE-RECONCILIATION
**Base commit:** `0f196feaafa59434139890d3e6106e096208cc51` (TB-R2)
**Execution authorization:** NOT_AUTHORIZED (SHADOW only)
**Scientific changes:** NONE

## 1. Problem

If the process dies after one, two, or three fills — or after a close, or
after manual broker intervention — the engine must be able to answer **exactly
what happened** without guessing. The R1 audit classified the prior stack's
persistence as **REPLACE**: it had no authoritative append-only basket ledger,
filled tickets were not durably persisted, and restart reconstruction was
insufficient (`state.json` mutable snapshot only).

## 2. Design Principles (frozen)

1. **Persist EVENTS, not mutable state.** The append-only `events` table is
   the audit source of truth. `basket_current` is a derived materialized view
   updated in the SAME transaction as the event — a fast reconstruction cache,
   never the source of truth.
2. **Write-ahead safety.** A material basket action (intent) is durably
   persisted BEFORE any broker action; broker responses are appended after.
   A crash between the two is recoverable by querying broker state.
3. **Fail closed.** Invalid state transition, missing states, schema
   mismatch, sequence gap, payload-hash mismatch, or DB corruption →
   BLOCKED_UNKNOWN_STATE. The engine refuses to process new signals.
4. **Idempotency.** Every event carries a deterministic `dedup_key` with a
   UNIQUE constraint. Re-processing the same signal / broker response / close
   event cannot double-record.
5. **Broker ownership is explicit.** A broker position is "owned" only via
   magic number AND basket-id comment linkage (or persisted execution
   linkage). Foreign magic → never altered. TB magic without linkage →
   ORPHAN, blocked, never assumed.
6. **No silent recovery.** Every reconciliation action is logged to the
   ledger (RECONCILIATION_STARTED / RECONCILIATION_COMPLETED) and surfaced.
7. **Control isolation.** CONTROL shadow events live in the same ledger as
   informational records but NEVER share executable basket state (they carry
   no basket lifecycle transition).

## 3. Storage

* **Engine:** SQLite, WAL journal mode, `synchronous=FULL`, foreign keys ON,
  `busy_timeout=10000`.
* **Schema version:** `TB_STATE_SCHEMA_VERSION = 1` (recorded in
  `schema_meta`). Future schema changes require a migration; old rows are
  never silently reinterpreted.
* **Location (live):** `quant-lab/state/triangular_basis/tb_ledger.db`
  (git-ignored runtime state).
* **Tables:**
  * `schema_meta(key, value)` — schema version + app version
  * `events(...)` — append-only ledger (see `TB_R3_EVENT_SCHEMA.json`)
  * `basket_current(...)` — materialized last-known basket state

## 4. Startup Sequence (frozen)

1. Open persistence store.
2. Integrity-check ledger (schema version, tables, sequence monotonicity,
   unique ids, payload hashes, transition validity, basket_current
   consistency). Any problem → FAIL CLOSED (no loop).
3. Reconstruct latest local basket state **solely from durable records**.
4. Query broker positions.
5. Compare expected vs broker truth (Reconciler).
6. Reconcile / classify.
7. Only then permit the SHADOW strategy loop.

## 5. Event Ledger (frozen set)

| Event | Basket transition | Notes |
|-------|-------------------|-------|
| `ENGINE_STARTED` / `ENGINE_SHUTDOWN` | — | process lifecycle |
| `SIGNAL_OBSERVED` / `SIGNAL_REJECTED` | — | per closed M5 bar; dedup by bar key |
| `BASKET_INTENT_CREATED` | SIGNAL_DETECTED → INTENT_CREATED | write-ahead BEFORE execution |
| `ENTRY_ATTEMPT_STARTED` | INTENT_CREATED → ENTRY_SUBMITTING | |
| `LEG_ORDER_SENT` / `LEG_FILL_CONFIRMED` / `LEG_FILL_FAILED` | — | per-leg info records (tickets, prices) |
| `BASKET_OPEN_VERIFIED` | ENTRY_SUBMITTING → OPEN_VERIFIED | only after 3-leg broker confirmation |
| `BROKEN_HEDGE_DETECTED` | PARTIALLY_FILLED → BROKEN_HEDGE | |
| `FLATTEN_STARTED` / `FLATTEN_LEG_CONFIRMED` | → FLATTENING | |
| `BASKET_FLAT_VERIFIED` | → FLAT_VERIFIED | |
| `EXIT_SIGNAL_OBSERVED` | OPEN_VERIFIED → CLOSE_REQUESTED | |
| `EXIT_ATTEMPT_STARTED` | CLOSE_REQUESTED → CLOSE_SUBMITTING | |
| `EXIT_FILL_CONFIRMED` | — | per-leg info record |
| `BASKET_CLOSED_VERIFIED` | CLOSE_SUBMITTING → CLOSED_VERIFIED | only after all legs flat confirmed |
| `MANUAL_POSITION_DETECTED` / `BROKER_LOCAL_MISMATCH` | → RECONCILIATION_REQUIRED | human/unknown change |
| `RECONCILIATION_STARTED` / `RECONCILIATION_COMPLETED` | — | audit trail of reconcile runs |
| `ENGINE_BLOCKED` | — | fail-closed state entry |
| `CONTROL_SIGNAL_OBSERVED` | — | control shadow stream (isolated) |

Every event records: event_id (uuid), monotonic seq, event_type, ts_utc,
basket_id, strategy_id, prior/new state, dedup_key, payload, payload_hash,
source, reason.

## 6. Reconciliation Classes (frozen)

MATCHED, BROKER_ONLY, LOCAL_ONLY, PARTIAL_MATCH, ORPHAN_POSITION,
UNKNOWN_POSITION. The full A–N case matrix with expected outcomes lives in
`TB_R3_RECONCILIATION_MATRIX.csv` and is enforced by tests.

## 7. What R3 does NOT do

* Sends real or demo orders (order_send unreachable — verified by test).
* Flattens any position automatically (R3 is not authorized to invent live
  recovery actions; divergence → BLOCK / RECONCILIATION_REQUIRED).
* Alters basis, z, entry/exit/stop thresholds, session, weights, or cost
  semantics.
* Builds demo/live execution (still NOT_AUTHORIZED).
