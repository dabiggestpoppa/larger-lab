# TB-R3 — Idempotency Contract

**Purpose:** A restart must NOT open a duplicate basket, double-record a fill,
close twice, or flatten an unrelated position. The same signal / basket
intent / execution response / fill / close event / reconciliation event must
not be processed twice.

## Mechanism

Every event carries a deterministic `dedup_key`. The `events.dedup_key`
column has a UNIQUE constraint. `append_event` checks the key first: if it
already exists, the existing event is returned and nothing new is written.

| dedup key | event(s) |
|-----------|----------|
| `INTENT|<basket_id>` | BASKET_INTENT_CREATED |
| `ENTRY|<basket_id>` | ENTRY_ATTEMPT_STARTED |
| `FILL|<basket_id>|<symbol>` | LEG_FILL_CONFIRMED |
| `OPEN|<basket_id>` | BASKET_OPEN_VERIFIED |
| `EXIT|<basket_id>` | EXIT_SIGNAL_OBSERVED |
| `EXITAT|<basket_id>` | EXIT_ATTEMPT_STARTED |
| `EXITF|<basket_id>|<symbol>` | EXIT_FILL_CONFIRMED |
| `CLOSED|<basket_id>` | BASKET_CLOSED_VERIFIED |
| `SIG|<bar_key>` | SIGNAL_OBSERVED (one per closed M5 bar) |
| `SIGREJ|<bar_key>` | SIGNAL_REJECTED |
| `CTRL|<n>` | CONTROL_SIGNAL_OBSERVED |

The same strategy dedup is also enforced at the feed level
(`SynchronizedTriangleFeed.last_processed_signal_ts`) and the engine level
(`TriangularBasisLiveEngine._last_processed_timestamp`) — three independent
layers, all idempotent.

## Guarantees (verified by tests)

1. Re-appending the same basket intent → no-op (event count unchanged).
2. Same leg-fill response twice → one record (no double counting).
3. Running reconciliation twice (restart) → same classifications, only the
   two reconcile events added, no duplicate baskets.
4. Same signal bar looped → one strategy evaluation (feed + engine dedup).
5. `BasketLedger` exposes no update/delete API — append-only by construction.
6. Payload hashes make silent corruption detectable at startup.

## Non-goals (frozen)

* This contract does NOT authorize executing anything. order_send remains
  unreachable.
* Idempotency is about event/state truth, not about broker-side order
  dedup (that is the execution layer's domain when execution is authorized).

**Scientific changes: NONE.**
