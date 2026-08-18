# CR-BLOCK4-D1 FAITHFULNESS METRICS

Frozen BEFORE any empirical result.

## Definitions

- `exposure_ratio = actual_representable_notional / target_economic_notional`
- `relative_exposure_error = (actual_representable_notional - target_economic_notional) / target_economic_notional`

Primary ideal: `exposure_ratio = 1`.

## Materiality tolerances (preregistered)

| band | condition | primary state |
|---|---|---|
| exact | exposure_ratio == 1 (within float tolerance) | EXACTLY_REPRESENTABLE |
| immaterial | |relative_exposure_error| <= 1% | REPRESENTABLE_WITH_IMMATERIAL_ROUNDING |
| distorted | |relative_exposure_error| > 5% | ROUNDING_DISTORTED |

Tolerances are frozen. They are not adjusted after seeing outputs.

## Coverage metrics (per physical scenario)

- faithful representable count / %
- blocked count / %
- distorted count / %
- mean / median / p5 exposure ratio
- worst underrepresentation (min exposure ratio)
- maximum overrepresentation (max exposure ratio)

## Distortion metrics (preregistered)

- family coverage (A vs B) and surviving share vs original share
- pos distribution of surviving vs original (median / p75 / p95 / p99 / max)
- feasibility by notional-quantile bin (see notional diagnostic grid)
- feasibility by frozen time/regime groupings (split / year / quarter / session / severity)
