# QL-EXEC-R2 MT5 BROKER SESSION CONTRACT

`MT5BrokerSession(mt5_module=None, *, fill_policy_codes=None, fill_policy_bits=None, max_comment_length=29, clock_probe_symbol="")`

- **Dependency injection**: the real MetaTrader5 module is passed in (lazily).
  Tests inject FakeMT5. No hard-wired `import MetaTrader5`.
- **External session**: `connect()` calls `initialize()` then requires
  `terminal_info() is not None`. No runtime credentials.
- **disconnect()**: idempotent `shutdown()`; never closes positions.

## Method -> semantics
| Method | Semantics |
|---|---|
| connect | attach to externally authenticated session |
| disconnect | idempotent shutdown |
| health | connected / clock_calibrated / last error category |
| identity | BrokerIdentity (company/server/login/env/currency/trade flags) |
| account_state | AccountState (balance/equity/margin/free margin; buying_power stays None) |
| clock_state | BrokerClockState from 12h-gated calibration |
| symbol_info | SymbolInfo (contract + declared fill policies) |
| ensure_symbol | symbol_select(symbol, True) |
| probe_fill_policies | order_check-based actual fill discovery |
| tick | Tick (bid/ask/last/source time/valid) |
| bars | Bar list (dict + numpy structured; raw bar-open time) |
| positions/orders/deals | normalized broker truth |
| order_check | CheckResult (retcode normalized) |
| submit_order | OrderResult (retcode normalized) |
| cancel_order | pending order removal |
| close_position | opposite market order referencing position ticket |
| reconcile_snapshot | BrokerSnapshot (broker truth only) |

## Error normalization
Raw AttributeError/NoneType/MetaTrader5 exceptions never escape. Failures map
to `BrokerErrorCategory` (see error catalog).

## Non-goals
No strategy notional, no Capital Routing math, no basket atomicity, no retry
loop, no automatic order_check-before-send (upstream policy).
