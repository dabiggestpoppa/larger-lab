# QL-EXEC-R3 — Reconciliation Contract

`Reconciler` compares durable local truth (`positions_owned` + `intents`)
against broker truth (`BrokerSnapshot.positions`). It never sends orders and
never closes positions.

## States

`FLAT_MATCH, OPEN_MATCH, CLOSED_MATCH, LOCAL_INTENT_BROKER_MISSING,
BROKER_OWNED_LOCAL_MISSING, DUPLICATE_OWNED_EXPOSURE, FOREIGN_ONLY, AMBIGUOUS,
ERROR`.

Clean (new-risk allowed): `FLAT_MATCH, OPEN_MATCH, CLOSED_MATCH, FOREIGN_ONLY`.

## Recovery actions

- `RETRY` — pending intent, broker flat (crash before submit / zero fill):
  safe idempotent resubmit.
- `RECONSTRUCT` — broker has our-tagged position but local has no open record
  (crash after submit): record it without resubmitting; or mark a
  `CLOSE_PENDING` position closed when the broker is flat.
- `CLOSE_RETRY` — `CLOSE_PENDING` position still present at broker: retry close.
- `BLOCK` — divergence cannot be resolved automatically (AMBIGUOUS,
  DUPLICATE, ERROR).

## Precedence

BROKER = truth for physical exposure. LOCAL JOURNAL = truth for intended
logical ownership/history. Reconciliation combines them and never deletes
contradictory evidence.

R3 is single-position: at most one owned exposure is assumed, so duplicates are
flagged, not averaged.
