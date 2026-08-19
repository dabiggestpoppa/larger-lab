# QL-EXEC-R5 — Reconciliation Contract

## Truth surfaces

1. current open positions (`GET positions`)
2. current non-final orders (`GET orders`)
3. orders history / fills (`ordersHistory`, `executions`)
4. local pending intents (durable ledger — upstream)
5. local owned-position ledger (upstream)

## Classifications

| Class | Meaning |
|---|---|
| CLEAN | local truth == broker truth |
| LOCAL_INTENT_NO_BROKER_ORDER | intent written, provider has no order (pre-send / lost) |
| BROKER_ORDER_NO_LOCAL_TRUTH | provider order without local record |
| BROKER_POSITION_NO_LOCAL_OWNER | open position with no owned tag (foreign / unknown) |
| MISSING_OWNED_POSITION | owned position vanished without close truth |
| QUANTITY_MISMATCH | local qty != broker qty |
| FOREIGN_POSITION | tag not ours — never modified |
| AMBIGUOUS_SUBMISSION | ambiguous POST; must reconcile before ANY retry |

## Rules

- No blind retry after ambiguous submission — reconcile broker truth first.
- Foreign positions are never modified (ownership by tag is a hint, not the
  only authority; ownership truth binds strategy+runtime+account+order+position
  ids).
- `reconcile_snapshot()` returns normalized `BrokerSnapshot` from live truth.

## Tests

- `test_28` snapshot reflects position truth; flat after close.
- `test_44` restart after ambiguous POST → clean (fake never dispatched).
- `test_45` restart after accepted order → position reconstructed from truth.
- `test_48` foreign position protected through our open+close.
- `test_56` basket restart dedup (2 legs reconstructed, no duplicates).
