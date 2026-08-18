# QL-EXEC-R2 MT5 SYMBOL MAPPING

| MT5 symbol_info field | Generic SymbolInfo field |
|---|---|
| (argument) | `symbol` |
| `digits` | `digits` |
| `point` | `point` |
| `trade_contract_size` | `contract_size` |
| `volume_min` | `volume_min` |
| `volume_step` | `volume_step` |
| `volume_max` | `volume_max` |
| `visible` | `visible` |
| `trade_mode` | `trade_mode` (normalized) |
| `trade_tick_size` | `trade_tick_size` |
| `trade_tick_value` | `trade_tick_value` |
| `filling_mode` bits | `declared_fill_policies` (tuple[FillPolicy]) |

## Symbol activation
`ensure_symbol(symbol)` -> `symbol_select(symbol, True)`. Fail closed if
activation cannot be proven. No silent quote/order calls on unavailable symbols.

## Fill capability — DECLARED vs ACTUAL
`declared_fill_policies` is the broker's declared bitfield truth. It is NOT a
guarantee of accepted behavior; `probe_fill_policies()` discovers the actual
mode via order_check. Bit mapping (TB-observed): 1 -> FOK, 2 -> IOC, 4 -> RETURN.

## Missing values
Missing fields are normalized to 0/empty/UNKNOWN; nothing is fabricated.
