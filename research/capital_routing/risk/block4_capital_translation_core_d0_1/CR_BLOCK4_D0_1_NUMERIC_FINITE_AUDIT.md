# CR-BLOCK4-D0.1 -- Numeric Finiteness Audit

## Why explicit isfinite
Guard patterns such as `if not pos_t or pos_t <= 0` do NOT reliably fail
closed on NaN:
    bool(float("nan")) == True      # passes the truthiness guard
    float("nan") <= 0               # False — NaN comparisons are False

## Fields (all must be math.isfinite)
| field | required | failure |
|---|---|---|
| pos_t | finite, > 0 | InvalidNumericInputError / InvalidPositionError |
| risk_unit_bps | finite, > 0, == frozen R | InvalidNumericInputError / RiskUnitMismatchError |
| requested_f_pct | finite, >= 0, == family contract | InvalidNumericInputError / CapitalDecisionConsistencyError |
| admitted_f_pct | finite, >= 0, status-consistent | InvalidNumericInputError / CapitalDecisionConsistencyError |
| model_heat_before | finite, >= -1e-09 | InvalidNumericInputError / CapitalDecisionConsistencyError |
| model_heat_after | finite, >= -1e-09, ACCEPT <= cap | InvalidNumericInputError / CapitalDecisionConsistencyError |
| equity_at_admission | finite, > 0 | InvalidNumericInputError / MissingAccountEquityError |

## Verified
All NaN / +inf / -inf injections on every field above fail closed with
InvalidNumericInputError through the repaired core (see adversarial audit).
The sealed ledger is clean: no NaN/inf in pos, heat, or f fields; 66 rows
carry model_heat_before fp noise down to -2.2e-16, handled by the documented
HEAT_EPS bound.
