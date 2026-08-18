# QL-EXEC-R1.1 DEFECT AUDIT

## Defect 1 — AUTHENTICATION != SECRET POSSESSION

**R1 behavior (defective):**
`transport_requires_secret(MT5) = true`. Any MT5 profile was forced to hold a
`SecretReference` merely because its transport was MT5.

**Why wrong:**
The proven TB MT5 runtime attaches to an existing, externally authenticated
terminal session and then validates broker company / server / account /
environment / currency / terminal truth. It does not require the Python
runtime to possess a password.

**Repair:**
- Added `AuthenticationMode` enum: `NONE`, `EXTERNAL_SESSION`,
  `RUNTIME_CREDENTIALS`.
- `AccountProfile.authentication_mode` is now an explicit, required field.
- `requires_secret(profile)` depends on the authentication mode, not the
  transport.
- `authentication_satisfied(profile, observed)` is a single centralized pure
  function feeding `derive_execution_authority()`.

## Defect 2 — SYMBOL ACTIVATION CONTRACT

**R1 behavior (incomplete):**
`BrokerSession` exposed `symbol_info/tick/bars` but had no broker-neutral way
to express the explicit symbol activation that validated MT5 operation needs
(`symbol_select`).

**Repair:**
- Added `BrokerSession.ensure_symbol(symbol) -> bool` (generic, never named
  `mt5_symbol_select`).
- Added `BrokerCapabilities.supports_symbol_activation` (tri-state).

## Defect 3 — BROKER CLOCK / SOURCE-TIME CONTRACT

**R1 behavior (incomplete):**
No way to represent the distinction between broker source time, local
observation time, and a calibrated reference. MT5 source timestamps and local
UTC must never be casually mixed.

**Repair:**
- Added `BrokerClockState` (source clock name, calibrated offset, status,
  age, failure reason).
- Added `BrokerSession.clock_state()`.
- Extended `Tick` and `Bar` with `observed_at_utc`, `source_clock_name`, and
  `offset_seconds` while preserving `time` as the raw source timestamp.

## Order contract
Reviewed read-only. No blocking omission found that requires a redesign in
R1.1. See `QL_EXEC_R1_1_ORDER_CONTRACT_REVIEW.md`.

## Capital Translation contract
Not modified. The R1.1 Capital Routing handoff seal exposes a richer
`CapitalDecisionReference`; recorded as a future R6 extension, not an R1.1
blocker. See `QL_EXEC_R1_1_CAPITAL_ROUTING_DRIFT_AUDIT.md`.
