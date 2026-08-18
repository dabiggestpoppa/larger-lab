# QL_EXEC_R1_ACCOUNT_ROUTER_CONTRACT

Implemented as `execution_runtime.routing.AccountRouter`. Pure account-selection validation; no broker connection.

## Interface

```
route(strategy_id, bindings, portfolios, accounts) -> RoutingResult
```

`RoutingResult` carries `decision` (`ROUTED` / `REJECTED`), the resolved `account_ids`, and blocking `reasons`.

## Rules

- zero bindings for the strategy -> REJECT
- binding disabled -> REJECT
- multiple enabled bindings without deterministic policy -> REJECT (ambiguous)
- EXCLUSIVE master -> exactly one account; allowlist enforced
- PORTFOLIO master -> strategy must belong to the approved, enabled `PortfolioGroup`; allowlist enforced
- FOLLOWER / MIRROR -> REJECT (cannot route direct execution)

## Layer separation

ACCOUNT ROUTING (where does the event run) is separate from CAPITAL ROUTING (how much heat) and BROKER EXECUTION (how to submit). The router only answers the "where" question.
