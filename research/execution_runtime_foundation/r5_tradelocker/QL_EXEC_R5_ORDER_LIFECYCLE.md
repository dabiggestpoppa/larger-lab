# QL-EXEC-R5 — Order Lifecycle

## Intent → TradeLocker request mapping (adapter-owned)

| Generic | TradeLocker |
|---|---|
| `OrderIntent.symbol` | resolved to `tradableInstrumentId` |
| `OrderIntent.side` BUY/SELL | `side` buy/sell |
| `OrderIntent.volume` (broker-native qty) | `qty` (string, rounded to profile precision) |
| `OrderType.MARKET` | `type=market`, `validity=IOC` (mandatory) |
| `OrderType.LIMIT` | `type=limit`, `validity=GTC` (mandatory) |
| `OrderType.STOP` | `type=stop`, `validity=GTC`, `stopPrice=price_constraint` |
| `reference_price` | `price` (ignored by provider for market) |
| `ownership_tag` | `strategyId` (max 32; fail closed if exceeded) |

Validity mapping lives in the adapter — the strategy never knows IOC/GTC.

## Lifecycle states

```
LOCAL_PREFLIGHT (zero network)
   -> POST /orders (write-ahead gate: exactly ONE write call per submit)
   -> ACCEPTED (orderId known; NOT a fill)
   -> market: Filled + position appears (IOC)
   -> limit/stop: pending order; fill only when the provider executes it
   -> fill truth confirmed via positions/executions reconciliation
```

## Rules

- `order_check` is LOCAL structural preflight only (TradeLocker has no
  broker-side preflight). Capability `supports_order_check=UNSUPPORTED`,
  documented.
- Unsupported combination fails closed (e.g. FOK fill policy on a market order,
  non-GTC on a resting order, unknown instrument, missing TRADE route, qty<=0,
  over-long strategyId).
- Rate limiter gates `PLACE_ORDER`; ambiguous sends are never retried.

## Tests

`test_22` market/IOC, `test_23` limit/GTC, `test_24` stop/GTC+stopPrice,
`test_25` invalid TIF blocked, `test_42` validation before any network write.
