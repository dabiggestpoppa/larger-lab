# QL-EXEC-R1.1 REPORT
MT5 AUTH / SESSION / CLOCK CONTRACT REPAIR

## Status: PASS

## Base
`9e11db928ad3c330fcde06d075e20a6e5b349d89`

## Summary
Three defects repaired in the generic `execution_runtime` package, all pure
and fail-closed. No broker implementation, no MT5 import, no connection, no
orders, no active-deployment change.

1. **Authentication != secret possession** — `AuthenticationMode` added;
   `requires_secret(profile)` replaces `transport_requires_secret(transport)`.
   MT5 `EXTERNAL_SESSION` no longer requires runtime credentials. Identity
   gate remains fail-closed.
2. **Symbol activation** — `BrokerSession.ensure_symbol` + tri-state
   `supports_symbol_activation` capability.
3. **Broker clock / source time** — `BrokerClockState` +
   `BrokerSession.clock_state()`; `Tick`/`Bar` now distinguish raw source
   timestamp, observation time, and calibration context. No UTC+3 hardcoding;
   source timestamps never silently normalized.

## Authority
- TB engineering: `d12005988ce61170d9bc5478089baa5ce54cc2a9`
- Capital Routing branch head: `d51b9b4772f0bf2ee9a87deb830614e7494f25d1`
- Capital Routing scientific translation seal: `2bbe52ea8798549ed9c03bd90684fd3a0d408a99`
  (status PENDING_SEALED_REPAIR)
- main: `9f61288679eea56a298e08f718c314f2ca509bc5`

## Tests
111/111 pass (75 preserved R1 + 36 new R1.1).

## Boundary results
- generic_code_imports_metatrader5: false
- broker_connection_attempted: false
- broker_order_attempted: false
- tb_active_runtime_modified: false
- capital_translation_contract_changed: false
- order_contract_r2_extension_required: true (bounded: price/fill/slippage)

## R2 readiness
R2 may consume the latest frozen TB engineering authority and wrap current
MT5 behavior behind `BrokerSession`. R2 must NOT automatically migrate the
active TB runtime.

## Next
`QL-EXEC-R2-MT5-BROKER-SESSION-EXTRACTION` (human authorization required).
