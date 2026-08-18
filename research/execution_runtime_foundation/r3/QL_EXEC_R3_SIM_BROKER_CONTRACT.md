# QL-EXEC-R3 — SimBrokerSession Contract

Transport-neutral, in-memory `BrokerSession` (`brokers/sim_broker.py`). No
network, no MetaTrader5. Proves the GenericRuntime is not MT5-dependent.

## Surface

`connect, disconnect, health, identity, account_state, clock_state,
symbol_info, ensure_symbol, tick, bars, positions, orders, deals, order_check,
submit_order, close_position, cancel_order, reconcile_snapshot`.

## Order model

An accepted market order deterministically creates:
- a broker order record,
- a deal record,
- a position record (full fill by default).

## Injected failure modes

- `FULL_FILL` (default)
- `PARTIAL_FILL` (position at `partial_ratio` of requested)
- `ZERO_FILL` (accepted order, NO position)
- `ORDER_REJECT` (retcode 10030, ORDER_REJECTED)
- `TRANSPORT_ERROR` (order_send transport error)

Plus: `set_connect_ok`, `set_order_check_ok`, `seed_foreign_position`.

## Persistence across restart

The broker's in-memory truth survives runtime object recreation when the same
instance is reused (it is the injected persistent fixture). Crash windows are
injected at the ENGINE boundary (`CrashPoint`), not inside the broker.
