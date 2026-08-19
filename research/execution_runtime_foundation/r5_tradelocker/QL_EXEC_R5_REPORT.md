# QL-EXEC-R5 — Report

**CHECKPOINT:** QL-EXEC-R5-TRADELOCKER-PROVIDER-FOUNDATION-AND-DUAL-PROVIDER-CONFORMANCE
**STATUS:** PASS (offline/mock/demo-read foundation)
**BASE:** 26b9b80d0b336f3c422fe187ece9075b68ffdf1b
**DATE:** 2026-08-18

## What was built

A first-class TradeLocker provider package (`execution_runtime.tradelocker`)
behind the SAME `BrokerSession` protocol as MT5:

- **Auth:** JWT token/refresh with singleflight, injected secrets (no
  plaintext), server-401 forced refresh.
- **Client:** REST over an injectable transport (stdlib urllib; fake in
  tests), dynamic column resolution via `/config`, provider-aware rate limits,
  401 refresh-retry, and NO blind retry on write methods.
- **Session:** `TradeLockerBrokerSession` implements every `BrokerSession`
  method with provider truth preserved (accountId vs accNum, INFO/TRADE routes,
  market=IOC / resting=GTC, orderId != positionId, close-as-order,
  strategyId ownership tags) plus a truthful `capabilities()` surface.
- **FakeTradeLocker:** deterministic in-memory provider with full state machine
  and failure injection (auth fail, token expiry, 429+Retry-After, 5xx, 403,
  malformed JSON, rejections, partial fills, deferred close, before-send /
  ambiguous timeouts) — zero network in tests.

## Evidence

- **459 / 459 tests pass** (380 R4.2 baseline + 79 new R5 tests; 59-test matrix
  + 20 conformance runs).
- MT5 regression suite unchanged and green; R4.2 TB shadow untouched and green.
- Conformance: identical `BrokerSession` behaviors against Sim + TradeLocker;
  the MT5 leg of the same contract is the (passing) R2/R2.1 suites.
- Provider-neutrality: no MT5 import/reference anywhere in the tradelocker
  package; GenericRuntime has no provider branch.

## Truthful caveats

- **No demo/live connection** was made and **no order was attempted** — R5 is
  offline/mock only. The 459 green tests prove contract conformance against
  fake provider truth, not the real demo API.
- `capital-routing` moved again during fetch (`43a6473c`); zero effect — no CR
  science is imported.
- `supports_modify_order`, `supports_trailing_stop`, hedging/netting mode are
  honestly UNKNOWN (fail closed) until verified against the real API in R5.1.
- Fill entry/exit normalization is `NORMALIZED_EQUIVALENT` (derived from
  positions truth), documented in the fill-truth contract.

## Gates

- live_execution_authorized: **false**
- production_authorized: **false**
- human_review_required: **true**

## Next

`QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION` (authorized only after
human review), then `QL-EXEC-R5.2-TRADELOCKER-DEMO-EXECUTION-CANARY`. Do NOT
jump directly to live.
