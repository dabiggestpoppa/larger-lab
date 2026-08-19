# QL-EXEC-R5.1 Report — TradeLocker DEMO Read-Only Integration

**Status:** `WAITING_TRADELOCKER_DEMO_ACCESS`
**Base:** `832ac0f43ab8cce8f3a09057740668fc25e07ce8`
**Full offline gate:** 490/490 PASS

## Summary

R5.1 built the complete read-only integration surface for connecting the R5
`TradeLockerBrokerSession` to a real TradeLocker DEMO API, and proved the
entire normalization pipeline offline. The single blocker is operational, not
technical: **no demo credentials exist in this environment**, so no real
connection was attempted — the runner exits with
`WAITING_TRADELOCKER_DEMO_ACCESS` and makes zero network calls until
`TRADELOCKER_EMAIL` / `TRADELOCKER_PASSWORD` / `TRADELOCKER_SERVER` are
provided.

## What is proven (offline, FakeTradeLocker — zero network)

- **Four independent write barriers**, each separately tested:
  1. runtime authority gate `can_submit_new_risk = False`
  2. `ReadOnlyTradeLockerBrokerSession` raises on submit/close/cancel
  3. `ReadOnlyTransport` denies every non-GET except the two auth POSTs
  4. demo-only environment gate (non-demo host refused, substring-spoof hosts
     like `demo.tradelocker.com.evil.example` rejected)
- **Read-only audit pipeline** (the same code that will run against the real
  demo): JWT auth, account discovery (accountId and accNum retained
  separately), `/config` with deterministic version hash, instrument discovery
  with INFO/TRADE routes, quotes with provider server timestamps, positions /
  orders / history / fills normalization, `orderId != positionId` preserved,
  foreign positions never claimed, multi-account read isolation across 2
  accounts, TB basket trio availability audit.
- **Secrets hygiene**: credentials come from the environment only; source
  audits (test-enforced) prove no credential literals and no print/logging in
  the real provider modules, so auth headers cannot leak to logs.
- **MT5/TB noninterference**: additive-only diff; all R4.2 shadow tests re-run
  green in the 490-test gate.

## Offline drill evidence

- Audit result: `HEALTHY_READ_ONLY`, 2 accounts, 7 instruments, TB trio
  `ALL_3_AVAILABLE`, 1 pending order + 1 filled execution (distinct
  orderId/positionId), 1 foreign position normalized as un-owned.
- `broker_write_calls = 0`, `submit/close/cancel = 0`,
  `transport_write_attempts = 0`.

## How to reach the real-demo read-only audit

1. Set `TRADELOCKER_EMAIL`, `TRADELOCKER_PASSWORD`, `TRADELOCKER_SERVER`
   (optionally `TRADELOCKER_DEV_API_KEY`) in the environment — never in the
   repo.
2. `python runtime/tradelocker_demo_readonly.py`
3. The audit authenticates, enumerates accounts, fetches config/instruments/
   quotes/positions/orders/history/clock, writes the 14 live evidence files,
   and reports `PASS (HEALTHY_READ_ONLY)` with `broker_write_calls = 0`.

## Honest limitations

- No real demo connection was made; every "PASS_OFFLINE" matrix item is
  offline conformance, not live observation. `token_refresh_observed` against
  the real service is `NOT_NATURALLY_OBSERVED` (we do not artificially expire
  tokens against a real service).
- The execution canary (any write) belongs to R5.2 and remains unauthorized:
  `r5_2_authorized = false`, `live_execution_authorized = false`,
  `production_authorized = false`, human review required.
