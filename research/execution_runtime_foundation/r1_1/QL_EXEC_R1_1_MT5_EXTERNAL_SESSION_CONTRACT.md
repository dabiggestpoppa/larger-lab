# QL-EXEC-R1.1 MT5 EXTERNAL SESSION CONTRACT

## Purpose
Model the proven TB MT5 pattern without connecting to a real account.

## Contract
An MT5 profile MAY use `AuthenticationMode.EXTERNAL_SESSION`. In that mode:

1. `SecretReference` is optional (may be `None`).
2. `requires_secret(profile)` returns `False`.
3. `authentication_satisfied(profile, observed)` returns satisfied only when
   `observed.authenticated` is true.
4. `derive_execution_authority` still applies the full identity gate:
   - broker company (case-insensitive match)
   - server
   - account identifier (when frozen)
   - environment
   - currency (when frozen)
   - account mode (when frozen)
   - terminal/session binding (when frozen)
5. A missing SecretReference must NOT, by itself, deny authority.
6. An identity mismatch MUST still deny.

## Why this is correct
The runtime attaches to a terminal/session already authenticated outside the
runtime. Credential possession is therefore not a runtime responsibility. The
runtime's duty is identity verification, not authentication.

## What this does NOT permit
- It does not make `CONNECTED` sufficient.
- It does not make `AUTHENTICATED` sufficient.
- It does not grant `FOLLOWER` / `MIRROR` order authority.
- It does not weaken the reconciliation / safety-block / intentional-stop
  gates.

## R2 note
R2's `MT5BrokerSession` must populate `AccountObservedState` (including
`authenticated` and identity fields) from the validated TB DemoEnvironment /
terminal truth path, and must reproduce the TB identity gate semantics.
