# QL-EXEC-R5 — Fill Truth Contract

## Principle

A successful `POST /orders` response (`s:ok`, `d.orderId`) means the order was
**accepted**, NOT filled. Fill truth comes only from broker truth:

- `positions` — open exposure (qty, side, positionId, strategyId)
- `orders` / `ordersHistory` — order status (Pending/Filled/Rejected)
- `executions` — fills in the current session

## Normalization (adapter)

- `positions()` → normalized `Position` (provider position id, symbol via
  instrument binding, abs(qty), LONG/SHORT from buy/sell, strategyId → tag).
- `orders()` → non-final orders only (`GET /orders`).
- `deals()` → executions normalized to `Deal`; entry vs exit determined by
  comparing each fill's `positionId`/side against current positions truth
  (documented as NORMALIZED_EQUIVALENT — TradeLocker has no native
  entry/exit flag).

## Close truth

- `close_position` places a CLOSING ORDER (IOC then GTC per the official
  client). `ok` means the closing order was accepted, NOT that the position is
  gone.
- Flatness must be confirmed from `positions()` truth; reconciliation continues
  while owned exposure remains.
- Partial close (`qty>0`) must reconcile the actual remaining quantity.

## Tests

- `test_26` accepted order != filled position (resting limit).
- `test_29` close request != closed truth (deferred close fixture).
- `test_30` partial close reconciliation (1.0 → close 0.4 → remaining 0.6).
- `test_28` position reconciliation after close.
- `test_21` fill-history normalization.
