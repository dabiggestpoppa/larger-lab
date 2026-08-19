# QL-EXEC-R5 — Order ID != Position ID

## Provider truth

TradeLocker `orderId` and `positionId` are DIFFERENT identities. An opening
market order returns `d.orderId`; the position id appears only later in
positions/ordersHistory (row field `positionId`). They must not be modeled like
a single MT5 ticket.

## Ledger identity fields

| Field | Meaning |
|---|---|
| `logical_execution_id` | runtime/ledger identity (idempotency authority) |
| `provider_order_id` | TradeLocker order id (submit response / orders rows) |
| `provider_position_id` | TradeLocker position id (positions truth) |
| `provider_fill_id` | execution/deal identity (executions rows) |

## Rules

- Opening order ACCEPTANCE never proves a position exists.
- A position is only assumed when positions truth contains it.
- Reconciliation must be able to represent: accepted-but-no-position,
  position-without-local-truth, quantity mismatch, etc.

## Tests

- `test_27` submit orderId != positionId.
- `test_26` accepted limit order → zero positions.
- `test_18` position truth after market fill.
