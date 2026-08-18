# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Model vs Actual Heat Contract

## Two states
- MODEL_HEAT: the sealed research admission in frozen f-units (requested_f,
  admitted_f from the R6 causal engine under H1-1.00-REJ @ A1_70_30).  On the
  sealed book this admits 371 A + 455 B
  events and rejects 64 by H1.
- REALIZED_TRANSLATED_HEAT: sum over ACTIVE events of
  (actual_one_R_budget / equity_at_admission) -- i.e. the realized f after
  broker quantity rounding.

## Invariant
The execution engine must satisfy BOTH at every moment:
    MODEL_HEAT <= 1.00 f-unit
    REALIZED_TRANSLATED_HEAT <= 1.00 f-unit (per the H1 allowance)
If model admission says 1.00 but rounding produces > allowed translated heat:
reduce or block -- broker rounding must never bypass H1.

## Active-heat continuity
Open events keep their admission-snapshot f (no dynamic resizing).  Heat is
released only when the position is actually confirmed closed (see
reservation state machine) -- broker truth, not research intent.
