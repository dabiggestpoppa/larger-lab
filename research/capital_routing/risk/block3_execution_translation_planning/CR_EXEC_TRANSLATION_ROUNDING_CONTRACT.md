# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Rounding Contract

## Frozen policy: ROUND TOWARD LOWER ABSOLUTE EXPOSURE
Broker quantity rounding must never increase exposure beyond the allowed
admitted_f.  Never round upward to reach the research fraction.

For every order compute:
    target_one_R_budget  = equity x admitted_f_pct/100
    actual_one_R_budget  = rounded_notional x (RISK_UNIT_BPS/10000)
    realized_f_pct       = actual_one_R_budget / equity x 100
    rounding_error_pct   = (target - actual) / target x 100   (>= 0 by policy)

## Tolerance / failure
- Tolerance band (pre-registration, NOT optimized here): e.g. realized_f_pct
  within [0.75x, 1.00x] of admitted_f_pct; values below 0.75x are recorded as
  UNDER-SIZED (never silently promoted to full f).
- If broker minimum quantity forces actual exposure ABOVE the admitted_f
  tolerance: REJECT with MIN_QUANTITY_RISK_OVERSHOOT.  Do not force minimum
  size.

## Under-sizing truth
The portfolio ledger must know ACTUAL exposure:
    target_admitted_f vs actual_admitted_f_equivalent.
Acceptable tracking-error bands are designed for future preregistration here,
NOT optimized.

## Post-rounding heat truth (see model-vs-actual heat contract)
Research admission (MODEL_HEAT) occurs in frozen f-units; the execution layer
must additionally satisfy REALIZED_TRANSLATED_HEAT = sum of actual
one_R_budget / equity over active events.  Both must be <= the H1 allowance.
Broker rounding must never bypass H1.
