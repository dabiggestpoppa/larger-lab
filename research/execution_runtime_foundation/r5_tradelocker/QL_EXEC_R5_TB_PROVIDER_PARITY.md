# QL-EXEC-R5 — TB Provider Parity (offline)

## Scope

R5 proves the TB strategy/basket contract can conceptually target EITHER MT5 or
TradeLocker through peer provider adapters — OFFLINE ONLY. No TB TradeLocker
live execution is authorized. TB strategy science is untouched (TB authority
`b48fd3525` frozen).

## What was proven

- The generic TB basket surface (`TBStrategyAdapter` → `EconomicTarget` →
  `BrokerSession`) has NO provider-specific branch. The R4 basket orchestration
  submits `OrderIntent`s through the `BrokerSession` protocol; both providers
  implement that protocol.
- A 3-leg TB-style basket (sell GBPAUD, buy GBPNZD, sell AUDNZD) was executed
  against `FakeTradeLocker` with exact leg direction/quantity targets
  (`test_51`), partial-open truth (`test_52`/`test_53`), partial fill
  (`test_54`), close (`test_55`), and restart dedup (`test_56`).
- Ownership tags (`strategyId`) survive open/close/restart (`test_49`,
  `test_56`).
- Foreign positions on the same instruments are never touched (`test_48`).

## TB-specific semantics preserved through the adapter

- Model weights remain MODEL WEIGHTS (economic targets) — the adapter receives
  broker-native `qty` at the session boundary; lot translation stays in the TB
  translation adapter (not in provider code).
- Multi-leg is NOT atomic: broken-hedge recovery is runtime/basket-level, using
  provider position truth per leg.
- TB daily-loss/session gates are upstream of the provider and untouched.

## Parity classification

| Surface | MT5 | TradeLocker | Classification |
|---|---|---|---|
| BrokerSession protocol | R2 suites | R5 suites | EXACT (same contract) |
| position/order/deal normalization | R2 | R5 | NORMALIZED_EQUIVALENT (documented) |
| fill policy | FOK/IOC/RETURN via profile | IOC/GTC validity | INTENTIONAL_ARCHITECTURE_DIFFERENCE (adapter-owned) |
| qty unit | lots | provider-native qty | NORMALIZED_EQUIVALENT (translation adapter) |
| ownership | magic/comment | strategyId | NORMALIZED_EQUIVALENT |
| order id semantics | ticket | orderId != positionId | INTENTIONAL_ARCHITECTURE_DIFFERENCE (ledger handles both) |

## Not done (frozen out)

- No live/demo TradeLocker connection, no order authority.
- No Capital Routing import; no fleet/portfolio work.
