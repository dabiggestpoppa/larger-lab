# QL-EXEC-R4.1 — Read-Only Broker Contract

## Class

`ReadOnlyBrokerSession` (G1 shadow), implementing the `BrokerSession`
interface with the write surface removed.

## Allowed (read-only)

- `identity()` — broker/account identity (observed)
- `account_state()` — equity/currency/leverage/margin (observed)
- `clock_state()` — `BrokerClockState`
- `symbol_info(symbol)` — contract size, digits, lot min/step/max
- `ticks(...)` / `bars(...)` — market data (via exported snapshot feed in G1)
- `positions()` / `orders()` / `deals()` — read-only truth
- `reconcile_snapshot()` — broker truth for reconciler

## Forbidden (write surface)

- `submit_order(...)` — NOT PRESENT (raises `AttributeError`/absent method)
- `close_position(...)` — NOT PRESENT
- `cancel_order(...)` — NOT PRESENT
- `order_check(...)` — **excluded from G1** (not needed; and, until proven
  side-effect-free on the provider, treated as non-read-only)
- any lower-level `order_send`, pending-order mutation, or position-close

## Enforcement

1. The class literally does not define the write methods — a type-checker and
   runtime attribute access both fail, not merely return an error.
2. A defensive `__getattr__` raises `ShadowBrokerWriteDenied` for any
   attribute name in a denylist (`submit_order`, `close_position`,
   `cancel_order`, `order_check`, `send`, `order_send`) so that a future
   refactor cannot silently reintroduce a write path.

## Accounting identity

Persist:

- `account_observed = true`
- `order_authority = false`

Observing an account never grants execution authority. The two are stored as
independent facts.
