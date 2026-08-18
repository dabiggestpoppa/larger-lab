# QL-EXEC-R2 MT5 ORDER MAPPING

## OrderIntent -> MT5 request (build_mt5_order_request)
| Generic | MT5 request field |
|---|---|
| (action) | `action` = DEAL(1) |
| `symbol` | `symbol` |
| `volume` | `volume` (broker-native lots) |
| `side` BUY/SELL | `type` = ORDER_TYPE_BUY(0) / SELL(1) |
| `reference_price` (or ask/bid) | `price` (BUY at ask, SELL at bid) |
| `slippage_constraint`+unit | `deviation` (POINTS direct; PRICE via point) |
| `broker_magic` | `magic` |
| `ownership_tag` | `comment` (bounded to 29 chars) |
| `fill_policy` | `type_filling` (broker-observed code) |
| (close only) | `position` = position ticket |

## Market side semantics (TB parity)
- LONG/BUY market order: price = ASK.
- SHORT/SELL market order: price = BID.
- `reference_price` overrides the tick-derived price explicitly.

## order_check / submit_order
Both share `_prepare_order` (validation + request build). `submit_order` calls
`order_send`; it does NOT silently call `order_check` first (upstream enforces
the TB precheck policy).

## close_position
Finds the owned position by ID, submits the opposite market order (LONG->SELL,
SHORT->BUY) with `position` = ticket. Unknown positions are never closed.

## cancel_order
Pending-order removal via `action=REMOVE(8)`. Never cancels positions.

## No strategy sizing
No weight->notional->lots logic. Volume arrives broker-ready.
