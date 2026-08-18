# QL_EXEC_R0_BROKER_SESSION_CONTRACT

A minimal cross-provider semantic interface for broker access. Built from validated TB runtime use cases, not from a maximal MT5 API surface.

---

## 1. Conceptual interface

```python
class BrokerSession:
    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...
    def health(self) -> dict: ...
    def identity(self) -> BrokerIdentity: ...

    def account_state(self) -> AccountState: ...        # equity/balance/margin/currency/mode
    def buying_power(self) -> float | None: ...
    def margin_state(self) -> dict: ...

    def symbol_info(self, symbol) -> SymbolInfo | None: ...
    def select_symbol(self, symbol) -> bool: ...
    def tick(self, symbol) -> Tick | None: ...
    def bars(self, symbol, timeframe, count) -> list[Bar] | None: ...

    def positions(self) -> list[Position]: ...
    def orders(self) -> list[Order]: ...
    def deals(self, start, end) -> list[Deal]: ...

    def order_check(self, intent: OrderIntent) -> CheckResult: ...
    def submit_order(self, intent: OrderIntent) -> SubmitResult: ...
    def cancel_order(self, order_id) -> CancelResult: ...
    def close_position(self, position_id, reason) -> CloseResult: ...

    def reconcile_snapshot(self) -> BrokerSnapshot: ...
```

All method results are normalized value objects; no MT5 numpy records leak across the interface.

---

## 2. Mapping to TB's validated use cases

| TB call today | BrokerSession method |
|---|---|
| `mt5.initialize` / `terminal_info` | `connect` / `health` |
| identity gate (account_info/terminal_info) | `identity` + account profile matching |
| `account_info().equity` | `account_state` |
| `symbol_info` | `symbol_info` |
| `symbol_select` | `select_symbol` |
| `copy_rates_from_pos` | `bars` |
| `symbol_info_tick` | `tick` |
| `positions_get` | `positions` |
| `orders_get` | `orders` |
| `history_deals_get` | `deals` |
| `order_check` | `order_check` |
| `order_send` (order/close) | `submit_order` / `close_position` |

---

## 3. Reference implementations

- `MT5BrokerSession` — wraps the current MT5 terminal/account/session behavior (R2).
- `SimBrokerSession` — deterministic fake broker for full-engine harness parity (TB already has `FakeBroker` in `full_engine.py`).
- `ReplayBrokerSession` — replays captured broker snapshots for reconstruction/reconciliation tests.
- `TradeLockerBrokerSession` — FUTURE/UNKNOWN. Not built in R0; no capability is invented.

---

## 4. Fail-closed rules

- Identity gate must pass before any order authority; mismatch → EXECUTION BLOCKED.
- Foreign/unknown positions are never modified; if they make resources ambiguous → BLOCK NEW RISK.
- Broker fills/positions are truth for exposure; the local ledger is truth for ownership intent; both must reconcile.
- `order_check` is preflight only; a check that cannot resolve the executable fill mode fails closed (as TB's `probe_filling_modes` already does).
