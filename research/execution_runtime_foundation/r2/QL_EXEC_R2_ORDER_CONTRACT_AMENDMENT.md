# QL-EXEC-R2 ORDER CONTRACT AMENDMENT

R1.1 flagged `R2_ORDER_CONTRACT_AMENDMENT_REQUIRED = true`: critical execution
fields were hidden in opaque `metadata`. R2 makes them broker-neutral and
explicit.

## OrderIntent (amended)
| Field | Type | Meaning |
|---|---|---|
| `side` | `OrderSide` | BUY / SELL (was opaque str) |
| `volume` | `float` | broker-native quantity at BrokerSession boundary |
| `quantity_unit` | `QuantityUnit` | LOT / UNKNOWN (no silent notional) |
| `order_type` | `OrderType` | MARKET / LIMIT |
| `reference_price` | `float | None` | preflight/expected price (not guaranteed fill) |
| `price_constraint` | `float | None` | limit price (LIMIT orders) |
| `fill_policy` | `FillPolicy` | FOK / IOC / RETURN / BROKER_DEFAULT / UNKNOWN |
| `slippage_constraint` | `float | None` | explicit slippage/deviation magnitude |
| `slippage_unit` | `SlippageUnit` | PRICE / POINTS / UNKNOWN (no naked 20) |
| `broker_magic` | `int` | broker-scoped numeric tag (not global) |
| `ownership_tag` | `str` | comment / ownership metadata |

## FillPolicy (broker-neutral)
FILL_OR_KILL / IMMEDIATE_OR_CANCEL / RETURN_OR_PARTIAL / BROKER_DEFAULT /
UNKNOWN. MT5 enum integers (`ORDER_FILLING_FOK` etc.) never appear in the
generic contract; the adapter maps them.

## No MT5 enum leak
Generic modules (`types.py`, `enums.py`, `interfaces.py`) contain none of
ORDER_TYPE_BUY / TRADE_ACTION_DEAL / ORDER_FILLING_FOK / POSITION_TYPE_BUY.
Verified by test.

## Quantity unit
`OrderIntent.volume` == broker-native lots for MT5. EconomicTarget -> lots
conversion is NOT part of MT5BrokerSession.

## Slippage
TB's `deviation=20` (20 MT5 points) is representable as
`slippage_constraint=20, slippage_unit=POINTS` but 20 is NOT a universal
default: no constraint => deviation 0.

## Related value-object extensions
- `Tick.valid` (invalid quote truth)
- `Bar.volume` (real_volume -> tick_volume fallback)
- `BrokerIdentity.trade_allowed / terminal_trade_allowed / tradeapi_disabled`
- `Position/Order/Deal` magic/comment/time/id-relationship fields
- `OrderResult` (normalized submission result)
