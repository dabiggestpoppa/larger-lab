# CR-BLOCK4-D1.2A EXECUTION RUNTIME HANDOFF AUDIT

## Inspected (read-only): execution-runtime-foundation `62e6d0402a780d171a8b81c2070567045e341be7`

| finding | detail |
|---|---|
| SymbolInfo contract | EXISTS — quant-lab/execution_runtime/types.py: symbol, digits, point, contract_size, volume_min/max/step, trade_mode, trade_tick_size/value, declared_fill_policies |
| InstrumentPhysicalSpec | ABSENT under that exact name (D1.2 plan contract; not yet in foundation) |
| AccountPhysicalProfile | ABSENT under that exact name |
| committed symbol/account observation snapshots | ABSENT — SymbolInfo values are runtime-only from a live MT5 session |
| FakeMT5 | EXISTS as test fixture — NOT truth |
| SimBroker | EXISTS — hardcodes generic FX contract — NOT truth |

## Boundary

- Capital Routing consumes future normalized InstrumentPhysicalSpec /
  AccountPhysicalProfile artifacts from Execution Runtime; it does NOT import
  the broker session implementation.
- The live MT5 BrokerSession in the foundation is the future ACTUAL_OBSERVED
  source once a real bound account exists.
- `execution_runtime_head` recorded: `62e6d0402a780d171a8b81c2070567045e341be7`.
