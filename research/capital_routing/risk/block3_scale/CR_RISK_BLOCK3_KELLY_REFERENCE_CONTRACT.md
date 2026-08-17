# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Kelly reference contract (frozen)

## Status
Kelly is a DIAGNOSTIC REFERENCE ONLY in Block III. It is NOT a risk
architecture, cannot override family allocation or the H1 heat limit, is
never executed, never selected, never authorized
(kelly_calculated = true, kelly_selected = false, kelly_authorized = false,
production_kelly_authorized = false).

## Method (pre-registered)
Empirical expected-log-growth on the event return distribution (returns are
continuous — NO simplistic binary win-rate / fixed-R formula):

    g(f) = mean over events of log(1 + f * w_i * r_i)
    f*  = argmax g(f) over a feasible grid (1 + f*w*r > 0 for all events)

where w_i = family weight of event i. Grid: 0.001..0.30 step 0.001 in
decimal f (percent 0.1%..30%).

## Reported fractions
full Kelly f*, plus 1/2, 1/4, 1/8.

## Uncertainty
Bootstrap the estimated f* (iid resample of event indices; deterministic
seed). Report median / p10 / p25 / p75 / p90. Classify:
- UNSTABLE_REFERENCE when the bootstrap spread is wide (IQR > 3pp) or the
  argmax sits at a grid boundary — never force a number.
- STABLE_REFERENCE otherwise.

## Scopes
pooled (allocation-weighted), A-only, B-only — each at 100% / 75% / 50% /
25% retained edge. A Kelly recommendation that collapses under modest edge
degradation is treated as fragile evidence.

## Numerical documentation
objective: mean expected log-growth; bounds: feasible domain (positive
inside terms); sample: sealed 890-event A/B book; assumptions: event-level
compounding, allocation fixed; method: vectorized grid argmax + bootstrap.
