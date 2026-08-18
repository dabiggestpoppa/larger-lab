# CR-BLOCK4-D1.2 FIDELITY METRICS

Frozen BEFORE any empirical outcome.

## Definitions

- `raw_quantity` — unrounded broker quantity from the pipeline
- `rounded_quantity` — faithful (floor-to-step) quantity
- `quantity_delta = rounded_quantity - raw_quantity`
- `target_notional` — sealed EconomicTarget notional (account currency)
- `represented_notional = rounded_quantity x price_semantics`
- `exposure_ratio = represented_notional / target_notional`
- `relative_exposure_error = |represented_notional - target_notional| / target_notional`
- `signed_exposure_error = (represented_notional - target_notional) / target_notional`

## Materiality tolerance (preregistered)

| band | condition | primary state |
|---|---|---|
| exact | exposure_ratio == 1 (float tolerance) | EXACTLY_REPRESENTABLE |
| immaterial | relative_exposure_error <= 1% | REPRESENTABLE_WITH_IMMATERIAL_ROUNDING |
| distorted | relative_exposure_error > 5% | ROUNDING_DISTORTED |

Rationale for the 1% candidate: it matches the D1
frozen immaterial band (IMMATERIAL_RELATIVE_ERROR = 1%
preregistered in D1), keeping one consistent materiality language across
lanes.  Expressed in risk-unit terms, 1% of target notional corresponds to 1%
of that event's one-R exposure — economically interpretable and independent
of PF/EV.  The tolerance is re-confirmed at D1.2A when the physical profile is
sealed; it is never chosen from performance.

## Result surfaces (future D1.2B)

Per profile / account size: n accepted targets, exactly representable,
immaterial rounding, rounding distorted, min blocked, max blocked, unresolved,
coverage %, mean / median / p95 / max relative error.
