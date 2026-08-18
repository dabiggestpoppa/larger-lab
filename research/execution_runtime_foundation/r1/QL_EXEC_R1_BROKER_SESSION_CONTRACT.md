# QL_EXEC_R1_BROKER_SESSION_CONTRACT

Implemented as `execution_runtime.interfaces.BrokerSession` (Protocol) + `execution_runtime.types` value objects. No `MetaTrader5` import; no actual adapter.

## Interface

```
connect() -> bool
disconnect() -> None
health() -> dict
identity() -> BrokerIdentity
account_state() -> AccountState
symbol_info(symbol) -> SymbolInfo | None
tick(symbol) -> Tick | None
bars(symbol, timeframe, count) -> list[Bar] | None
positions() -> list[Position]
orders() -> list[Order]
deals(start, end) -> list[Deal]
order_check(intent: OrderIntent) -> CheckResult
submit_order(intent: OrderIntent) -> SubmitResult
cancel_order(order_id) -> CancelResult
close_position(position_id, reason) -> CloseResult
reconcile_snapshot() -> BrokerSnapshot
```

## Purity

- All results are normalized value objects; no numpy records leak.
- Fail-closed: identity gate before order authority; foreign positions never modified; broker truth vs ledger truth both reconciled.

## Capabilities

`BrokerCapabilities` is tri-state (`SUPPORTED` / `UNSUPPORTED` / `UNKNOWN`). Unknown required capability fails closed. R2 implements `MT5BrokerSession` behind this contract.
