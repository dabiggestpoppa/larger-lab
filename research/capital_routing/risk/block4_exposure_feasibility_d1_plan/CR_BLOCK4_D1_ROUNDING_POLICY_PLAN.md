# CR-BLOCK4-D1 ROUNDING POLICY PLAN

## Frozen defaults

- primary: **ROUND_DOWN_TOWARD_ZERO** — round toward lower absolute exposure; never
  exceed the approved scientific target
- comparator: NEAREST_STEP (diagnostic only)
- upward rounding default: **False**
- min-quantity default: **MIN_QUANTITY_BLOCKED** — do not round up to minimum
- max-quantity default: **MAX_QUANTITY_BLOCKED** — do not silently clip

## Materiality

- |relative error| <= 1% -> REPRESENTABLE_WITH_IMMATERIAL_ROUNDING
- |relative error| > 5% -> ROUNDING_DISTORTED

## Rules

1. Rounding never silently inflates exposure beyond the admitted economic target.
2. A minimum-lot overshoot lane, if studied later, is ALTERED_BOOK_DIAGNOSTIC and
   requires preregistration before results.
3. Rounding policy is not optimized against performance.
4. Post-rounding translated heat must never exceed the model H1 allowance
   (MODEL_HEAT vs REALIZED_TRANSLATED_HEAT contract from planning R1).
