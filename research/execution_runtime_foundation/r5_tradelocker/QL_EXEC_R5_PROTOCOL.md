# QL-EXEC-R5 — TradeLocker Provider Foundation + Dual-Provider Conformance

**Checkpoint:** `QL-EXEC-R5-TRADELOCKER-PROVIDER-FOUNDATION-AND-DUAL-PROVIDER-CONFORMANCE`
**Base:** `26b9b80d0b336f3c422fe187ece9075b68ffdf1b` (R4.2)
**Status:** PASS (offline/mock/demo-read foundation only)
**Date:** 2026-08-18

## Mission

Correct the provider imbalance: the generic Execution Runtime must support MT5
and TradeLocker as first-class peer provider adapters. TradeLocker is NOT
implemented as an MT5-shaped wrapper; GenericRuntime core stays
provider-neutral. R4.2 TB shadow continues independently — R5 is parallel
provider work.

## Hard boundaries (honored)

- No live orders. No demo connection. No production authorization.
- No modification of active TB, MT5 Task Scheduler, R4.2 shadow, or current
  canary evidence rules.
- TradeLocker live execution: `false` everywhere.
- Capital Routing science: NOT imported (capital-routing moved during fetch —
  irrelevant to R5).

## Architecture

```
GenericRuntime
    |
    +-- BrokerSession protocol
            |
            +-- MT5BrokerSession        (R2 frozen; unchanged)
            |
            +-- TradeLockerBrokerSession (R5 new; provider-native truth)
```

Everything above BrokerSession stays provider-independent. The TradeLocker
adapter owns provider quirks: INFO/TRADE route ids, market=IOC / limit+stop=GTC
validity, `accountId` vs `accNum`, orderId != positionId, close-as-order,
strategyId tag ownership.

## Provider truth frozen (2026-08-18)

Official sources: `https://public-api.tradelocker.com/` reference + the
official Python client (`TradeLocker/tradelocker-python`,
`src/tradelocker/tradelocker_api.py`). See `QL_EXEC_R5_TRADECLLOCKER_API_TRUTH.md`.

## Evidence

- Full suite: **459 / 459 pass** (380 R4.2 baseline + 79 new R5 tests).
- 59-test matrix (items 1-60) + 20 conformance runs (10 behaviors x 2
  providers). MT5 leg of the same contract = R2/R2.1 suites (unchanged, pass).
- Zero network in tests; `FakeTradeLocker` implements the transport protocol.
- Provider-neutrality scan: no MT5 import/reference in the tradelocker package.

## Gates

- `generic_runtime_provider_neutral`: true
- `mt5_provider_supported`: true
- `tradelocker_provider_supported`: true
- `real_tradelocker_demo_connected`: false
- `real_tradelocker_order_attempted`: false
- `live_execution_authorized`: false — `production_authorized`: false

## Next (not authorized)

`QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION` — then
`QL-EXEC-R5.2-TRADELOCKER-DEMO-EXECUTION-CANARY` after human review. Do NOT jump
directly to live.
