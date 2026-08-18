# QL-EXEC-R2.1 — ERROR RESULT CONTRACT

## Truthful success state
`BrokerErrorCategory.NONE` is the success sentinel. The frozen invariant:

- `result.ok == True`  => `error_category is NONE` (never an error).
- `result.ok == False` => a meaningful non-success category where determinable,
  else `UNKNOWN_BROKER_ERROR` **only** when genuinely unresolved.

## Result types (all backward-compatible field additions)
| Type | error_category |
|---|---|
| `OrderResult` | added in R2 (default fixed from `UNKNOWN_BROKER_ERROR` to `NONE`) |
| `CheckResult` | added (default `NONE`) |
| `CancelResult` | added (default `NONE`) |
| `CloseResult` | added (default `NONE`) |

## Categories used
`NONE`, `NOT_CONNECTED`, `INVALID_REQUEST`, `SYMBOL_UNAVAILABLE`,
`UNSUPPORTED_CAPABILITY`, `ORDER_CHECK_FAILED`, `ORDER_REJECTED`,
`TRANSPORT_ERROR`, `UNKNOWN_BROKER_ERROR` (reserved for genuinely unresolved).

## Cancel / Close / Check review
- `CancelResult` and `CloseResult` now carry `error_category`: `NONE` on
  success, `ORDER_REJECTED`/`TRANSPORT_ERROR`/`NOT_CONNECTED`/`INVALID_REQUEST`
  on failure. Backward-compatible and useful for R3 normalization.
- `CheckResult` cannot be `ok=True` with a failure reason or error: a
  successful check returns `reason == ""` and `error_category is NONE`.
