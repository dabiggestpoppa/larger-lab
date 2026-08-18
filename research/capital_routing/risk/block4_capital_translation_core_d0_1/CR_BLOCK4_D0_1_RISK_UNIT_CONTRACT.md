# CR-BLOCK4-D0.1 -- Risk-Unit Contract

## Canonical formula (D0.1)
    target_notional = equity x (admitted_f_pct/100) x pos_t x 10000 / risk_unit_bps

The arithmetic uses the EXPLICIT `risk_unit_bps` argument. It never silently
substitutes a module constant. (BOTH statements hold:)

- **A. mathematical correctness** — `target_notional(E, f, pos, R)` computes
  exactly E x f x pos x 1e4 / R for ANY positive finite R (verified: R2 = 2R1
  scales the notional inversely by exactly 2).
- **B. science-contract correctness** — `translate()` rejects any event whose
  risk_unit_bps does not match the frozen strategy-science contract.

## Frozen strategy-science contract (science R1.1)
    risk_unit_bps == 24.49489742783178   (tolerance 1e-09)

Derivation: 1R = TARGET_VOL x sqrt(6h hold) = 10 bps/h x sqrt(6) bps.
1R is a NORMALIZED EXPECTED-MOVE UNIT — NOT a hard stop / max loss / broker
stop. Historical events include losses materially below -1R (Family A worst
-3.66R, Family B worst -3.31R).

## Reclassified constant
`ONE_R_NOTIONAL_FACTOR = 1e4 / RISK_UNIT_BPS = 408.248290` is a
FROZEN DIAGNOSTIC / REFERENCE constant only. It is NOT used in production
arithmetic and can never override an explicit function input.

## Failure semantics
- NaN / +/-inf risk_unit_bps  -> InvalidNumericInputError (not finite)
- risk_unit_bps <= 0           -> InvalidNumericInputError
- risk_unit_bps != frozen R    -> RiskUnitMismatchError
- unsupported science version  -> RiskUnitMismatchError (this core implements
  exactly the sealed R1.1 contract)
