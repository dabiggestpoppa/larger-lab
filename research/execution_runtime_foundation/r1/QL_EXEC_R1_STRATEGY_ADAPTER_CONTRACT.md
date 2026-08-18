# QL_EXEC_R1_STRATEGY_ADAPTER_CONTRACT

Implemented as `execution_runtime.interfaces.StrategyAdapter` (a `typing.Protocol`). Value objects only; no implementation migrated from TB.

## Interface

```
strategy_id: str
required_market_data() -> tuple[str, ...]
initialize(runtime_ctx: dict) -> None
warm(historical: object) -> None
on_market_snapshot(snapshot: object) -> None
produce_events() -> tuple[StrategyEvent, ...]
serialize_state() -> str
restore_state(state: str) -> None
health() -> dict
```

## Shape independence

- `required_market_data()` returns one symbol (single-leg) or N (basket).
- `produce_events()` returns `StrategyEvent`s (opaque to the generic runtime).
- Execution translation is separate; the adapter does NOT produce broker orders.

## Purity

- No MT5/TradeLocker types (enforced by test).
- No capital math (no A/B, no f, no notional).
- TB's triangular engine is a future conforming implementation; R1 does not migrate it.
