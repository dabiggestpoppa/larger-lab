# QL-EXEC-R2.1 — MT5 FILL-POLICY + RESULT-TRUTH REPAIR PROTOCOL

## Checkpoint
`QL-EXEC-R2.1-MT5-FILL-POLICY-AND-RESULT-TRUTH-REPAIR`

## Authoritative base
`4f318a8f6716d5db3406c2ace8785944c4f8a50c` (`QL-EXEC-R2-MT5-BROKER-SESSION-EXTRACTION`)

## Mission
Repair three narrow MT5 transport-truth defects before R3 consumes
`MT5BrokerSession`:

1. **D1 — broker-specific fill codes used as universal default.** The Ox/TB
   permuted `type_filling` mapping (FOK=1 / IOC=2 / RETURN=0) was the default
   for every future MT5 broker.
2. **D2 — unknown fill fallback too permissive.** `BROKER_DEFAULT` / `UNKNOWN`
   silently fell back to RETURN when no policy could be proven.
3. **D3 — success carried an error.** `OrderResult.ok == True` was shipped with
   `BrokerErrorCategory.UNKNOWN_BROKER_ERROR`.

## Scope boundaries (unchanged)
- No TB strategy science changes.
- No Capital Routing changes.
- No R3, no generic worker, no TB migration.
- No real MT5 connection, no real orders, no TradeLocker.
- Account, ownership, clock, and broker-timestamp semantics untouched.
- Strategy sizing untouched.

## Repair shape
- Introduce immutable, instance-scoped `MT5ExecutionProfile`
  (`fill_policy_codes`, `fill_policy_bits`, `max_comment_length`).
- Generic default = provider-neutral standard MT5 constants derived from the
  **injected module**; missing constants => FAIL CLOSED (empty mapping).
- Ox/TB-observed behavior preserved as an explicit fixture:
  `ox_observed_execution_profile()` (in `fake_mt5.py`).
- `BROKER_DEFAULT` / `UNKNOWN` resolve by evidence only:
  probe → declared capability → BLOCK. No unconditional RETURN fallback.
- Add `BrokerErrorCategory.NONE` and thread a truthful `error_category` through
  `OrderResult`, `CheckResult`, `CancelResult`, and `CloseResult`.

## Verification
- Full suite: **226 passed, 0 failed** (R1+R1.1 = 111, R2 = 90, R2.1 = 25).
- All order paths use `FakeMT5` only. No real MetaTrader5, no real orders.
