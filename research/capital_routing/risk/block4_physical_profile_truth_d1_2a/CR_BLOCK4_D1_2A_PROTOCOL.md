# CR-BLOCK4-D1.2A PROTOCOL — Physical Profile Truth Ingest and Seal

**Checkpoint:** CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL
**Base:** `aaf3e0548ec9bff85b38b7f8a853a7becffce4c3` (D1.2 plan)
**Status:** TRUTH INGESTION + PROVENANCE + SEALING (no D1.2B surface, no D1.3 margin)

## 1. Question

> What physical USDJPY account/product contracts do we actually know, how do
> we know them, and which are sufficiently complete to permit empirical
> quantity translation?

## 2. Core principle

Assumptions are never turned into broker facts.  Every field carries value +
truth_class + source + observed_at + provenance.  Precedence: ACTUAL_OBSERVED
> BROKER_DOCUMENTED > PROFILE_FROZEN > USER_SPECIFIED_SCENARIO >
HYPOTHETICAL_DIAGNOSTIC > UNKNOWN.

## 3. Evidence collected (read-only, git fetch)

- execution-runtime-foundation `62e6d0402a780d171a8b81c2070567045e341be7` (QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN):
  SymbolInfo contract SHAPE exists (quant-lab/execution_runtime/types.py) but
  is populated only at runtime from a live MT5 session; NO committed
  USDJPY/account observation snapshots exist.
- FakeMT5 / SimBroker fixtures hardcode generic FX values (100000 / 0.01 /
  0.01 / 100) — TEST FIXTURES, NOT truth.
- capital-routing has USDJPY MT5 price-data session evidence only.
- tb-forward-engine `b48fd35255b41865026a3cba333ae2a2a0d6a004`: TB-specific lot/execution artifacts —
  NOT CR USDJPY account truth.
- User-specified scenarios: equity + leverage only; instrument fields NOT
  supplied.

## 4. Conclusion

NO actual/documented USDJPY quantity truth exists in the repository.  No
profile is QUANTITY_MINIMUM_COMPLETE.  Status:
PARTIAL_PASS_WAITING_PHYSICAL_TRUTH.  No PASS is manufactured; D1.2B stays
BLOCKED until quantity truth is collected and sealed.

## 5. Non-goals

No quantity surface (D1.2B), no margin study (D1.3), no broker client, no
MetaTrader5 import, no order API, no performance-based selection, no science
change.
