# QL_EXEC_R1_CAPITAL_ROUTING_BOUNDARY_AUDIT

## Authorities

| Type | SHA | Status |
|---|---|---|
| Scale / heat science | `40d237123ac2b709cc0ebce1d7f057bbfde25dab` | SEALED (frozen) |
| Capital translation science | `00bef1b5b52db63c22a29b3287799742631930db` | PENDING_SEALED_REPAIR |

## What moved

origin/capital-routing advanced past the sealed scale commit:

- `5a79bf23` — CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING
- `00bef1b5` — CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR

The repair derives `N_t = Equity_t x admitted_f_decimal x pos_t x 1e4 / RISK_UNIT_BPS` and marks execution net parity `BROKER_DEPENDENT_UNRESOLVED`. Its own decision is `PASS, implementation_ready=true, implementation_authorized=false`.

## Boundary (explicitly frozen by Capital Routing)

- Capital Routing owns only capital translation.
- Generic execution belongs to `execution-runtime-foundation` (this workstream).
- Portfolio Master requires A+B on ONE shared H1 ledger.
- TB Forward is the read-only engineering reference.

## R1 enforcement

- Generic package contains NO hardcoded `A=0.70` / `B=0.30` / `1R=24.494897...` / pos formula / `USDJPY` / `H1-1.00` (test-enforced).
- `CapitalPolicyAdapter` has no `translate_heat_to_notional`.
- `CapitalTranslationAdapter` is a separate interface, unimplemented in R1.
