# QL-EXEC-R2.1 — REPORT

## Result: PASS

Repaired three narrow MT5 transport-truth defects on top of
`4f318a8f` (R2), without touching strategy science, Capital Routing, clock,
ownership, or account architecture.

## Changes

### Code
- `enums.py`: added `BrokerErrorCategory.NONE` (truthful success state).
- `types.py`: added `error_category` to `CheckResult`, `CancelResult`,
  `CloseResult`; fixed `OrderResult.error_category` default to `NONE`.
- `brokers/mt5.py`:
  - Added immutable `MT5ExecutionProfile` and `standard_fill_policy_codes` /
    `standard_fill_policy_bits` (module-derived, fail-closed when missing).
  - Generic fill default is now standard MT5, never Ox.
  - `_resolve_fill_code` fail-closed (probe → declared → BLOCK, no RETURN).
  - `_prepare_order` returns an error category and gates on symbol availability.
  - `submit_order`/`order_check`/`cancel_order`/`close_position` set truthful
    error categories.
  - Generic comment default = no truncation; 29-char bound is a profile value.
- `brokers/fake_mt5.py`: added `SYMBOL_FILLING_*` constants and
  `ox_observed_execution_profile()`.

### Tests
- New `test_execution_runtime_mt5_fill_result_r2_1.py` (25 tests).
- Updated four R2 tests that had encoded the Ox quirk as the universal default.

## Verification
- `pytest quant-lab/execution_runtime/tests`: **226 passed, 0 failed**.
- FakeMT5 only. No real MetaTrader5, no real orders, no real connection.

## Gates
- Broker-specific fill mappings are no longer universal defaults. ✓
- Provider-neutral standard MT5 mapping works. ✓
- Explicit broker overrides work independently. ✓
- Unknown fill capability fails closed. ✓
- No unconditional RETURN fallback remains. ✓
- Successful order results cannot carry error state. ✓
- TB/Ox observed behavior remains representable (via profile). ✓
- Two simultaneous MT5 brokers can use different mappings. ✓
- All R2 functionality remains intact. ✓
- No real broker activity. ✓
- All tests pass. ✓

## Next
Recommend `QL-EXEC-R3-GENERIC-SINGLE-INSTANCE-RUNTIME` (NOT auto-authorized).
